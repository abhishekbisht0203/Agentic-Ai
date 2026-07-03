"""S3/MinIO storage service."""

import uuid
from typing import BinaryIO

from minio import Minio

from app.core.config import settings


class S3Storage:
    """S3-compatible storage using MinIO."""

    def __init__(self) -> None:
        self._client: Minio | None = None

    def get_client(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                settings.minio.endpoint,
                access_key=settings.minio.access_key,
                secret_key=settings.minio.secret_key,
                secure=settings.minio.secure,
            )
        return self._client

    def _ensure_bucket(self) -> None:
        client = self.get_client()
        if not client.bucket_exists(settings.minio.bucket_name):
            client.make_bucket(settings.minio.bucket_name)

    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
        folder: str = "uploads",
    ) -> str:
        client = self.get_client()
        self._ensure_bucket()
        object_name = f"{folder}/{uuid.uuid4()}/{filename}"
        data = file_data.read()
        client.put_object(
            settings.minio.bucket_name,
            object_name,
            data,
            length=len(data),
            content_type=content_type,
        )
        return object_name

    async def download_file(self, object_name: str) -> bytes:
        client = self.get_client()
        response = client.get_object(settings.minio.bucket_name, object_name)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def delete_file(self, object_name: str) -> bool:
        client = self.get_client()
        try:
            client.remove_object(settings.minio.bucket_name, object_name)
            return True
        except Exception:
            return False

    async def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        client = self.get_client()
        return client.presigned_get_object(
            settings.minio.bucket_name,
            object_name,
            expires=expires,
        )
