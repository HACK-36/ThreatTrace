"""
Evidence Builder for Labyrinth
Constructs digital evidence packages from captured session data
"""
import os
import json
import hashlib
import tempfile
import shutil
import time
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from shared.evidence.models import (
    EvidencePackage, EvidenceMetadata, SessionMetadata,
    BehaviorProfile, HARLog, HARLogEntry, PayloadArtifact,
    EvidencePointer
)
from shared.storage.minio_client import get_storage_client
from shared.utils.metrics import (
    record_evidence_creation,
    payloads_extracted,
    storage_operations
)


class EvidenceBuilder:
    """
    Builds structured evidence packages from Labyrinth captures
    
    Workflow:
    1. Initialize with event_id and session metadata
    2. Add HAR entries as requests/responses arrive
    3. Add extracted payloads
    4. Optionally add uploaded files
    5. Build package and upload to MinIO
    6. Return evidence pointer for messaging
    """
    
    def __init__(self, event_id: str, session_id: str, attacker_ip: str, user_agent: str):
        """
        Initialize evidence builder
        
        Args:
            event_id: Unique event ID
            session_id: Session identifier
            attacker_ip: Source IP
            user_agent: User-Agent header
        """
        self.event_id = event_id
        self.session_id = session_id
        self.attacker_ip = attacker_ip
        self.user_agent = user_agent
        
        # Session tracking
        self.session_start = datetime.utcnow().isoformat()
        self.session_end = None
        self.fingerprint = self._generate_fingerprint()
        
        # Collectors
        self.har_entries: List[HARLogEntry] = []
        self.payloads: List[PayloadArtifact] = []
        self.uploaded_files: List[Dict[str, str]] = []
        self.tags: List[str] = []
        
        # Temporary workspace
        self.workspace = tempfile.mkdtemp(prefix=f"evidence_{event_id}_")
        
    def _generate_fingerprint(self) -> str:
        """Generate session fingerprint from IP + UA"""
        data = f"{self.attacker_ip}:{self.user_agent}"
        return hashlib.md5(data.encode()).hexdigest()[:16]
    
    def add_har_entry(
        self,
        method: str,
        url: str,
        request_headers: Dict[str, str],
        request_body: str,
        response_status: int,
        response_headers: Dict[str, str],
        response_body: str,
        start_time: datetime,
        duration_ms: float
    ):
        """
        Add HAR entry for request/response pair
        
        Args:
            method: HTTP method
            url: Request URL
            request_headers: Request headers
            request_body: Request body
            response_status: HTTP status code
            response_headers: Response headers
            response_body: Response body
            start_time: Request start time
            duration_ms: Total duration
        """
        entry = HARLogEntry(
            startedDateTime=start_time.isoformat(),
            time=duration_ms,
            request={
                "method": method,
                "url": url,
                "httpVersion": "HTTP/1.1",
                "headers": [{"name": k, "value": v} for k, v in request_headers.items()],
                "bodySize": len(request_body),
                "postData": {"text": request_body} if request_body else {}
            },
            response={
                "status": response_status,
                "statusText": "OK" if 200 <= response_status < 300 else "Error",
                "httpVersion": "HTTP/1.1",
                "headers": [{"name": k, "value": v} for k, v in response_headers.items()],
                "bodySize": len(response_body),
                "content": {
                    "size": len(response_body),
                    "mimeType": response_headers.get("Content-Type", "application/octet-stream"),
                    "text": response_body[:1000] if len(response_body) < 10000 else None  # Truncate large responses
                }
            },
            timings={
                "send": 5.0,  # Estimate
                "wait": duration_ms - 10.0,
                "receive": 5.0
            }
        )
        
        self.har_entries.append(entry)
    
    def add_payload(
        self,
        payload_type: str,
        payload_value: str,
        location: str,
        confidence: float,
        save_as_file: bool = False
    ):
        """
        Add extracted malicious payload
        
        Args:
            payload_type: Type of payload (sql_injection, xss, etc.)
            payload_value: Actual payload content
            location: Where found (query.id, body.username, etc.)
            confidence: Detection confidence (0-1)
            save_as_file: Whether to save payload as separate file
        """
        artifact_id = f"payload_{len(self.payloads):03d}"
        checksum = hashlib.sha256(payload_value.encode()).hexdigest()
        
        file_path = None
        if save_as_file:
            file_path = f"payloads/{artifact_id}.txt"
            full_path = os.path.join(self.workspace, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(payload_value)
        
        payload = PayloadArtifact(
            artifact_id=artifact_id,
            payload_type=payload_type,
            payload_value=payload_value,
            location=location,
            confidence=confidence,
            file_path=file_path,
            checksum=checksum
        )
        
        self.payloads.append(payload)
    
    def add_uploaded_file(self, filename: str, file_path: str, file_size: int):
        """
        Add metadata about uploaded malicious file
        
        Args:
            filename: Original filename
            file_path: Path where file is stored
            file_size: File size in bytes
        """
        with open(file_path, 'rb') as f:
            checksum = hashlib.sha256(f.read()).hexdigest()
        
        self.uploaded_files.append({
            "filename": filename,
            "size": file_size,
            "checksum": checksum,
            "stored_path": file_path
        })
    
    def add_tag(self, tag: str):
        """Add tag to evidence package"""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def build_and_upload(
        self,
        bucket_name: str = "labyrinth-evidence",
        behavior_profile: Optional[BehaviorProfile] = None
    ) -> EvidencePointer:
        """
        Build evidence package and upload to MinIO
        
        Args:
            bucket_name: Target MinIO bucket
            behavior_profile: Optional behavioral analysis
            
        Returns:
            Evidence pointer for messaging
        """
        self.session_end = datetime.utcnow().isoformat()
        
        # Create HAR log
        har_log = HARLog(entries=self.har_entries)
        
        # Save HAR to workspace
        har_path = os.path.join(self.workspace, "session.har")
        with open(har_path, 'w') as f:
            json.dump(har_log.model_dump(), f, indent=2)
        
        # Save metadata
        session_meta = SessionMetadata(
            session_id=self.session_id,
            attacker_ip=self.attacker_ip,
            user_agent=self.user_agent,
            fingerprint=self.fingerprint,
            session_start=self.session_start,
            session_end=self.session_end,
            request_count=len(self.har_entries),
            total_duration_ms=int((datetime.fromisoformat(self.session_end) - 
                                  datetime.fromisoformat(self.session_start)).total_seconds() * 1000),
            tags=self.tags
        )
        
        storage_location = f"s3://{bucket_name}/{self.event_id}/"
        
        evidence_metadata = EvidenceMetadata(
            event_id=self.event_id,
            session_metadata=session_meta,
            behavior_profile=behavior_profile,
            storage_location=storage_location,
            tags=self.tags
        )
        
        metadata_path = os.path.join(self.workspace, "metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump(evidence_metadata.model_dump(), f, indent=2)
        
        # Save behavior profile if provided
        if behavior_profile:
            behavior_path = os.path.join(self.workspace, "behavior.json")
            with open(behavior_path, 'w') as f:
                json.dump(behavior_profile.model_dump(), f, indent=2)
        
        # Upload to MinIO
        upload_start = time.time()
        storage = get_storage_client()
        storage.ensure_bucket(bucket_name)
        
        # Upload all files in workspace
        uploaded_artifacts = []
        for root, dirs, files in os.walk(self.workspace):
            for file in files:
                local_path = os.path.join(root, file)
                relative_path = os.path.relpath(local_path, self.workspace)
                object_name = f"{self.event_id}/{relative_path}"

                try:
                    upload_info = storage.upload_file(
                        bucket_name,
                        object_name,
                        local_path
                    )
                    uploaded_artifacts.append(upload_info)
                    storage_operations.labels(
                        service="labyrinth",
                        operation="upload",
                        status="success"
                    ).inc()
                except Exception:
                    storage_operations.labels(
                        service="labyrinth",
                        operation="upload",
                        status="error"
                    ).inc()
                    raise
        
        # Calculate package checksum
        all_checksums = "".join([a["checksum"] for a in uploaded_artifacts])
        package_checksum = hashlib.sha256(all_checksums.encode()).hexdigest()

        # Create evidence pointer
        pointer = EvidencePointer(
            event_id=self.event_id,
            capture_id=evidence_metadata.capture_id,
            session_id=self.session_id,
            attacker_ip=self.attacker_ip,
            location=storage_location,
            payload_count=len(self.payloads),
            request_count=len(self.har_entries),
            checksum=package_checksum,
            tags=self.tags
        )

        # Record metrics
        total_bytes = sum(artifact["size"] for artifact in uploaded_artifacts)
        upload_duration = time.time() - upload_start
        record_evidence_creation(
            service="labyrinth",
            har_entries=len(self.har_entries),
            payload_count=len(self.payloads),
            package_size=total_bytes,
            upload_duration=upload_duration
        )
        for payload in self.payloads:
            payloads_extracted.labels(
                service="labyrinth",
                payload_type=payload.payload_type
            ).inc()
        
        # Cleanup workspace
        shutil.rmtree(self.workspace, ignore_errors=True)
        
        return pointer
