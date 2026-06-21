"""Factory for creating object storage adapters from configuration."""

from __future__ import annotations

import os
from pathlib import Path

from briefchain.storage.base import ObjectStorage
from briefchain.storage.local import LocalObjectStorage


def _project_root() -> Path:
    """Return the project root directory.

    Assumes this module is located at ``src/briefchain/storage/factory.py``.
    """
    return Path(__file__).resolve().parents[3]


def create_storage(
    storage_type: str | None = None,
    base_path: Path | str | None = None,
    base_url: str | None = None,
) -> ObjectStorage:
    """Create an object storage adapter based on configuration.

    Args:
        storage_type: Backend type. Currently only ``local`` is supported.
        base_path: Root directory for local storage.
        base_url: Base URL used when generating object URLs.

    Returns:
        An initialized object storage adapter.
    """
    storage_type = (storage_type or os.getenv("OBJECT_STORAGE_TYPE", "local")).lower()

    if storage_type == "local":
        if base_path is None:
            base_path = os.getenv("OBJECT_STORAGE_PATH", _project_root() / ".storage")
        if base_url is None:
            base_url = os.getenv("OBJECT_STORAGE_BASE_URL", "/storage")
        return LocalObjectStorage(base_path=base_path, base_url=base_url)

    msg = f"Unsupported storage type: {storage_type}"
    raise ValueError(msg)
