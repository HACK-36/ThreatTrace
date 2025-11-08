"""
Evidence Retriever for Sentinel
Downloads and validates evidence packages from MinIO
"""
import os
import json
import hashlib
import tempfile
import shutil
from typing import Dict, List, Optional
from pathlib import Path

from shared.evidence.models import (
    EvidencePackage, EvidenceMetadata, HARLog,
    PayloadArtifact, EvidencePointer
)
from shared.storage.minio_client import get_storage_client
import logging

logger = logging.getLogger(__name__)


class EvidenceRetriever:
    """
    Retrieves and validates evidence packages from MinIO storage
    
    Workflow:
    1. Receive evidence pointer from message bus
    2. Download artifacts from MinIO to temporary workspace
    3. Validate checksums
    4. Parse and return structured evidence
    5. Cleanup workspace
    """
    
    def __init__(self, workspace_root: Optional[str] = None):
        """
        Initialize evidence retriever
        
        Args:
            workspace_root: Root directory for evidence workspaces (default: /tmp)
        """
        self.workspace_root = workspace_root or "/tmp/sentinel/evidence"
        os.makedirs(self.workspace_root, exist_ok=True)
        self.storage = get_storage_client()
    
    def retrieve(self, pointer: EvidencePointer) -> Dict[str, any]:
        """
        Retrieve complete evidence package from pointer
        
        Args:
            pointer: Evidence pointer with location and metadata
            
        Returns:
            Dict containing parsed evidence and workspace path
            {
                "metadata": EvidenceMetadata,
                "har_log": HARLog,
                "payloads": List[PayloadArtifact],
                "workspace": str (path to downloaded files),
                "valid": bool (checksum validation result)
            }
        """
        event_id = pointer.event_id
        logger.info(f"Retrieving evidence for event {event_id}")
        
        # Create workspace for this evidence package
        workspace = os.path.join(self.workspace_root, event_id)
        os.makedirs(workspace, exist_ok=True)
        
        try:
            # Parse S3 location
            # Format: s3://bucket/event_id/
            location_parts = pointer.location.replace("s3://", "").split("/", 1)
            bucket_name = location_parts[0]
            prefix = location_parts[1] if len(location_parts) > 1 else ""
            
            # List all objects in evidence folder
            objects = self.storage.list_objects(
                bucket_name,
                prefix=prefix,
                recursive=True
            )
            
            logger.info(f"Found {len(objects)} artifacts for {event_id}")
            
            # Download all artifacts
            downloaded_checksums = []
            for obj in objects:
                object_name = obj["name"]
                local_filename = object_name.replace(f"{event_id}/", "")
                local_path = os.path.join(workspace, local_filename)
                
                # Create subdirectories if needed
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # Download
                self.storage.download_file(bucket_name, object_name, local_path)
                
                # Track checksum
                with open(local_path, 'rb') as f:
                    checksum = hashlib.sha256(f.read()).hexdigest()
                    downloaded_checksums.append(checksum)
            
            # Validate package checksum if provided
            valid = True
            if pointer.checksum:
                calculated_checksum = hashlib.sha256(
                    "".join(downloaded_checksums).encode()
                ).hexdigest()
                
                if calculated_checksum != pointer.checksum:
                    logger.warning(f"Checksum mismatch for {event_id}: expected {pointer.checksum}, got {calculated_checksum}")
                    valid = False
                else:
                    logger.info(f"Checksum validated for {event_id}")
            
            # Parse artifacts
            metadata_path = os.path.join(workspace, "metadata.json")
            har_path = os.path.join(workspace, "session.har")
            
            metadata = None
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    metadata = EvidenceMetadata.model_validate_json(f.read())
            
            har_log = None
            if os.path.exists(har_path):
                with open(har_path, 'r') as f:
                    har_data = json.load(f)
                    har_log = HARLog.model_validate(har_data)
            
            # Extract payloads from metadata
            payloads = []
            if metadata and metadata.session_metadata:
                # Payloads are in metadata, not separate files for now
                # Could be extended to read from payloads/ directory
                pass
            
            return {
                "event_id": event_id,
                "metadata": metadata,
                "har_log": har_log,
                "payloads": payloads,
                "workspace": workspace,
                "valid": valid,
                "artifact_count": len(objects)
            }
        
        except Exception as e:
            logger.error(f"Failed to retrieve evidence for {event_id}: {e}")
            # Cleanup on error
            shutil.rmtree(workspace, ignore_errors=True)
            raise
    
    def get_har_log(self, workspace: str) -> Optional[HARLog]:
        """
        Load HAR log from workspace
        
        Args:
            workspace: Evidence workspace path
            
        Returns:
            Parsed HAR log or None
        """
        har_path = os.path.join(workspace, "session.har")
        if not os.path.exists(har_path):
            return None
        
        with open(har_path, 'r') as f:
            har_data = json.load(f)
            return HARLog.model_validate(har_data)
    
    def get_metadata(self, workspace: str) -> Optional[EvidenceMetadata]:
        """
        Load metadata from workspace
        
        Args:
            workspace: Evidence workspace path
            
        Returns:
            Evidence metadata or None
        """
        metadata_path = os.path.join(workspace, "metadata.json")
        if not os.path.exists(metadata_path):
            return None
        
        with open(metadata_path, 'r') as f:
            return EvidenceMetadata.model_validate_json(f.read())
    
    def get_payload_files(self, workspace: str) -> List[str]:
        """
        Get list of payload files in workspace
        
        Args:
            workspace: Evidence workspace path
            
        Returns:
            List of payload file paths
        """
        payloads_dir = os.path.join(workspace, "payloads")
        if not os.path.exists(payloads_dir):
            return []
        
        return [
            os.path.join(payloads_dir, f)
            for f in os.listdir(payloads_dir)
            if os.path.isfile(os.path.join(payloads_dir, f))
        ]
    
    def cleanup(self, workspace: str):
        """
        Cleanup evidence workspace
        
        Args:
            workspace: Evidence workspace path to delete
        """
        try:
            shutil.rmtree(workspace, ignore_errors=True)
            logger.info(f"Cleaned up evidence workspace: {workspace}")
        except Exception as e:
            logger.warning(f"Failed to cleanup workspace {workspace}: {e}")
    
    def cleanup_all(self, max_age_hours: int = 24):
        """
        Cleanup old evidence workspaces
        
        Args:
            max_age_hours: Maximum age in hours before cleanup
        """
        import time
        current_time = time.time()
        
        for workspace_name in os.listdir(self.workspace_root):
            workspace_path = os.path.join(self.workspace_root, workspace_name)
            if not os.path.isdir(workspace_path):
                continue
            
            # Check age
            workspace_age_hours = (current_time - os.path.getmtime(workspace_path)) / 3600
            if workspace_age_hours > max_age_hours:
                logger.info(f"Cleaning up old workspace: {workspace_name} (age: {workspace_age_hours:.1f}h)")
                shutil.rmtree(workspace_path, ignore_errors=True)
