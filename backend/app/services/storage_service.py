"""
Storage Service

Abstraction layer for file storage operations.
Supports local filesystem and AWS S3 backends.
"""

import os
import shutil
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO
from datetime import datetime, timedelta
import structlog

from fastapi import UploadFile, HTTPException
from app.config import settings

logger = structlog.get_logger()


class StorageService(ABC):
    """Abstract storage interface for file operations."""

    @abstractmethod
    async def upload_file(
        self, file: UploadFile, user_id: str, deck_id: str
    ) -> str:
        """
        Upload file and return storage path.

        Args:
            file: The uploaded file
            user_id: User ID for organizing files
            deck_id: Deck ID for organizing files

        Returns:
            Storage path (local path or S3 key)
        """
        pass

    @abstractmethod
    async def get_file(self, path: str) -> bytes:
        """
        Retrieve file contents.

        Args:
            path: Storage path

        Returns:
            File contents as bytes
        """
        pass

    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """
        Delete file from storage.

        Args:
            path: Storage path

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_file_url(self, path: str, expiration: int = 3600) -> str:
        """
        Get temporary URL for file access.

        Args:
            path: Storage path
            expiration: URL expiration time in seconds

        Returns:
            URL for file access
        """
        pass

    @abstractmethod
    async def file_exists(self, path: str) -> bool:
        """
        Check if file exists.

        Args:
            path: Storage path

        Returns:
            True if file exists, False otherwise
        """
        pass


class LocalStorageService(StorageService):
    """Local filesystem storage implementation."""

    def __init__(self, base_path: str | None = None):
        """
        Initialize local storage service.

        Args:
            base_path: Base directory for file storage
        """
        self.base_path = Path(base_path or settings.storage_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info("local_storage_initialized", base_path=str(self.base_path))

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other security issues.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        # Remove path separators and other dangerous characters
        filename = os.path.basename(filename)
        filename = re.sub(r'[^\w\s.-]', '', filename)
        filename = filename.replace('..', '')

        # Add timestamp to avoid collisions
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        return f"{timestamp}_{name}{ext}"

    def _get_full_path(self, path: str) -> Path:
        """
        Get full filesystem path from storage path.

        Args:
            path: Relative storage path

        Returns:
            Full filesystem path
        """
        full_path = self.base_path / path
        # Ensure the path is within base_path (prevent path traversal)
        if not str(full_path.resolve()).startswith(str(self.base_path.resolve())):
            raise HTTPException(
                status_code=400, detail="Invalid file path"
            )
        return full_path

    async def upload_file(
        self, file: UploadFile, user_id: str, deck_id: str
    ) -> str:
        """Upload file to local filesystem."""
        try:
            # Create directory structure: {base_path}/{user_id}/{deck_id}/
            user_dir = self.base_path / user_id / deck_id
            user_dir.mkdir(parents=True, exist_ok=True)

            # Sanitize filename
            safe_filename = self._sanitize_filename(file.filename or "unnamed_file")

            # Full file path
            file_path = user_dir / safe_filename
            storage_path = f"{user_id}/{deck_id}/{safe_filename}"

            # Write file to disk
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            logger.info(
                "file_uploaded_local",
                user_id=user_id,
                deck_id=deck_id,
                filename=safe_filename,
                path=storage_path,
                size=file_path.stat().st_size
            )

            return storage_path

        except Exception as e:
            logger.error(
                "file_upload_failed",
                user_id=user_id,
                deck_id=deck_id,
                filename=file.filename,
                error=str(e)
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to upload file: {str(e)}"
            )

    async def get_file(self, path: str) -> bytes:
        """Retrieve file from local filesystem."""
        try:
            full_path = self._get_full_path(path)

            if not full_path.exists():
                raise HTTPException(status_code=404, detail="File not found")

            with open(full_path, "rb") as f:
                return f.read()

        except HTTPException:
            raise
        except Exception as e:
            logger.error("file_retrieval_failed", path=path, error=str(e))
            raise HTTPException(
                status_code=500, detail=f"Failed to retrieve file: {str(e)}"
            )

    async def delete_file(self, path: str) -> bool:
        """Delete file from local filesystem."""
        try:
            full_path = self._get_full_path(path)

            if full_path.exists():
                full_path.unlink()
                logger.info("file_deleted", path=path)
                return True

            return False

        except Exception as e:
            logger.error("file_deletion_failed", path=path, error=str(e))
            return False

    async def get_file_url(self, path: str, expiration: int = 3600) -> str:
        """
        Get file URL for local storage.
        Note: For local storage, this returns a path. In production with a web server,
        this could return a temporary URL endpoint.
        """
        full_path = self._get_full_path(path)
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        return str(full_path)

    async def file_exists(self, path: str) -> bool:
        """Check if file exists in local filesystem."""
        try:
            full_path = self._get_full_path(path)
            return full_path.exists()
        except Exception:
            return False


class S3StorageService(StorageService):
    """AWS S3 storage implementation."""

    def __init__(self, bucket_name: str | None = None):
        """
        Initialize S3 storage service.

        Args:
            bucket_name: S3 bucket name
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
            self.ClientError = ClientError
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 storage. Install with: pip install boto3"
            )

        self.bucket_name = bucket_name or settings.s3_bucket
        if not self.bucket_name:
            raise ValueError("S3 bucket name is required")

        self.s3_client = boto3.client("s3", region_name=settings.s3_region)
        logger.info(
            "s3_storage_initialized",
            bucket=self.bucket_name,
            region=settings.s3_region
        )

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for S3 key."""
        filename = os.path.basename(filename)
        filename = re.sub(r'[^\w\s.-]', '', filename)
        filename = filename.replace('..', '')

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(filename)
        return f"{timestamp}_{name}{ext}"

    def _get_s3_key(self, user_id: str, deck_id: str, filename: str) -> str:
        """
        Generate S3 key with environment prefix.

        Args:
            user_id: User ID
            deck_id: Deck ID
            filename: Sanitized filename

        Returns:
            S3 key
        """
        env = settings.env
        return f"{env}/{user_id}/{deck_id}/{filename}"

    async def upload_file(
        self, file: UploadFile, user_id: str, deck_id: str
    ) -> str:
        """Upload file to S3."""
        try:
            # Sanitize filename
            safe_filename = self._sanitize_filename(file.filename or "unnamed_file")

            # Generate S3 key
            s3_key = self._get_s3_key(user_id, deck_id, safe_filename)

            # Reset file pointer
            await file.seek(0)

            # Upload to S3 with server-side encryption
            self.s3_client.upload_fileobj(
                file.file,
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    "ServerSideEncryption": "AES256",
                    "ContentType": file.content_type or "application/octet-stream",
                    "Metadata": {
                        "user_id": user_id,
                        "deck_id": deck_id,
                        "original_filename": file.filename or "unnamed_file"
                    }
                }
            )

            logger.info(
                "file_uploaded_s3",
                user_id=user_id,
                deck_id=deck_id,
                filename=safe_filename,
                s3_key=s3_key,
                bucket=self.bucket_name
            )

            return s3_key

        except self.ClientError as e:
            logger.error(
                "s3_upload_failed",
                user_id=user_id,
                deck_id=deck_id,
                filename=file.filename,
                error=str(e)
            )
            raise HTTPException(
                status_code=500, detail=f"Failed to upload file to S3: {str(e)}"
            )

    async def get_file(self, path: str) -> bytes:
        """Retrieve file from S3."""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=path)
            return response["Body"].read()

        except self.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise HTTPException(status_code=404, detail="File not found")
            logger.error("s3_retrieval_failed", path=path, error=str(e))
            raise HTTPException(
                status_code=500, detail=f"Failed to retrieve file from S3: {str(e)}"
            )

    async def delete_file(self, path: str) -> bool:
        """Delete file from S3."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=path)
            logger.info("file_deleted_s3", path=path, bucket=self.bucket_name)
            return True

        except self.ClientError as e:
            logger.error("s3_deletion_failed", path=path, error=str(e))
            return False

    async def get_file_url(self, path: str, expiration: int = 3600) -> str:
        """Generate presigned URL for S3 object."""
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": path},
                ExpiresIn=expiration
            )
            return url

        except self.ClientError as e:
            logger.error("s3_presigned_url_failed", path=path, error=str(e))
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate presigned URL: {str(e)}"
            )

    async def file_exists(self, path: str) -> bool:
        """Check if file exists in S3."""
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=path)
            return True
        except self.ClientError:
            return False


def get_storage_service() -> StorageService:
    """
    Factory function to get storage service based on configuration.

    Returns:
        StorageService instance (Local or S3)
    """
    if settings.storage_backend == "s3":
        return S3StorageService()
    else:
        return LocalStorageService()
