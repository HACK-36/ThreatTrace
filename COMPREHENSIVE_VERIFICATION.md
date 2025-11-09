# 🔍 Cerberus System - Complete Feature Verification Guide

## 📋 Quick Start - Check Everything is Running

### 1. Start All Services
```bash
cd /Users/mishragaurav/Documents/Cerberus

# Start all services
docker compose up -d

# Wait for services to be ready (30 seconds)
sleep 30

# Check all containers are running
docker compose ps
```

**Expected**: All 12 services should show "Up"

---

## 🏗️ INFRASTRUCTURE VERIFICATION

### 2. Infrastructure Health Check
```bash
echo "=== Infrastructure Health Check ==="

# Redis
echo "Redis:" && docker exec cerberus-redis redis-cli ping && echo "✅ OK"

# PostgreSQL
echo "PostgreSQL:" && docker exec cerberus-postgres psql -U cerberus -d cerberus -c "SELECT 1;" > /dev/null && echo "✅ OK"

# Kafka
echo "Kafka:" && docker exec cerberus-kafka kafka-topics --list --bootstrap-server localhost:9092 > /dev/null && echo "✅ OK"

# MinIO
echo "MinIO:" && curl -s http://localhost:9000/minio/health/live && echo "✅ OK"

# Prometheus
echo "Prometheus:" && curl -s http://localhost:9090/-/healthy && echo "✅ OK"

# Grafana
echo "Grafana:" && curl -s http://localhost:3001/api/health > /dev/null && echo "✅ OK"
```

### 3. Database Functionality Test
```bash
# Comprehensive database test
python3 scripts/test_databases.py
```
**Expected**: "🎉 All database tests passed!"

---

## 🤖 ML MODEL VERIFICATION

### 4. Gatekeeper AI Model Status
```bash
# Check ML model is loaded
curl -s http://localhost:8000/api/v1/gatekeeper/ml-model | python3 -m json.tool
```
**Expected**:
- `"model_loaded": true`
- `"feature_count": 102`
- `"n_estimators": 100`

### 5. Test ML Detection - Normal Request
```bash
curl -s -X POST http://localhost:8000/api/v1/gatekeeper/analyze-features \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "url": "http://example.com/api/users",
    "headers": {"User-Agent": "Mozilla/5.0"},
    "body": "",
    "query_params": {},
    "client_ip": "192.168.1.100",
    "session_id": "normal-test-session"
  }' | python3 -m json.tool
```
**Expected**: `"action": "allow"` or `"tag_poi"` (depending on ML score)

### 6. Test ML Detection - SQL Injection Attack
```bash
curl -s -X POST http://localhost:8000/api/v1/gatekeeper/analyze-features \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "url": "http://example.com/api/users?id=1 UNION SELECT password FROM users",
    "headers": {"User-Agent": "sqlmap/1.0"},
    "body": "",
    "query_params": {"id": "1 UNION SELECT password FROM users"},
    "client_ip": "192.168.1.100",
    "session_id": "sql-attack-test"
  }' | python3 -m json.tool
```
**Expected**:
- High `"ml_anomaly"` score (> 0.7)
- `"sql_patterns": 3`
- `"action": "tag_poi"`

### 7. Test ML Detection - XSS Attack
```bash
curl -s -X POST http://localhost:8000/api/v1/gatekeeper/analyze-features \
  -H "Content-Type: application/json" \
  -d '{
    "method": "POST",
    "url": "http://example.com/comment",
    "headers": {"User-Agent": "Chrome"},
    "body": "<script>alert(document.cookie)</script>",
    "query_params": {},
    "client_ip": "192.168.1.100",
    "session_id": "xss-attack-test"
  }' | python3 -m json.tool
```
**Expected**: `"xss_patterns": 1`, high anomaly score

### 8. Verify Session History in Redis
```bash
# Check session data is stored in Redis
docker exec cerberus-redis redis-cli LRANGE "session:sql-attack-test" 0 -1 | head -1
```
**Expected**: JSON with timestamp, ml_score, features

---

## 🏠 HONEYPOT VERIFICATION

### 9. Labyrinth Decoy APIs
```bash
# Test fake user data
curl -s http://localhost:8002/api/v1/users?limit=3 | python3 -m json.tool
```
**Expected**: Array of fake users with realistic names/emails

### 10. Fake Admin Panel
```bash
# Test honeypot admin endpoint
curl -s http://localhost:8002/admin/config | python3 -m json.tool
```
**Expected**: Fake credentials and configuration data

### 11. Fake Environment File
```bash
# Test .env file disclosure honeypot
curl -s http://localhost:8002/.env | head -10
```
**Expected**: Fake environment variables and secrets

### 12. Fake Documents API
```bash
# Test fake documents
curl -s http://localhost:8002/api/v1/documents | python3 -m json.tool
```
**Expected**: Array of fake document metadata

---

## 🔬 THREAT INTELLIGENCE VERIFICATION

### 13. Sentinel Model Server Health
```bash
curl -s http://localhost:8003/api/v1/sentinel/model-server/health | python3 -m json.tool
```
**Expected**: `"health": "healthy"` with active models

### 14. Trigger Payload Simulation
```bash
# Trigger AI-powered payload simulation
SIM_JOB=$(curl -s -X POST http://localhost:8003/api/v1/sentinel/simulate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sentinel-dev-key-change-me" \
  -d '{
    "payload": {"type": "sql_injection", "value": "1 OR 1=1", "confidence": 0.9},
    "shadow_app_ref": "main",
    "metadata": {}
  }' | python3 -c 'import sys, json; print(json.load(sys.stdin)["job_id"])')

echo "Simulation Job ID: $SIM_JOB"
```

### 15. Check Simulation Result
```bash
# Wait for completion
sleep 5

# Check result
curl -s "http://localhost:8003/api/v1/sentinel/sim-result/$SIM_JOB" | python3 -m json.tool
```
**Expected**: `"status": "completed"`, verdict, execution_time_ms

### 16. Test Payload Analysis
```bash
curl -s -X POST http://localhost:8003/api/v1/sentinel/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "evidence": {
      "session_id": "test",
      "payloads": [{"type": "sql_injection", "value": "1 OR 1=1"}]
    }
  }' | python3 -m json.tool
```
**Expected**: Analysis with verdict

### 17. Check Auto-Generated WAF Rules
```bash
curl -s http://localhost:8003/api/v1/sentinel/rules | python3 -m json.tool
```
**Expected**: Array of WAF rules with confidence scores

---

## 📊 MONITORING STACK VERIFICATION

### 18. Prometheus Targets
```bash
# Check all services are being scraped
curl -s http://localhost:9090/api/v1/targets | python3 -c '
import sys, json
data = json.load(sys.stdin)
active = len(data["data"]["activeTargets"])
print(f"Active targets: {active}")
for target in data["data"]["activeTargets"]:
    print(f"  - {target[\"labels\"][\"job\"]}: {target[\"health\"]}")
'
```
**Expected**: 4+ active targets (gatekeeper, switch, labyrinth, sentinel) all "up"

### 19. Query Metrics
```bash
# Check basic metrics are being collected
curl -s 'http://localhost:9090/api/v1/query?query=up' | python3 -m json.tool
```
**Expected**: All services showing `value: 1`

### 20. Cerberus-Specific Metrics
```bash
# Check custom Cerberus metrics
curl -s 'http://localhost:9090/api/v1/query?query=cerberus_requests_total' | python3 -m json.tool
```
**Expected**: Request counters from each service

### 21. Grafana Dashboard Access
```bash
# Check Grafana is accessible
curl -s http://localhost:3001/api/datasources | python3 -c '
import sys, json
datasources = json.load(sys.stdin)
print(f"Datasources: {len(datasources)}")
for ds in datasources:
    print(f"  - {ds[\"name\"]}: {ds[\"type\"]}")
'
```
**Expected**: Prometheus datasource configured

### 22. MinIO Storage
```bash
# Check MinIO is accessible
curl -s http://localhost:9000/minio/health/live
echo ""

# List buckets (requires MinIO client setup)
echo "MinIO Console: http://localhost:9001 (cerberus/cerberus_minio_password)"
```
**Expected**: MinIO health check returns OK

---

## 🔄 SERVICE INTEGRATION VERIFICATION

### 23. Service Health Check
```bash
echo "=== Service Health Check ==="
curl -s http://localhost:8000/health > /dev/null && echo "✅ Gatekeeper (8000)" || echo "❌ Gatekeeper"
curl -s http://localhost:8001/health > /dev/null && echo "✅ Switch (8001)" || echo "❌ Switch"
curl -s http://localhost:8002/health > /dev/null && echo "✅ Labyrinth (8002)" || echo "❌ Labyrinth"
curl -s http://localhost:8003/health > /dev/null && echo "✅ Sentinel (8003)" || echo "❌ Sentinel"
```

### 24. End-to-End Request Flow
```bash
# Test complete request flow through Switch → Gatekeeper
SESSION_ID="e2e-test-$(date +%s)"

curl -s -X POST http://localhost:8001/api/v1/inspect \
  -H "Content-Type: application/json" \
  -d "{
    \"method\": \"GET\",
    \"url\": \"http://test.com/api?id=1' OR '1'='1\",
    \"headers\": {\"User-Agent\": \"sqlmap\"},
    \"body\": \"\",
    \"query_params\": {},
    \"client_ip\": \"1.2.3.4\",
    \"session_id\": \"$SESSION_ID\"
  }" | python3 -m json.tool
```
**Expected**: Request routed through Switch to Gatekeeper, ML analysis performed

### 25. Database Event Storage
```bash
# Check events are being stored in PostgreSQL
docker exec cerberus-postgres psql -U cerberus -d cerberus -c "
SELECT event_id, event_type, data->>'action' as action, data->'scores'->>'combined' as score
FROM cerberus.events
ORDER BY timestamp DESC
LIMIT 5;
"
```
**Expected**: Recent events with scores and actions

---

## 🧪 ADVANCED TESTING

### 26. Load Testing (Optional)
```bash
# Simple load test - send multiple requests
for i in {1..10}; do
  curl -s -X POST http://localhost:8000/api/v1/gatekeeper/analyze-features \
    -H "Content-Type: application/json" \
    -d "{\"method\":\"GET\",\"url\":\"http://test.com/$i\",\"headers\":{},\"body\":\"\",\"query_params\":{},\"client_ip\":\"1.2.3.$i\",\"session_id\":\"load-test-$i\"}" > /dev/null &
done
wait
echo "Load test completed"
```

### 27. Behavioral Analysis Test
```bash
# Send multiple requests from same session to trigger behavioral analysis
SESSION="behavior-test-$(date +%s)"

for i in {1..5}; do
  curl -s -X POST http://localhost:8000/api/v1/gatekeeper/analyze-features \
    -H "Content-Type: application/json" \
    -d "{
      \"method\": \"GET\",
      \"url\": \"http://test.com/api?id=$i\",
      \"headers\": {\"User-Agent\": \"sqlmap\"},
      \"body\": \"\",
      \"query_params\": {\"id\": \"$i\"},
      \"client_ip\": \"192.168.1.100\",
      \"session_id\": \"$SESSION\"
    }" > /dev/null
  sleep 1
done

# Check session history in Redis
echo "Session history for $SESSION:"
docker exec cerberus-redis redis-cli LLEN "session:$SESSION"
```
**Expected**: Session history grows with multiple entries

### 28. Rule Management Test
```bash
# Check current WAF rules
curl -s http://localhost:8000/api/v1/gatekeeper/rules | python3 -m json.tool
```
**Expected**: Array of active WAF rules

### 29. Statistics Check
```bash
# Check Gatekeeper statistics
curl -s http://localhost:8000/api/v1/gatekeeper/stats | python3 -m json.tool
```
**Expected**: Request counts, blocked counts, etc.

---

## 📈 PERFORMANCE VERIFICATION

### 30. Response Time Test
```bash
# Test ML inference speed
echo "Testing ML inference response time..."
time curl -s -X POST http://localhost:8000/api/v1/gatekeeper/analyze-features \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "url": "http://test.com",
    "headers": {},
    "body": "",
    "query_params": {},
    "client_ip": "1.2.3.4",
    "session_id": "perf-test"
  }' > /dev/null
```
**Expected**: Response time < 200ms

### 31. Memory Usage Check
```bash
# Check service memory usage
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```
**Expected**: All services running with reasonable memory usage

---

## 🔧 TROUBLESHOOTING

### 32. Check Service Logs
```bash
# Check for errors in service logs
echo "=== Checking for errors in logs ==="
for service in gatekeeper switch labyrinth sentinel prometheus grafana; do
  echo "Checking $service logs..."
  docker compose logs --tail=10 $service 2>&1 | grep -i error || echo "  No errors found"
done
```

### 33. Network Connectivity Test
```bash
# Test service-to-service communication
docker exec cerberus-gatekeeper curl -s http://switch:8001/health > /dev/null && echo "✅ Gatekeeper -> Switch" || echo "❌ Gatekeeper -> Switch"
docker exec cerberus-gatekeeper curl -s http://labyrinth:8002/health > /dev/null && echo "✅ Gatekeeper -> Labyrinth" || echo "❌ Gatekeeper -> Labyrinth"
```

### 34. Database Connection Test
```bash
# Test database connections from services
docker exec cerberus-gatekeeper python3 -c "
from shared.database import get_redis_client, get_postgres_client
redis = get_redis_client()
pg = get_postgres_client()
print('Redis:', redis.ping())
print('PostgreSQL:', pg.ping())
"
```

---

## 🎯 QUICK VERIFICATION SCRIPT

### 35. Run All Checks (Automated)
```bash
#!/bin/bash
# Save as verify_all.sh and run with: bash verify_all.sh

echo "🔍 Cerberus System Verification"
echo "================================="

# Infrastructure
echo ""
echo "1. Infrastructure Health:"
docker exec cerberus-redis redis-cli ping > /dev/null && echo "   ✅ Redis" || echo "   ❌ Redis"
docker exec cerberus-postgres psql -U cerberus -d cerberus -c "SELECT 1;" > /dev/null && echo "   ✅ PostgreSQL" || echo "   ❌ PostgreSQL"
curl -s http://localhost:9090/-/healthy > /dev/null && echo "   ✅ Prometheus" || echo "   ❌ Prometheus"
curl -s http://localhost:3001/api/health > /dev/null && echo "   ✅ Grafana" || echo "   ❌ Grafana"

# Services
echo ""
echo "2. Service Health:"
curl -s http://localhost:8000/health > /dev/null && echo "   ✅ Gatekeeper" || echo "   ❌ Gatekeeper"
curl -s http://localhost:8001/health > /dev/null && echo "   ✅ Switch" || echo "   ❌ Switch"
curl -s http://localhost:8002/health > /dev/null && echo "   ✅ Labyrinth" || echo "   ❌ Labyrinth"
curl -s http://localhost:8003/health > /dev/null && echo "   ✅ Sentinel" || echo "   ❌ Sentinel"

# ML Model
echo ""
echo "3. ML Model:"
MODEL_INFO=$(curl -s http://localhost:8000/api/v1/gatekeeper/ml-model)
echo "$MODEL_INFO" | grep -q '"model_loaded": true' && echo "   ✅ Model loaded" || echo "   ❌ Model not loaded"
echo "$MODEL_INFO" | grep -q '"total_features": 102' && echo "   ✅ 102 features" || echo "   ❌ Feature count mismatch"

# Database Test
echo ""
echo "4. Database Functionality:"
python3 scripts/test_databases.py 2>/dev/null | grep -q "All database tests passed" && echo "   ✅ Database tests passed" || echo "   ❌ Database tests failed"

echo ""
echo "================================="
echo "Verification complete!"
```

---

## 📊 SUMMARY REPORT

### 36. Generate System Report
```bash
echo "=== Cerberus System Report ==="
echo "Generated: $(date)"
echo ""

# Container status
echo "Containers Running:"
docker compose ps --format "table {{.Name}}\t{{.Status}}" | grep -E "(Up|running)"

echo ""
# Database stats
echo "Database Statistics:"
docker exec cerberus-postgres psql -U cerberus -d cerberus -c "
SELECT 
    schemaname || '.' || tablename as table_name,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    (SELECT count(*) FROM cerberus.events) as event_count
FROM pg_tables 
WHERE schemaname = 'cerberus' 
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

echo ""
# Redis stats
echo "Redis Statistics:"
docker exec cerberus-redis redis-cli info keyspace | grep -E "^db[0-9]"

echo ""
echo "=== Report Complete ==="
```

---

## 🎯 FEATURE STATUS CHECKLIST

Run these commands to verify each feature:

- [ ] **Infrastructure**: Commands 1-3 (Redis, PostgreSQL, Kafka, MinIO, Prometheus, Grafana)
- [ ] **ML Models**: Commands 4-8 (Model loading, detection, session storage)
- [ ] **Honeypot**: Commands 9-12 (Decoy APIs, fake data)
- [ ] **Threat Intel**: Commands 13-17 (Simulation, analysis, rule generation)
- [ ] **Monitoring**: Commands 18-22 (Prometheus, Grafana, MinIO)
- [ ] **Integration**: Commands 23-25 (Service health, end-to-end flow, event storage)
- [ ] **Advanced**: Commands 26-31 (Load testing, behavioral analysis, performance)
- [ ] **Troubleshooting**: Commands 32-34 (Logs, connectivity, database connections)

**All features should show ✅ status for a fully functional Cerberus system!**

---

## 🚀 JUDGE DEMONSTRATION SCRIPT

For judges, run this sequence:

```bash
# 1. Show system is running
docker compose ps

# 2. Show ML detection
curl -s http://localhost:8000/api/v1/gatekeeper/ml-model | python3 -m json.tool

# 3. Demo SQL injection detection
curl -s -X POST http://localhost:8000/api/v1/gatekeeper/analyze-features -H "Content-Type: application/json" -d '{"method":"GET","url":"http://test.com?id=1 UNION SELECT","headers":{"User-Agent":"sqlmap"},"body":"","query_params":{},"client_ip":"1.2.3.4","session_id":"judge-demo"}' | python3 -m json.tool

# 4. Show honeypot
curl -s http://localhost:8002/api/v1/users?limit=2 | python3 -m json.tool

# 5. Show simulation
curl -s -X POST http://localhost:8003/api/v1/sentinel/simulate -H "Content-Type: application/json" -H "X-API-Key: sentinel-dev-key-change-me" -d '{"payload":{"type":"sql_injection","value":"1 OR 1=1","confidence":0.9},"shadow_app_ref":"main","metadata":{}}' | python3 -m json.tool

# 6. Show monitoring
echo "Grafana: http://localhost:3001 (admin/admin)"
echo "Prometheus: http://localhost:9090"
```

**This comprehensive guide ensures you can verify every feature of Cerberus is working correctly!** 🎯
