# Project Cerberus - Complete Structure

```
cerberus/
├── README.md                          # Main documentation
├── QUICKSTART.md                      # 5-minute setup guide
├── PROJECT_SUMMARY.md                 # Implementation summary
├── STRUCTURE.md                       # This file
├── LICENSE                            # Apache 2.0 license
├── requirements.txt                   # Python dependencies
├── pytest.ini                         # Test configuration
├── Makefile                           # Build and run commands
├── docker-compose.yml                 # Multi-service orchestration
├── .gitignore                         # Git ignore patterns
│
├── docs/                              # Documentation
│   └── architecture.md                # System architecture
│
├── gatekeeper/                        # WAF + ML Triage Component
│   ├── api/
│   │   └── main.py                    # FastAPI service (8000)
│   └── ml/
│       ├── feature_extractor.py       # 102-feature extraction
│       └── anomaly_detector.py        # Isolation Forest + LSTM
│
├── switch/                            # Session Routing Component
│   └── api/
│       └── main.py                    # FastAPI service (8001)
│
├── labyrinth/                         # Honeypot Component
│   ├── app/
│   │   └── main.py                    # FastAPI decoy app (8002)
│   └── decoy_gen/
│       └── data_generator.py          # Synthetic data generation
│
├── sentinel/                          # AI Analysis Component
│   ├── api/
│   │   └── main.py                    # FastAPI service (8003)
│   ├── profiler/
│   │   └── behavioral_profiler.py     # TTP mapping & intent classification
│   ├── simulator/
│   │   └── payload_simulator.py       # Sandboxed payload execution
│   └── rule_gen/
│       └── rule_generator.py          # Automated rule synthesis
│
├── shared/                            # Shared Libraries
│   └── events/
│       └── schemas.py                 # Pydantic event models
│
├── infrastructure/                    # Deployment Configs
│   ├── docker/
│   │   ├── Dockerfile.gatekeeper
│   │   ├── Dockerfile.switch
│   │   ├── Dockerfile.labyrinth
│   │   └── Dockerfile.sentinel
│   ├── postgres/
│   │   └── init.sql                   # Database schema
│   ├── prometheus/
│   │   └── prometheus.yml             # Metrics config
│   └── grafana/
│       ├── dashboards/
│       └── datasources/
│
├── scripts/                           # Automation Scripts
│   ├── demo.sh                        # Interactive demo (executable)
│   └── panic.sh                       # Emergency shutdown (executable)
│
├── tests/                             # Test Suite
│   ├── unit/
│   │   └── test_feature_extractor.py  # ML feature tests
│   └── integration/
│       └── test_e2e_flow.py           # End-to-end acceptance test
│
└── data/                              # Runtime Data (gitignored)
    ├── events/                        # Event logs (.gitkeep)
    ├── captures/                      # Honeypot captures (.gitkeep)
    ├── models/                        # ML models (.gitkeep)
    ├── simulations/                   # Simulation results (.gitkeep)
    └── samples/
        └── sample_events.json         # Example event data
```

## Key Files by Function

### Entry Points
- `docker-compose.yml` - Start entire system
- `Makefile` - Build, test, run commands
- `scripts/demo.sh` - Run demonstration

### Core Services
- `gatekeeper/api/main.py` - WAF with ML detection (Port 8000)
- `switch/api/main.py` - Session router (Port 8001)
- `labyrinth/app/main.py` - Honeypot (Port 8002)
- `sentinel/api/main.py` - AI engine (Port 8003)

### ML & AI
- `gatekeeper/ml/feature_extractor.py` - Extract 102 features
- `gatekeeper/ml/anomaly_detector.py` - Isolation Forest model
- `sentinel/profiler/behavioral_profiler.py` - Attacker profiling
- `sentinel/simulator/payload_simulator.py` - Sandbox execution
- `sentinel/rule_gen/rule_generator.py` - Auto-generate WAF rules

### Data Models
- `shared/events/schemas.py` - All event schemas (POI, Capture, Simulation, Rule)

### Infrastructure
- `infrastructure/docker/Dockerfile.*` - Container definitions
- `infrastructure/postgres/init.sql` - Database tables and indexes

### Testing
- `tests/unit/test_feature_extractor.py` - Unit tests
- `tests/integration/test_e2e_flow.py` - Integration & E2E tests

### Documentation
- `README.md` - Overview, setup, legal
- `QUICKSTART.md` - Quick start (5 min)
- `PROJECT_SUMMARY.md` - Complete implementation summary
- `docs/architecture.md` - Technical architecture

## Lines of Code Summary

**Python Code:**
- Gatekeeper: ~600 LOC (feature extraction + ML + API)
- Switch: ~300 LOC (routing logic + API)
- Labyrinth: ~500 LOC (honeypot app + data generation)
- Sentinel: ~800 LOC (profiler + simulator + rule gen + API)
- Shared: ~300 LOC (event schemas)
- Tests: ~400 LOC
- **Total Python: ~2,900 LOC**

**Configuration:**
- Docker Compose: ~150 LOC
- Dockerfiles: ~100 LOC
- SQL Schema: ~200 LOC
- Makefile: ~100 LOC
- **Total Config: ~550 LOC**

**Scripts & Docs:**
- Demo script: ~300 LOC
- Documentation: ~2,000 LOC
- **Total: ~2,300 LOC**

**Grand Total: ~5,750 LOC** (excluding dependencies)

## Component Dependencies

```
Gatekeeper (8000)
├── Uses: Kafka (events), Redis (sessions), PostgreSQL (rules)
├── Emits: POITaggedEvent
└── Receives: Rule updates from Sentinel

Switch (8001)
├── Uses: Redis (session pins)
├── Receives: POITaggedEvent from Gatekeeper
└── Routes: Production vs Labyrinth

Labyrinth (8002)
├── Uses: Kafka (events), MinIO (evidence)
├── Receives: Requests from Switch
└── Emits: PayloadCapturedEvent

Sentinel (8003)
├── Uses: Docker (sandboxes), PostgreSQL (results), Kafka (events)
├── Receives: PayloadCapturedEvent from Labyrinth
├── Emits: SimulationCompleteEvent, RuleGeneratedEvent
└── Pushes: Rules to Gatekeeper
```

## Data Flow

```
1. Request → Gatekeeper
2. Gatekeeper → POI Tag → Kafka
3. Switch consumes POI Tag
4. Switch pins session → Labyrinth
5. Labyrinth captures → PayloadCapturedEvent → Kafka
6. Sentinel consumes PayloadCapturedEvent
7. Sentinel → Profile + Simulate + Generate Rule
8. Sentinel → Push Rule → Gatekeeper
9. Gatekeeper blocks future identical attacks
```

## Quick Command Reference

```bash
# Setup
make init               # Create directories
make build              # Build images

# Run
make up                 # Start all services
make demo               # Run demonstration
make down               # Stop services

# Monitor
make logs               # View all logs
make logs-gatekeeper    # View specific service
make health             # Check service health
make status             # Service status

# Test
make test-unit          # Unit tests
make test-integration   # Integration tests
make test-e2e          # Full E2E test

# Emergency
make panic              # Emergency shutdown

# Clean
make clean              # Remove containers/volumes
make clean-all          # Deep clean (including images)
```

## Service Ports

- **8000** - Gatekeeper API
- **8001** - Switch API
- **8002** - Labyrinth (Honeypot)
- **8003** - Sentinel API
- **8080** - Production Mock Backend
- **9000** - MinIO Storage
- **9001** - MinIO Console
- **9090** - Prometheus
- **3001** - Grafana Dashboard
- **5432** - PostgreSQL
- **6379** - Redis
- **9092** - Kafka

## Environment Requirements

**Minimum:**
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM
- 20GB Disk

**Recommended:**
- Docker 24.0+
- Docker Compose 2.20+
- 16GB RAM
- 50GB Disk
- Multi-core CPU

## File Counts

- **Python files:** 13
- **Dockerfiles:** 4
- **Config files:** 6 (docker-compose, pytest.ini, etc.)
- **Shell scripts:** 2
- **Documentation:** 5
- **Test files:** 2
- **SQL files:** 1

**Total tracked files:** ~35 core files

---

**Built with ❤️ for defensive security research**
