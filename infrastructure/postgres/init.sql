-- Cerberus PostgreSQL Initialization Script

-- Create schemas
CREATE SCHEMA IF NOT EXISTS cerberus;

-- Events table
CREATE TABLE IF NOT EXISTS cerberus.events (
    event_id VARCHAR(64) PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    source VARCHAR(32) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    session_id VARCHAR(128),
    client_ip INET,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_events_timestamp ON cerberus.events(timestamp DESC);
CREATE INDEX idx_events_session ON cerberus.events(session_id);
CREATE INDEX idx_events_type ON cerberus.events(event_type);
CREATE INDEX idx_events_data_gin ON cerberus.events USING GIN(data);

-- WAF Rules table
CREATE TABLE IF NOT EXISTS cerberus.waf_rules (
    rule_id VARCHAR(64) PRIMARY KEY,
    created_by VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    priority INTEGER NOT NULL DEFAULT 100,
    match_config JSONB NOT NULL,
    action VARCHAR(32) NOT NULL,
    confidence FLOAT NOT NULL,
    evidence JSONB,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    valid_from TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ,
    audit JSONB
);

CREATE INDEX idx_rules_priority ON cerberus.waf_rules(priority DESC);
CREATE INDEX idx_rules_enabled ON cerberus.waf_rules(enabled);

-- Attacker Profiles table
CREATE TABLE IF NOT EXISTS cerberus.attacker_profiles (
    session_id VARCHAR(128) PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    action_sequence TEXT[],
    ttps TEXT[],
    intent VARCHAR(64),
    sophistication_score FLOAT,
    cluster_id INTEGER,
    profile_data JSONB NOT NULL
);

CREATE INDEX idx_profiles_intent ON cerberus.attacker_profiles(intent);
CREATE INDEX idx_profiles_ttps_gin ON cerberus.attacker_profiles USING GIN(ttps);

-- Simulations table
CREATE TABLE IF NOT EXISTS cerberus.simulations (
    simulation_id VARCHAR(64) PRIMARY KEY,
    payload_id VARCHAR(64),
    session_id VARCHAR(128),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(32) NOT NULL,
    verdict VARCHAR(32),
    severity FLOAT,
    execution_time_ms INTEGER,
    result JSONB
);

CREATE INDEX idx_simulations_status ON cerberus.simulations(status);
CREATE INDEX idx_simulations_verdict ON cerberus.simulations(verdict);

-- Captures table (evidence from Labyrinth)
CREATE TABLE IF NOT EXISTS cerberus.captures (
    capture_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(128),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    client_ip INET,
    request_method VARCHAR(16),
    request_url TEXT,
    payloads JSONB,
    evidence_url TEXT,
    capture_data JSONB NOT NULL
);

CREATE INDEX idx_captures_timestamp ON cerberus.captures(timestamp DESC);
CREATE INDEX idx_captures_session ON cerberus.captures(session_id);

-- Metrics table
CREATE TABLE IF NOT EXISTS cerberus.metrics (
    metric_id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    component VARCHAR(32) NOT NULL,
    metric_name VARCHAR(128) NOT NULL,
    metric_value FLOAT NOT NULL,
    labels JSONB
);

CREATE INDEX idx_metrics_timestamp ON cerberus.metrics(timestamp DESC);
CREATE INDEX idx_metrics_component ON cerberus.metrics(component);

-- Create function for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA cerberus TO cerberus;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA cerberus TO cerberus;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA cerberus TO cerberus;

-- Insert sample data for testing
INSERT INTO cerberus.metrics (component, metric_name, metric_value, labels)
VALUES 
    ('gatekeeper', 'requests_processed', 0, '{"environment": "test"}'::jsonb),
    ('labyrinth', 'captures_total', 0, '{"environment": "test"}'::jsonb),
    ('sentinel', 'simulations_total', 0, '{"environment": "test"}'::jsonb)
ON CONFLICT DO NOTHING;

-- Create views for monitoring
CREATE OR REPLACE VIEW cerberus.recent_attacks AS
SELECT 
    e.event_id,
    e.timestamp,
    e.session_id,
    e.client_ip,
    e.data->>'action' as action,
    (e.data->'scores'->>'combined')::float as threat_score,
    e.data->'tags' as tags
FROM cerberus.events e
WHERE e.event_type = 'poi_tagged'
ORDER BY e.timestamp DESC
LIMIT 100;

CREATE OR REPLACE VIEW cerberus.rule_effectiveness AS
SELECT 
    r.rule_id,
    r.created_at,
    r.action,
    r.confidence,
    r.enabled,
    COUNT(e.event_id) as blocks_triggered
FROM cerberus.waf_rules r
LEFT JOIN cerberus.events e ON e.data->>'blocked_by_rule' = r.rule_id
WHERE r.enabled = true
GROUP BY r.rule_id, r.created_at, r.action, r.confidence, r.enabled
ORDER BY blocks_triggered DESC;

COMMENT ON TABLE cerberus.events IS 'All system events from Gatekeeper, Switch, Labyrinth, and Sentinel';
COMMENT ON TABLE cerberus.waf_rules IS 'Active and historical WAF rules';
COMMENT ON TABLE cerberus.attacker_profiles IS 'Behavioral profiles of detected attackers';
COMMENT ON TABLE cerberus.simulations IS 'Payload simulation results from Sentinel';
COMMENT ON TABLE cerberus.captures IS 'Evidence captured in Labyrinth honeypot';
