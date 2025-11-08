# Cerberus Integration Guide

## Using the Evidence Locker System

### For Labyrinth (Evidence Collection)

```python
from labyrinth.capture.session_tracker import get_session_tracker
from labyrinth.capture.har_middleware import HARRecorderMiddleware, extract_payloads_from_request

# Add middleware to FastAPI app
app.add_middleware(HARRecorderMiddleware, payload_extractor=extract_payloads_from_request)

# Finalize session and get evidence pointer
tracker = get_session_tracker()
pointer = tracker.finalize_session(session_id)

# Publish pointer to Kafka/Redis for Sentinel
# pointer.model_dump_json() contains all metadata
```

### For Sentinel (Evidence Consumption)

```python
from shared.evidence.retriever import EvidenceRetriever
from shared.evidence.models import EvidencePointer

# Initialize retriever
retriever = EvidenceRetriever()

# When receiving evidence pointer from message bus
evidence = retriever.retrieve(pointer)

# Access HAR log
har_log = evidence["har_log"]
for entry in har_log.entries:
    print(f"{entry.request['method']} {entry.request['url']}")

# Access metadata
metadata = evidence["metadata"]
print(f"Session: {metadata.session_metadata.session_id}")
print(f"Attacker: {metadata.session_metadata.attacker_ip}")

# Clean up when done
retriever.cleanup(evidence["workspace"])
```

### MinIO Client Direct Usage

```python
from shared.storage.minio_client import get_storage_client

storage = get_storage_client()

# Ensure bucket exists
storage.ensure_bucket("labyrinth-evidence")

# Upload file
upload_info = storage.upload_file(
    "labyrinth-evidence",
    "evt_123/session.har",
    "/path/to/session.har"
)

# Download file
storage.download_file(
    "labyrinth-evidence",
    "evt_123/session.har",
    "/tmp/downloaded.har",
    validate_checksum=upload_info["checksum"]
)

# List objects
objects = storage.list_objects("labyrinth-evidence", prefix="evt_123/")
```

### Authentication

```python
from shared.auth.jwt_handler import create_access_token, decode_token, get_service_token
from fastapi import Depends
from shared.auth.dependencies import get_current_user

# Create user token
token = create_access_token(data={
    "username": "admin",
    "service": "gatekeeper",
    "roles": ["admin"]
})

# Get service token
sentinel_token = get_service_token("sentinel")

# Protect endpoint
@app.post("/api/v1/protected")
async def protected_endpoint(user: TokenData = Depends(get_current_user)):
    return {"message": f"Hello {user.username}"}
```

## Environment Variables

```bash
# MinIO Configuration
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=cerberus
MINIO_SECRET_KEY=cerberus_minio_password
MINIO_SECURE=false

# JWT Configuration
JWT_SECRET_KEY=<your-secret-key>
JWT_EXPIRE_MINUTES=60

# Service API Keys
GATEKEEPER_API_KEY=<secure-key>
SWITCH_API_KEY=<secure-key>
LABYRINTH_API_KEY=<secure-key>
SENTINEL_API_KEY=<secure-key>
WARROOM_API_KEY=<secure-key>
```

## Docker Compose Updates

Add to service environment:

```yaml
labyrinth:
  environment:
    - MINIO_ENDPOINT=minio:9000
    - MINIO_ACCESS_KEY=cerberus
    - MINIO_SECRET_KEY=cerberus_minio_password

sentinel:
  environment:
    - MINIO_ENDPOINT=minio:9000
    - MINIO_ACCESS_KEY=cerberus
    - MINIO_SECRET_KEY=cerberus_minio_password
    - JWT_SECRET_KEY=${JWT_SECRET_KEY}
```
