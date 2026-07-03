"""Local filesystem storage service."""

import uuid
from pathlib import Path
from typing import BinaryIO

from app.core.config import settings


class LocalStorage:
    """Local filesystem storage for development and small deployments."""

    def __init__(self, base_path: str = "./uploads") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload_file(
        self,
        file_data: BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
        folder: str = "uploads",
    ) -> str:
        file_dir = self.base_path / folder / str(uuid.uuid4())
        file_dir.mkdir(parents=True, exist_ok=True)
        file_path = file_dir / filename
        data = file_data.read()
        file_path.write_bytes(data)
        return str(file_path.relative_to(self.base_path))

    async def download_file(self, file_path: str) -> bytes:
        full_path = self.base_path / file_path
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return full_path.read_bytes()

    async def delete_file(self, file_path: str) -> bool:
        full_path = self.base_path / file_path
        if full_path.exists():
            full_path.unlink()
            return True
        return False

    async def get_file_url(self, file_path: str) -> str:
        full_path = self.base_path / file_path
        return full_path.as_uri()
