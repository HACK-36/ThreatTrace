"""
Evidence Package Models for Cerberus Digital Evidence Locker
Defines structured formats for forensic evidence collection
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import uuid4


class HARLogEntry(BaseModel):
    """HTTP Archive (HAR) log entry for a single request/response pair"""
    startedDateTime: str
    time: float  # milliseconds
    request: Dict[str, Any]
    response: Dict[str, Any]
    cache: Dict[str, Any] = {}
    timings: Dict[str, float] = {}
    serverIPAddress: Optional[str] = None
    connection: Optional[str] = None


class HARLog(BaseModel):
    """HAR format log of session HTTP traffic"""
    version: str = "1.2"
    creator: Dict[str, str] = {"name": "Cerberus Labyrinth", "version": "1.0"}
    pages: List[Dict[str, Any]] = []
    entries: List[HARLogEntry] = []


class PayloadArtifact(BaseModel):
    """Individual malicious payload captured"""
    artifact_id: str = Field(default_factory=lambda: f"payload_{uuid4().hex[:8]}")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    payload_type: str  # sql_injection, xss, command_injection, file_upload, etc.
    payload_value: str  # The actual malicious content
    location: str  # Where it was found (query.id, body.username, etc.)
    encoding: str = "utf-8"  # Encoding used
    confidence: float  # Detection confidence (0-1)
    file_path: Optional[str] = None  # Path in evidence package if saved as file
    checksum: Optional[str] = None  # SHA256 of payload


class SessionMetadata(BaseModel):
    """Metadata about the attacker session"""
    session_id: str
    attacker_ip: str
    user_agent: str
    fingerprint: str  # Browser/client fingerprint
    session_start: str
    session_end: str
    request_count: int
    total_duration_ms: int
    geoip: Optional[Dict[str, Any]] = None
    tags: List[str] = []
    risk_score: float = 0.0


class TTPs(BaseModel):
    """MITRE ATT&CK TTPs observed"""
    techniques: List[str] = []  # T1190, T1059, etc.
    tactics: List[str] = []  # Initial Access, Execution, etc.
    description: str = ""


class BehaviorProfile(BaseModel):
    """Behavioral analysis of attacker"""
    intent: str  # reconnaissance, exploitation, data_exfiltration
    sophistication_score: float  # 0-10
    ttps: TTPs
    action_sequence: List[str] = []  # Timeline of actions
    automation_detected: bool = False
    tool_signatures: List[str] = []  # sqlmap, nikto, etc.


class EvidenceMetadata(BaseModel):
    """Metadata for the complete evidence package"""
    event_id: str
    capture_id: str = Field(default_factory=lambda: f"cap_{uuid4().hex[:8]}")
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    created_by: str = "labyrinth"
    session_metadata: SessionMetadata
    behavior_profile: Optional[BehaviorProfile] = None
    artifacts_manifest: List[Dict[str, str]] = []  # List of files in package with checksums
    package_checksum: Optional[str] = None  # SHA256 of entire package
    storage_location: str  # s3://bucket/path
    retention_until: Optional[str] = None
    tags: List[str] = []
    notes: str = ""


class EvidencePackage(BaseModel):
    """
    Complete digital evidence package for a captured attack session
    
    This represents the "Digital Evidence Bag" stored in MinIO
    """
    metadata: EvidenceMetadata
    har_log: HARLog
    payloads: List[PayloadArtifact]
    uploaded_files: List[Dict[str, str]] = []  # Metadata about uploaded malicious files
    
    def to_manifest(self) -> Dict[str, Any]:
        """Generate manifest of evidence package contents"""
        return {
            "event_id": self.metadata.event_id,
            "capture_id": self.metadata.capture_id,
            "created_at": self.metadata.created_at,
            "session_id": self.metadata.session_metadata.session_id,
            "attacker_ip": self.metadata.session_metadata.attacker_ip,
            "artifacts": {
                "har_log": "session.har",
                "payloads": [p.artifact_id for p in self.payloads],
                "metadata": "metadata.json",
                "behavior": "behavior.json" if self.metadata.behavior_profile else None
            },
            "total_payloads": len(self.payloads),
            "total_requests": len(self.har_log.entries),
            "storage_location": self.metadata.storage_location
        }


class EvidencePointer(BaseModel):
    """
    Lightweight pointer to evidence package (published to message bus)
    
    This is what gets sent via Kafka/Redis instead of the full evidence
    """
    status: str = "evidence_ready"
    event_id: str
    capture_id: str
    session_id: str
    attacker_ip: str
    location: str  # s3://bucket/event_id/
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    payload_count: int
    request_count: int
    checksum: Optional[str] = None  # Package checksum for validation
    tags: List[str] = []


# Sample evidence package for testing
SAMPLE_EVIDENCE_PACKAGE = EvidencePackage(
    metadata=EvidenceMetadata(
        event_id="evt_demo_001",
        session_metadata=SessionMetadata(
            session_id="sess_demo_001",
            attacker_ip="203.0.113.42",
            user_agent="sqlmap/1.5.2",
            fingerprint="abc123def456",
            session_start="2024-01-01T10:00:00Z",
            session_end="2024-01-01T10:15:30Z",
            request_count=25,
            total_duration_ms=930000,
            tags=["sql_injection", "automated_tool"]
        ),
        behavior_profile=BehaviorProfile(
            intent="exploitation",
            sophistication_score=6.5,
            ttps=TTPs(
                techniques=["T1190", "T1059"],
                tactics=["Initial Access", "Execution"]
            ),
            action_sequence=[
                "probe_admin_endpoint",
                "sql_injection_attempt",
                "union_select_payload",
                "file_disclosure_attempt"
            ],
            automation_detected=True,
            tool_signatures=["sqlmap"]
        ),
        storage_location="s3://labyrinth-evidence/evt_demo_001/",
        tags=["high_severity", "confirmed_exploit"]
    ),
    har_log=HARLog(
        entries=[
            HARLogEntry(
                startedDateTime="2024-01-01T10:00:00Z",
                time=245.5,
                request={
                    "method": "GET",
                    "url": "/api/users?id=1' OR '1'='1",
                    "httpVersion": "HTTP/1.1",
                    "headers": [{"name": "User-Agent", "value": "sqlmap/1.5.2"}],
                    "queryString": [{"name": "id", "value": "1' OR '1'='1"}]
                },
                response={
                    "status": 200,
                    "statusText": "OK",
                    "httpVersion": "HTTP/1.1",
                    "headers": [{"name": "Content-Type", "value": "application/json"}],
                    "content": {"size": 1024, "mimeType": "application/json"}
                },
                timings={"send": 10.2, "wait": 230.1, "receive": 5.2}
            )
        ]
    ),
    payloads=[
        PayloadArtifact(
            payload_type="sql_injection",
            payload_value="1' OR '1'='1",
            location="query.id",
            confidence=0.95,
            checksum="abc123..."
        )
    ]
)
