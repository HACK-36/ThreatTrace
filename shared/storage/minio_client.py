"""
MinIO Client for Cerberus Evidence Storage
Provides unified S3-compatible storage interface
"""
import os
import io
import json
import hashlib
from typing import Optional, Dict, List, BinaryIO
from datetime import datetime, timedelta
from minio import Minio
from minio.error import S3Error
import logging

logger = logging.getLogger(__name__)


class CerberusStorageClient:
    """
    Unified storage client for Cerberus evidence and artifacts
    
    Features:
    - Evidence package upload/download
    - Metadata management
    - Checksum validation
    - Bucket lifecycle management
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        secure: bool = False
    ):
        """
        Initialize MinIO client
        
        Args:
            endpoint: MinIO endpoint (default from env MINIO_ENDPOINT)
            access_key: Access key (default from env MINIO_ACCESS_KEY)
            secret_key: Secret key (default from env MINIO_SECRET_KEY)
            secure: Use HTTPS (default False for local dev)
        """
        self.endpoint = endpoint or os.getenv("MINIO_ENDPOINT", "minio:9000")
        self.access_key = access_key or os.getenv("MINIO_ACCESS_KEY", "cerberus")
        self.secret_key = secret_key or os.getenv("MINIO_SECRET_KEY", "cerberus_minio_password")
        self.secure = secure or os.getenv("MINIO_SECURE", "false").lower() == "true"
        
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            logger.info(f"MinIO client initialized: {self.endpoint}")
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            raise
    
    def ensure_bucket(self, bucket_name: str, retention_days: Optional[int] = None) -> bool:
        """
        Ensure bucket exists, create if not
        
        Args:
            bucket_name: Name of bucket
            retention_days: Optional retention policy in days
            
        Returns:
            True if bucket exists/created
        """
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
                
                # Set retention policy if specified
                if retention_days:
                    # Note: MinIO lifecycle policy would go here
                    # For now, just log
                    logger.info(f"Retention policy: {retention_days} days for {bucket_name}")
            
            return True
        except S3Error as e:
            logger.error(f"Failed to ensure bucket {bucket_name}: {e}")
            return False
    
    def upload_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Upload file to MinIO
        
        Args:
            bucket_name: Target bucket
            object_name: Object path in bucket
            file_path: Local file path
            metadata: Optional metadata dict
            
        Returns:
            Dict with upload info (etag, size, checksum)
        """
        try:
            # Calculate checksum
            with open(file_path, 'rb') as f:
                file_data = f.read()
                checksum = hashlib.sha256(file_data).hexdigest()
            
            # Upload
            result = self.client.fput_object(
                bucket_name,
                object_name,
                file_path,
                metadata=metadata or {}
            )
            
            file_size = os.path.getsize(file_path)
            
            logger.info(f"Uploaded {object_name} to {bucket_name} ({file_size} bytes)")
            
            return {
                "bucket": bucket_name,
                "object": object_name,
                "etag": result.etag,
                "size": file_size,
                "checksum": checksum,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to upload {file_path} to {bucket_name}/{object_name}: {e}")
            raise
    
    def upload_bytes(
        self,
        bucket_name: str,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Upload bytes directly to MinIO
        
        Args:
            bucket_name: Target bucket
            object_name: Object path
            data: Bytes to upload
            content_type: MIME type
            metadata: Optional metadata
            
        Returns:
            Dict with upload info
        """
        try:
            checksum = hashlib.sha256(data).hexdigest()
            data_stream = io.BytesIO(data)
            
            result = self.client.put_object(
                bucket_name,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type,
                metadata=metadata or {}
            )
            
            logger.info(f"Uploaded {len(data)} bytes to {bucket_name}/{object_name}")
            
            return {
                "bucket": bucket_name,
                "object": object_name,
                "etag": result.etag,
                "size": len(data),
                "checksum": checksum,
                "uploaded_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to upload bytes to {bucket_name}/{object_name}: {e}")
            raise
    
    def download_file(
        self,
        bucket_name: str,
        object_name: str,
        file_path: str,
        validate_checksum: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Download file from MinIO
        
        Args:
            bucket_name: Source bucket
            object_name: Object path
            file_path: Destination file path
            validate_checksum: Optional SHA256 to validate against
            
        Returns:
            Dict with download info
        """
        try:
            self.client.fget_object(bucket_name, object_name, file_path)
            
            # Validate checksum if provided
            if validate_checksum:
                with open(file_path, 'rb') as f:
                    actual_checksum = hashlib.sha256(f.read()).hexdigest()
                    
                if actual_checksum != validate_checksum:
                    raise ValueError(f"Checksum mismatch: expected {validate_checksum}, got {actual_checksum}")
            
            file_size = os.path.getsize(file_path)
            
            logger.info(f"Downloaded {bucket_name}/{object_name} to {file_path} ({file_size} bytes)")
            
            return {
                "bucket": bucket_name,
                "object": object_name,
                "local_path": file_path,
                "size": file_size,
                "downloaded_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to download {bucket_name}/{object_name}: {e}")
            raise
    
    def download_bytes(
        self,
        bucket_name: str,
        object_name: str
    ) -> bytes:
        """
        Download object as bytes
        
        Args:
            bucket_name: Source bucket
            object_name: Object path
            
        Returns:
            Object data as bytes
        """
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"Downloaded {len(data)} bytes from {bucket_name}/{object_name}")
            return data
        except Exception as e:
            logger.error(f"Failed to download bytes from {bucket_name}/{object_name}: {e}")
            raise
    
    def list_objects(
        self,
        bucket_name: str,
        prefix: Optional[str] = None,
        recursive: bool = False
    ) -> List[Dict[str, any]]:
        """
        List objects in bucket
        
        Args:
            bucket_name: Bucket to list
            prefix: Optional prefix filter
            recursive: List recursively
            
        Returns:
            List of object info dicts
        """
        try:
            objects = self.client.list_objects(
                bucket_name,
                prefix=prefix,
                recursive=recursive
            )
            
            result = []
            for obj in objects:
                result.append({
                    "name": obj.object_name,
                    "size": obj.size,
                    "last_modified": obj.last_modified.isoformat() if obj.last_modified else None,
                    "etag": obj.etag
                })
            
            logger.info(f"Listed {len(result)} objects from {bucket_name} (prefix={prefix})")
            return result
        except Exception as e:
            logger.error(f"Failed to list objects from {bucket_name}: {e}")
            raise
    
    def delete_object(self, bucket_name: str, object_name: str) -> bool:
        """
        Delete object from bucket
        
        Args:
            bucket_name: Source bucket
            object_name: Object to delete
            
        Returns:
            True if deleted
        """
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"Deleted {bucket_name}/{object_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {bucket_name}/{object_name}: {e}")
            return False
    
    def get_presigned_url(
        self,
        bucket_name: str,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Generate presigned URL for object access
        
        Args:
            bucket_name: Bucket containing object
            object_name: Object path
            expires: URL expiry duration
            
        Returns:
            Presigned URL string
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name,
                object_name,
                expires=expires
            )
            logger.info(f"Generated presigned URL for {bucket_name}/{object_name} (expires in {expires})")
            return url
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise


# Singleton instance
_storage_client: Optional[CerberusStorageClient] = None


def get_storage_client() -> CerberusStorageClient:
    """Get singleton storage client instance"""
    global _storage_client
    if _storage_client is None:
        _storage_client = CerberusStorageClient()
    return _storage_client
