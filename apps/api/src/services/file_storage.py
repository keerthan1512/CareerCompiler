"""
File Storage Service
Abstracts local filesystem storage. Interface designed to be swapped for S3.

Storage layout:
  uploads/
    {user_id}/
      {resume_id}/
        main.pdf          ← primary PDF file
"""

from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path

import aiofiles

from ..config import get_settings

settings = get_settings()


class FileStorageError(Exception):
    pass


class FileStorage:
    """Local filesystem implementation. Swap this class for an S3 implementation later."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or settings.upload_path
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resume_dir(self, user_id: str, resume_id: str) -> Path:
        return self.base_dir / user_id / resume_id

    def _assets_dir(self, user_id: str, resume_id: str) -> Path:
        return self._resume_dir(user_id, resume_id) / "assets"

    async def save_pdf(
        self, user_id: str, resume_id: str, content: bytes, filename: str = "main.pdf"
    ) -> tuple[str, str]:
        """
        Save the primary .pdf file.

        Returns:
            (relative_path, sha256_checksum)
        """
        resume_dir = self._resume_dir(user_id, resume_id)
        resume_dir.mkdir(parents=True, exist_ok=True)

        target = resume_dir / filename
        async with aiofiles.open(target, "wb") as f:
            await f.write(content)

        checksum = hashlib.sha256(content).hexdigest()
        relative_path = str(target.relative_to(self.base_dir))
        return relative_path, checksum

    async def read_pdf(self, user_id: str, resume_id: str, filename: str = "main.pdf") -> bytes:
        """Read the primary .pdf file content."""
        target = self._resume_dir(user_id, resume_id) / filename
        if not target.exists():
            raise FileStorageError(f"File not found: {target}")
        async with aiofiles.open(target, "rb") as f:
            return await f.read()

    def get_absolute_path(self, relative_path: str) -> Path:
        """Resolve a stored relative path to an absolute Path."""
        return self.base_dir / relative_path

    def delete_resume(self, user_id: str, resume_id: str) -> None:
        """Delete all files for a resume (used only for data erasure flows)."""
        resume_dir = self._resume_dir(user_id, resume_id)
        if resume_dir.exists():
            shutil.rmtree(resume_dir)


# ── Singleton ─────────────────────────────────────────────────────────────────

_storage: FileStorage | None = None


def get_file_storage() -> FileStorage:
    global _storage
    if _storage is None:
        _storage = FileStorage()
    return _storage
