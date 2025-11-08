# Cerberus Quick Start Guide

Get Cerberus up and running in 5 minutes.

## Prerequisites

- **Docker** 20.10+ and **Docker Compose** 2.0+
- **Python** 3.11+ (for local development)
- **8GB RAM** minimum (16GB recommended)
- **20GB disk space** for images and data

## Step 1: Clone and Setup

```bash
cd /path/to/Cerberus

# Initialize data directories
make init

# Verify structure
ls -la data/
```

## Step 2: Build Images

```bash
# Build all Docker images (takes 5-10 minutes)
make build

# Verify images
docker images | grep cerberus
```

## Step 3: Start Services

```bash
# Start all Cerberus services
make up

# Services will start in this order:
# 1. Infrastructure (Kafka, PostgreSQL, Redis, MinIO)
# 2. Gatekeeper (WAF)
# 3. Switch (Router)
# 4. Labyrinth (Honeypot)
# 5. Sentinel (AI Engine)
# 6. Monitoring (Prometheus, Grafana)

# Check service status
make status

# View logs
make logs
```

Wait approximately 30 seconds for all services to initialize.

## Step 4: Verify Health

```bash
# Check all services are healthy
make health

# Expected output:
# ✓ Gatekeeper: healthy
# ✓ Switch: healthy
# ✓ Labyrinth: healthy
# ✓ Sentinel: healthy
```

Or manually:

```bash
curl http://localhost:8000/health  # Gatekeeper
curl http://localhost:8001/health  # Switch
curl http://localhost:8002/health  # Labyrinth
curl http://localhost:8003/health  # Sentinel
```

## Step 5: Run the Demo

```bash
# Run interactive demo showing complete attack-to-block flow
make demo
```

The demo will:
1. Send normal traffic (baseline)
2. Simulate SQL injection attack
3. Redirect attacker to honeypot
4. Capture attack payloads
5. Profile attacker behavior
6. Simulate payload in sandbox
7. Auto-generate WAF rule
8. Verify subsequent attacks are blocked

**Demo duration:** ~2-3 minutes

## Step 6: Explore the UI

### Grafana Dashboard (Metrics & Monitoring)

```bash
# Open Grafana
make metrics

# Or manually:
open http://localhost:3001
```

**Login:**
- Username: `admin`
- Password: `admin`

### MinIO Console (Evidence Storage)

```bash
open http://localhost:9001
```

**Login:**
- Username: `cerberus`
- Password: `cerberus_minio_password`

### API Endpoints

- **Gatekeeper API:** http://localhost:8000/docs
- **Switch API:** http://localhost:8001/docs
- **Labyrinth:** http://localhost:8002 (honeypot - browse at your own risk!)
- **Sentinel API:** http://localhost:8003/docs

## Common Commands

```bash
# View logs for specific service
make logs-gatekeeper
make logs-sentinel

# Restart all services
make restart

# Stop services
make down

# Emergency shutdown (panic button)
make panic

# Run tests
make test-unit
make test-integration
make test-e2e
```

## Quick Test - Manual Attack

### 1. Normal Request

```bash
curl -X POST http://localhost:8000/api/v1/inspect \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "url": "/api/users",
    "headers": {"User-Agent": "Mozilla/5.0"},
    "body": "",
    "query_params": {},
    "client_ip": "192.168.1.100",
    "session_id": "test_normal",
    "metadata": {}
  }'
```

**Expected:** `"action": "allow"`

### 2. SQL Injection Attack

```bash
curl -X POST http://localhost:8000/api/v1/inspect \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "url": "/api/users?id=1'\'' OR '\''1'\''='\''1",
    "headers": {"User-Agent": "sqlmap/1.0"},
    "body": "",
    "query_params": {"id": "1'\'' OR '\''1'\''='\''1"},
    "client_ip": "203.0.113.42",
    "session_id": "test_attack",
    "metadata": {}
  }'
```

**Expected:** `"action": "tag_poi"` or `"action": "block"`

### 3. Interact with Honeypot

```bash
# This will be captured!
curl "http://localhost:8002/api/v1/users?id=1' OR '1'='1"
curl "http://localhost:8002/admin"
curl "http://localhost:8002/.env"
```

All interactions are logged to `data/captures/`

### 4. Check Generated Rules

```bash
curl http://localhost:8003/api/v1/sentinel/rules | jq
```

## Troubleshooting

### Services Not Starting

```bash
# Check Docker status
docker ps -a

# View error logs
docker-compose logs gatekeeper
docker-compose logs sentinel

# Restart problematic service
docker-compose restart gatekeeper
```

### Port Conflicts

If ports 8000-8003 are in use, edit `docker-compose.yml`:

```yaml
services:
  gatekeeper:
    ports:
      - "18000:8000"  # Change external port
```

### Out of Memory

Increase Docker memory limit:
- Docker Desktop → Settings → Resources → Memory → 8GB+

### Simulation Timeouts

Sentinel needs Docker socket access for sandboxing:

```bash
# Verify Docker socket is mounted
docker inspect cerberus-sentinel | grep docker.sock
```

## Next Steps

1. **Read the Architecture:** `docs/architecture.md`
2. **Run Tests:** `make test`
3. **Customize Rules:** Edit `gatekeeper/rules/`
4. **Deploy to K8s:** See `infrastructure/kubernetes/`
5. **Integrate SIEM:** See `docs/integrations.md`

## Production Deployment

⚠️ **DO NOT use default credentials in production!**

Before production deployment:

1. Change all passwords in `docker-compose.yml`
2. Enable mTLS for inter-service communication
3. Configure proper secrets management (Vault, AWS Secrets Manager)
4. Set up backup and disaster recovery
5. Configure alerts and monitoring
6. Review security hardening checklist
7. Conduct penetration testing on your test infrastructure

See `docs/deployment.md` for production best practices.

## Getting Help

- **Documentation:** `docs/`
- **Issues:** Check logs in `data/events/`
- **Panic Button:** `make panic` for emergency shutdown

## Legal Reminder

⚠️ **Deploy only on infrastructure you own or have explicit permission to test.**

See `README.md` for full legal disclaimer.

---

**Ready to defend? Let's go! 🛡️**
