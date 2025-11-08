"""
Prometheus Metrics for Cerberus
Standardized metrics collection across all services
"""
from prometheus_client import Counter, Histogram, Gauge, Summary
from typing import Dict, Optional
import time
from functools import wraps


# ============================================================================
# REQUEST METRICS
# ============================================================================

# Request counters
requests_total = Counter(
    'cerberus_requests_total',
    'Total requests processed',
    ['service', 'endpoint', 'method', 'status']
)

requests_in_progress = Gauge(
    'cerberus_requests_in_progress',
    'Requests currently being processed',
    ['service', 'endpoint']
)

# Request duration histogram
request_duration_seconds = Histogram(
    'cerberus_request_duration_seconds',
    'Request duration in seconds',
    ['service', 'endpoint', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# ============================================================================
# GATEKEEPER METRICS
# ============================================================================

# Detection metrics
threats_detected = Counter(
    'cerberus_threats_detected_total',
    'Total threats detected',
    ['service', 'threat_type', 'action']
)

ml_predictions = Counter(
    'cerberus_ml_predictions_total',
    'ML model predictions',
    ['service', 'model', 'prediction']
)

ml_score = Histogram(
    'cerberus_ml_score',
    'ML anomaly scores',
    ['service', 'model'],
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

waf_rules_applied = Counter(
    'cerberus_waf_rules_applied_total',
    'WAF rules applied',
    ['service', 'rule_id', 'action']
)

sessions_tracked = Gauge(
    'cerberus_active_sessions',
    'Number of active sessions',
    ['service']
)

# ============================================================================
# LABYRINTH METRICS
# ============================================================================

# Evidence collection
evidence_packages_created = Counter(
    'cerberus_evidence_packages_created_total',
    'Evidence packages created',
    ['service']
)

har_entries_captured = Counter(
    'cerberus_har_entries_captured_total',
    'HAR entries captured',
    ['service']
)

payloads_extracted = Counter(
    'cerberus_payloads_extracted_total',
    'Payloads extracted',
    ['service', 'payload_type']
)

evidence_upload_duration = Histogram(
    'cerberus_evidence_upload_duration_seconds',
    'Evidence upload duration',
    ['service'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
)

evidence_package_size = Histogram(
    'cerberus_evidence_package_size_bytes',
    'Evidence package size in bytes',
    ['service'],
    buckets=[1024, 10240, 102400, 1048576, 10485760, 104857600]
)

# ============================================================================
# SENTINEL METRICS
# ============================================================================

# Simulation metrics
simulations_total = Counter(
    'cerberus_simulations_total',
    'Total simulations executed',
    ['service', 'verdict']
)

simulation_duration = Histogram(
    'cerberus_simulation_duration_seconds',
    'Simulation duration',
    ['service', 'payload_type'],
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0]
)

rules_generated = Counter(
    'cerberus_rules_generated_total',
    'Rules generated',
    ['service', 'action', 'confidence_band']
)

rules_applied = Counter(
    'cerberus_rules_applied_total',
    'Rules applied to Gatekeeper',
    ['service', 'auto_applied']
)

attacker_profiles_created = Counter(
    'cerberus_attacker_profiles_created_total',
    'Attacker profiles created',
    ['service', 'intent', 'sophistication_band']
)

# Evidence consumption
evidence_pointers_consumed = Counter(
    'cerberus_evidence_pointers_consumed_total',
    'Evidence pointers consumed',
    ['service', 'status']
)

evidence_retrieval_duration = Histogram(
    'cerberus_evidence_retrieval_duration_seconds',
    'Evidence retrieval duration',
    ['service'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

# ============================================================================
# STORAGE METRICS
# ============================================================================

storage_operations = Counter(
    'cerberus_storage_operations_total',
    'Storage operations',
    ['service', 'operation', 'status']
)

storage_bytes_transferred = Counter(
    'cerberus_storage_bytes_transferred_total',
    'Bytes transferred to/from storage',
    ['service', 'direction']
)

# ============================================================================
# MESSAGING METRICS
# ============================================================================

messages_published = Counter(
    'cerberus_messages_published_total',
    'Messages published to event bus',
    ['service', 'topic', 'status']
)

messages_consumed = Counter(
    'cerberus_messages_consumed_total',
    'Messages consumed from event bus',
    ['service', 'topic', 'status']
)

message_processing_duration = Histogram(
    'cerberus_message_processing_duration_seconds',
    'Message processing duration',
    ['service', 'topic'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def track_request_metrics(service: str, endpoint: str, method: str):
    """
    Decorator to automatically track request metrics
    
    Usage:
        @track_request_metrics("gatekeeper", "/api/v1/inspect", "POST")
        async def inspect_request():
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Track in-progress
            requests_in_progress.labels(service=service, endpoint=endpoint).inc()
            
            # Track duration
            start_time = time.time()
            status = "success"
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                
                # Record metrics
                requests_total.labels(
                    service=service,
                    endpoint=endpoint,
                    method=method,
                    status=status
                ).inc()
                
                request_duration_seconds.labels(
                    service=service,
                    endpoint=endpoint,
                    method=method
                ).observe(duration)
                
                requests_in_progress.labels(service=service, endpoint=endpoint).dec()
        
        return wrapper
    return decorator


def record_threat_detection(
    service: str,
    threat_type: str,
    action: str,
    ml_score: Optional[float] = None
):
    """
    Record threat detection metrics
    
    Args:
        service: Service name
        threat_type: Type of threat (sql_injection, xss, etc.)
        action: Action taken (allow, block, tag_poi)
        ml_score: ML anomaly score (0-1)
    """
    threats_detected.labels(
        service=service,
        threat_type=threat_type,
        action=action
    ).inc()
    
    if ml_score is not None:
        ml_score.labels(service=service, model="anomaly_detector").observe(ml_score)


def record_evidence_creation(
    service: str,
    har_entries: int,
    payload_count: int,
    package_size: int,
    upload_duration: float
):
    """
    Record evidence package creation metrics
    
    Args:
        service: Service name
        har_entries: Number of HAR entries
        payload_count: Number of payloads
        package_size: Package size in bytes
        upload_duration: Upload duration in seconds
    """
    evidence_packages_created.labels(service=service).inc()
    har_entries_captured.labels(service=service).inc(har_entries)
    evidence_package_size.labels(service=service).observe(package_size)
    evidence_upload_duration.labels(service=service).observe(upload_duration)


def record_simulation(
    service: str,
    payload_type: str,
    verdict: str,
    duration: float
):
    """
    Record simulation metrics
    
    Args:
        service: Service name
        payload_type: Type of payload
        verdict: Simulation verdict
        duration: Duration in seconds
    """
    simulations_total.labels(service=service, verdict=verdict).inc()
    simulation_duration.labels(service=service, payload_type=payload_type).observe(duration)


def record_rule_generation(
    service: str,
    action: str,
    confidence: float,
    auto_applied: bool
):
    """
    Record rule generation metrics
    
    Args:
        service: Service name
        action: Rule action (block, challenge, etc.)
        confidence: Rule confidence (0-1)
        auto_applied: Whether rule was auto-applied
    """
    # Confidence bands
    if confidence >= 0.9:
        band = "high"
    elif confidence >= 0.7:
        band = "medium"
    else:
        band = "low"
    
    rules_generated.labels(
        service=service,
        action=action,
        confidence_band=band
    ).inc()
    
    rules_applied.labels(
        service=service,
        auto_applied=str(auto_applied)
    ).inc()


def record_storage_operation(
    service: str,
    operation: str,
    status: str,
    bytes_transferred: Optional[int] = None,
    direction: Optional[str] = None
):
    """
    Record storage operation metrics
    
    Args:
        service: Service name
        operation: Operation type (upload, download, list, delete)
        status: Operation status (success, error)
        bytes_transferred: Bytes transferred (if applicable)
        direction: Direction (upload, download)
    """
    storage_operations.labels(
        service=service,
        operation=operation,
        status=status
    ).inc()
    
    if bytes_transferred and direction:
        storage_bytes_transferred.labels(
            service=service,
            direction=direction
        ).inc(bytes_transferred)


class MetricsContext:
    """
    Context manager for tracking operation metrics
    
    Usage:
        with MetricsContext("gatekeeper", "inspection"):
            # Do work
            pass
    """
    
    def __init__(self, service: str, operation: str):
        self.service = service
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        status = "success" if exc_type is None else "error"
        
        # Record metrics
        requests_total.labels(
            service=self.service,
            endpoint=self.operation,
            method="internal",
            status=status
        ).inc()
        
        return False  # Don't suppress exceptions
