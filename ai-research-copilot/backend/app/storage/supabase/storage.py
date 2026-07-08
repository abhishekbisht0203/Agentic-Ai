"""Supabase Storage service."""

import uuid
from typing import BinaryIO

from supabase import create_client

from app.core.config import settings


class SupabaseStorage:
    """File storage using Supabase Storage."""

    def __init__(self) -> None:
        self._client = None
        self._bucket = settings.supabase.storage_bucket

    def get_client(self):
        if self._client is None:
            self._client = create_client(
                settings.supabase.url,
                settings.supabase.key,
            )
        return self._client

    def _get_storage(self):
        return self.get_client().storage

    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
        folder: str = "uploads",
    ) -> str:
        storage = self._get_storage()
        object_name = f"{folder}/{uuid.uuid4()}/{filename}"
        data = file_data.read()
        storage.from_(self._bucket).upload(
            path=object_name,
            file=data,
            file_options={"content-type": content_type},
        )
        return object_name

    async def download_file(self, file_path: str) -> bytes:
        storage = self._get_storage()
        return storage.from_(self._bucket).download(file_path)

    async def delete_file(self, file_path: str) -> bool:
        storage = self._get_storage()
        try:
            storage.from_(self._bucket).remove([file_path])
            return True
        except Exception:
            return False

    async def get_presigned_url(self, object_name: str, expires: int = 3600) -> str:
        storage = self._get_storage()
        return storage.from_(self._bucket).create_signed_url(
            path=object_name,
            expires_in=expires,
        )
