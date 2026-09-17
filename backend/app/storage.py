"""Private filesystem storage for imported attachment bytes."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from uuid import uuid4

from app.config import get_settings


class StorageError(ValueError):
    """Raised when an attachment storage operation is invalid."""


def storage_root() -> Path:
    root = Path(get_settings().storage_path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def safe_storage_path(storage_key: str) -> Path:
    if not storage_key or "\x00" in storage_key:
        raise StorageError("Invalid storage key")
    key_path = Path(storage_key)
    if key_path.is_absolute() or any(part in {"", ".", ".."} for part in key_path.parts):
        raise StorageError("Invalid storage key")
    root = storage_root()
    path = (root / key_path).resolve()
    if path == root or root not in path.parents:
        raise StorageError("Invalid storage key")
    return path


def _safe_filename(filename: str | None) -> str:
    name = Path(filename or "attachment").name.replace("\x00", "").strip()
    return name[:255] or "attachment"


def write_attachment(data: bytes, filename: str | None = None) -> tuple[str, str]:
    """Write bytes atomically and return a private key plus SHA-256 digest."""
    root = storage_root()
    suffix = Path(_safe_filename(filename)).suffix.lower()
    if len(suffix) > 16 or not suffix.replace(".", "").isalnum():
        suffix = ".bin"
    storage_key = f"{uuid4().hex}{suffix}"
    target = safe_storage_path(storage_key)
    temp = root / f".{uuid4().hex}.tmp"
    digest = hashlib.sha256(data).hexdigest()
    try:
        temp.write_bytes(data)
        os.chmod(temp, 0o600)
        os.replace(temp, target)
    except OSError as exc:
        temp.unlink(missing_ok=True)
        raise StorageError("Unable to store attachment") from exc
    return storage_key, digest


def read_attachment(storage_key: str) -> Path:
    path = safe_storage_path(storage_key)
    if not path.is_file():
        raise StorageError("Attachment file not found")
    return path


def remove_attachment(storage_key: str) -> None:
    try:
        safe_storage_path(storage_key).unlink(missing_ok=True)
    except (OSError, StorageError):
        return


def verify_attachment(storage_key: str, expected_hash: str) -> bool:
    path = read_attachment(storage_key)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest == expected_hash
