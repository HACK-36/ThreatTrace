# 🔍 Cerberus System Verification Checklist

## Infrastructure Components

### ✅ Docker Services
```bash
docker compose ps
```
**Expected:** All services UP
- cerberus-kafka
- cerberus-postgres
- cerberus-redis
- cerberus-minio
- cerberus-gatekeeper
- cerberus-switch
- cerberus-labyrinth
- cerberus-sentinel
- cerberus-prometheus
- cerberus-grafana

### ✅ Health Checks
```bash
# Gatekeeper
curl -s http://localhost:8000/health | python3 -m json.tool

# Switch
curl -s http://localhost:8001/health | python3 -m json.tool

# Labyrinth
curl -s http://localhost:8002/health | python3 -m json.tool

# Sentinel
curl -s http://localhost:8003/health | python3 -m json.tool
```

---

## 🤖 ML Model Verification

### Gatekeeper AI Models

#### 1. Model Info Endpoint
```bash
curl -s http://localhost:8000/api/v1/gatekeeper/ml-model | python3 -m json.tool
```
**Expected:**
- Isolation Forest model loaded
- 102 features configured
- LSTM behavioral classifier initialized

#### 2. Feature Extraction Test
```bash
curl -s -X POST http://localhost:8000/api/v1/gatekeeper/analyze-features \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "url": "http://test.com/api",
    "headers": {"User-Agent": "Mozilla/5.0"},
    "body": "",
    "query_params": {},
    "client_ip": "1.2.3.4",
    "session_id": "test-1"
  }' | python3 -m json.tool
```
**Expected:**
- Returns scores object
- Returns verdict object
- Returns top_features
- Returns analysis with pattern counts

#### 3. SQL Injection Detection
```bash
curl -s -X POST http://localhost:8000/api/v1/gatekeeper/analyze-features \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "url": "http://test.com/api?id=1 UNION SELECT password FROM users",
    "headers": {"User-Agent": "sqlmap"},
    "body": "",
    "query_params": {"id": "1 UNION SELECT password FROM users"},
    "client_ip": "1.2.3.4",
    "session_id": "attack-1"
  }' | python3 -m json.tool
```
**Expected:**
- High sql_keyword_count
- High modsecurity score (> 80)
- High ml_anomaly score (> 0.5)
- Action: "tag_poi" or "block"

#### 4. XSS Detection
```bash
curl -s -X POST http://localhost:8000/api/v1/gatekeeper/analyze-features \
  -H "Content-Type: application/json" \
  -d '{
    "method": "POST",
    "url": "http://test.com/comment",
    "headers": {"User-Agent": "Chrome"},
    "body": "<script>alert(1)</script>",
    "query_params": {},
    "client_ip": "1.2.3.4",
    "session_id": "attack-2"
  }' | python3 -m json.tool
```
**Expected:**
- xss_pattern_count > 0
- High combined score
- Action: "tag_poi"

### Sentinel AI Models

#### 1. Model Server Health
```bash
curl -s http://localhost:8003/api/v1/sentinel/model-server/health | python3 -m json.tool
```
**Expected:**
- active_model present
- canary_model info
- health: "healthy"

#### 2. ML Analysis Endpoint
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
**Expected:**
- Returns verdict
- Returns explanation

#### 3. Payload Prediction
```bash
curl -s -X POST http://localhost:8003/api/v1/sentinel/predict-payload \
  -H "Content-Type: application/json" \
  -d '{
    "payload": "1 UNION SELECT NULL",
    "context": {}
  }' | python3 -m json.tool
```
**Expected:**
- Returns prediction with confidence
- Returns payload_type

---

## 🎭 Honeypot Functionality

### Labyrinth Decoy APIs

#### 1. Fake Users API
```bash
curl -s http://localhost:8002/api/v1/users?limit=5 | python3 -m json.tool
```
**Expected:**
- Returns array of fake users
- Realistic names and emails

#### 2. Fake Documents
```bash
curl -s http://localhost:8002/api/v1/documents | python3 -m json.tool
```
**Expected:**
- Returns fake document list

#### 3. Fake Admin Config (Honeypot Trigger)
```bash
curl -s http://localhost:8002/admin/config | python3 -m json.tool
```
**Expected:**
- Returns fake credentials
- Request is logged for analysis

#### 4. Fake .env File
```bash
curl -s http://localhost:8002/.env
```
**Expected:**
- Returns fake environment variables

---

## 🔬 Simulation & Sandbox

### Sentinel Simulation Engine

#### 1. Trigger Simulation
```bash
JOB_ID=$(curl -s -X POST http://localhost:8003/api/v1/sentinel/simulate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sentinel-dev-key-change-me" \
  -d '{
    "payload": {"type": "sql_injection", "value": "1 OR 1=1", "confidence": 0.9},
    "shadow_app_ref": "main",
    "metadata": {}
  }' | python3 -c 'import sys, json; print(json.load(sys.stdin)["job_id"])')

echo "Job ID: $JOB_ID"
```

#### 2. Check Simulation Result
```bash
# Wait for completion
sleep 5

curl -s "http://localhost:8003/api/v1/sentinel/sim-result/$JOB_ID" | python3 -m json.tool
```
**Expected:**
- status: "completed"
- verdict present
- execution_time_ms present

#### 3. Sandbox Security
```bash
curl -s http://localhost:8003/api/v1/sentinel/sandbox/audit-log | python3 -m json.tool
```
**Expected:**
- Returns sandbox activity log

---

## 📊 Observability Stack

### Prometheus

#### 1. Prometheus Health
```bash
curl -s http://localhost:9090/-/healthy
```
**Expected:** "Prometheus Server is Healthy."

#### 2. Check Targets
```bash
curl -s http://localhost:9090/api/v1/targets | python3 -c 'import sys, json; data=json.load(sys.stdin); print("Active targets:", len(data["data"]["activeTargets"]))'
```
**Expected:** 4+ active targets (gatekeeper, switch, labyrinth, sentinel)

#### 3. Query Metrics
```bash
curl -s 'http://localhost:9090/api/v1/query?query=up' | python3 -m json.tool
```
**Expected:** All services up=1

### Grafana

#### 1. Grafana Health
```bash
curl -s http://localhost:3001/api/health | python3 -m json.tool
```
**Expected:**
- database: "ok"

#### 2. Check Datasources
```bash
curl -s -u admin:admin http://localhost:3001/api/datasources | python3 -m json.tool
```
**Expected:** Prometheus datasource configured

### MinIO

#### 1. MinIO Health
```bash
curl -s http://localhost:9000/minio/health/live
```
**Expected:** Empty 200 response

#### 2. List Buckets
```bash
# Requires MinIO client or AWS CLI
# mc ls minio
```

---

## 🔐 Security & Auth

### API Authentication

#### 1. Sentinel API Key Auth
```bash
# Without API key (should fail)
curl -s -X POST http://localhost:8003/api/v1/sentinel/simulate \
  -H "Content-Type: application/json" \
  -d '{"payload":{}, "shadow_app_ref": "main", "metadata": {}}'
```
**Expected:** 403 Forbidden or 401 Unauthorized

#### 2. With Valid API Key
```bash
curl -s -X POST http://localhost:8003/api/v1/sentinel/simulate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sentinel-dev-key-change-me" \
  -d '{"payload":{"type":"test","value":"test","confidence":0.5}, "shadow_app_ref": "main", "metadata": {}}'
```
**Expected:** 200 OK with job_id

---

## 🔄 Integration Tests

### End-to-End Attack Flow

#### 1. Complete Attack Simulation
```bash
SESSION="e2e-test-$(date +%s)"

# Step 1: Initial request through Gatekeeper
curl -s -X POST http://localhost:8000/api/v1/inspect \
  -H "Content-Type: application/json" \
  -d "{
    \"method\": \"GET\",
    \"url\": \"http://test.com/api?id=1' OR '1'='1\",
    \"headers\": {\"User-Agent\": \"sqlmap\"},
    \"body\": \"\",
    \"query_params\": {},
    \"client_ip\": \"1.2.3.4\",
    \"session_id\": \"$SESSION\"
  }" | python3 -m json.tool

# Step 2: Check session history
curl -s http://localhost:8000/api/v1/gatekeeper/stats | python3 -m json.tool

echo "E2E Test Session: $SESSION"
```

### Dataset & Training

#### 1. Add Training Sample
```bash
curl -s -X POST http://localhost:8003/api/v1/sentinel/dataset/add-sample \
  -H "Content-Type: application/json" \
  -d '{
    "sample_type": "payload",
    "data": {"type": "sql_injection", "value": "test"},
    "label": "malicious",
    "confidence": 0.9,
    "source": "test"
  }' | python3 -m json.tool
```

#### 2. Dataset Statistics
```bash
curl -s http://localhost:8003/api/v1/sentinel/dataset/stats | python3 -m json.tool
```

---

## 📈 Performance Tests

### Latency Checks

```bash
# Gatekeeper ML inference latency
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
**Expected:** < 100ms for feature extraction + ML inference

---

## 📋 Final Checklist

- [ ] All Docker services running
- [ ] All health endpoints return 200 OK
- [ ] Gatekeeper ML model loaded
- [ ] Gatekeeper detects SQL injection
- [ ] Gatekeeper detects XSS
- [ ] Sentinel model server healthy
- [ ] Sentinel simulations execute
- [ ] Labyrinth honeypot APIs respond
- [ ] Prometheus scraping all targets
- [ ] Grafana accessible
- [ ] MinIO accessible
- [ ] API authentication working
- [ ] End-to-end attack flow works
- [ ] Dataset management functional
- [ ] Performance within acceptable limits

---

## 🐛 Troubleshooting

### Service Won't Start
```bash
# Check logs
docker compose logs -f <service-name>

# Rebuild
docker compose build <service-name>
docker compose up -d <service-name>
```

### ML Model Errors
```bash
# Check Gatekeeper logs for model loading
docker compose logs gatekeeper | grep -i model

# Verify models directory exists
docker exec cerberus-gatekeeper ls -la /app/gatekeeper/ml/models/
```

### Prometheus Not Scraping
```bash
# Check Prometheus config
docker exec cerberus-prometheus cat /etc/prometheus/prometheus.yml

# Check network connectivity
docker exec cerberus-prometheus wget -O- http://gatekeeper:8000/health
```
