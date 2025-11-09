"""
Prometheus metrics definitions for Cerberus services
"""
from prometheus_client import Counter, Histogram, Gauge

# Evidence operations
EVIDENCE_OPERATIONS = Counter(
    'cerberus_evidence_operations_total',
    'Total evidence operations',
    ['service', 'operation', 'status']
)

# Kafka messages
KAFKA_MESSAGES = Counter(
    'cerberus_kafka_messages_total',
    'Total Kafka messages processed',
    ['service', 'topic', 'status']
)

# Sentinel inference metrics
SENTINEL_INFERENCE_LATENCY = Histogram(
    'sentinel_inference_latency_seconds',
    'Sentinel ML inference latency',
    ['model_type']
)

SENTINEL_PREDICTIONS = Counter(
    'sentinel_predictions_total',
    'Total predictions made',
    ['model_type', 'verdict']
)

SENTINEL_CACHE_HITS = Counter(
    'sentinel_cache_hits_total',
    'Cache hits for inference',
    ['cache_type']
)

# General service metrics
cerberus_requests_total = Counter(
    'cerberus_requests_total',
    'Total requests processed by Cerberus components',
    ['service']
)

requests_in_progress = Gauge(
    'cerberus_requests_in_progress',
    'Requests currently being processed',
    ['service', 'endpoint']
)

request_duration_seconds = Histogram(
    'cerberus_request_duration_seconds',
    'Request duration in seconds',
    ['service', 'endpoint', 'method']
)

cerberus_poi_tagged_total = Counter(
    'cerberus_poi_tagged_total',
    'Total requests tagged as Person of Interest'
)

cerberus_requests_blocked_total = Counter(
    'cerberus_requests_blocked_total',
    'Total requests blocked by Cerberus'
)

cerberus_requests_allowed_total = Counter(
    'cerberus_requests_allowed_total',
    'Total requests allowed by Cerberus'
)

cerberus_ml_anomaly_score_bucket = Histogram(
    'cerberus_ml_anomaly_score_bucket',
    'ML anomaly scores distribution',
    ['service'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

cerberus_attack_patterns_total = Counter(
    'cerberus_attack_patterns_total',
    'Total detected attack patterns',
    ['attack_type']
)

cerberus_payloads_captured_total = Counter(
    'cerberus_payloads_captured_total',
    'Total payloads captured by honeypot'
)

cerberus_simulations_total = Counter(
    'cerberus_simulations_total',
    'Total payload simulations run'
)

cerberus_rules_generated_total = Counter(
    'cerberus_rules_generated_total',
    'Total WAF rules auto-generated'
)

cerberus_db_operations_total = Counter(
    'cerberus_db_operations_total',
    'Database operations by Cerberus',
    ['db', 'operation']
)
