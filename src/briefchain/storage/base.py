"""Object storage abstraction and metadata models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO, Protocol, runtime_checkable
from uuid import uuid4


@dataclass
class StoredObject:
    """Metadata describing an object stored in an object storage backend."""

    key: str
    filename: str
    content_type: str
    size: int
    url: str
    group: str = "default"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


def generate_key() -> str:
    """Generate a unique storage key."""
    return str(uuid4())


def validate_group(group: str) -> None:
    """Validate a group name to prevent path traversal.

    Raises:
        ValueError: If the group name contains path separators or parent references.
    """
    if not group:
        msg = "Group name cannot be empty"
        raise ValueError(msg)
    if group in (".", "..") or "/" in group or "\\" in group or ".." in group:
        msg = f"Invalid group name: {group}"
        raise ValueError(msg)


@runtime_checkable
class ObjectStorage(Protocol):
    """Storage-agnostic interface for saving, reading, and deleting objects."""

    def save(
        self,
        file: BinaryIO | bytes,
        filename: str,
        content_type: str,
        group: str | None = None,
    ) -> StoredObject:
        """Save an object and return its metadata."""
        ...

    def get(self, key: str, group: str | None = None) -> BinaryIO:
        """Return a readable stream for the object identified by ``key``."""
        ...

    def delete(self, key: str, group: str | None = None) -> None:
        """Delete the object identified by ``key``."""
        ...

    def get_url(self, key: str, group: str | None = None) -> str:
        """Return a URL that addresses the object identified by ``key``."""
        ...

    def list(self, group: str | None = None) -> list[StoredObject]:
        """List metadata for all objects in the given group."""
        ...


def _ensure_base_path(base_path: Path) -> None:
    """Create the base storage directory if it does not exist."""
    base_path.mkdir(parents=True, exist_ok=True)


def _group_path(base_path: Path, group: str) -> Path:
    """Return the resolved directory path for a group."""
    validate_group(group)
    return (base_path / group).resolve()


def _object_path(base_path: Path, group: str, key: str) -> Path:
    """Return the resolved file path for an object key within a group."""
    group_dir = _group_path(base_path, group)
    return group_dir / key
