"""Local file system implementation of the object storage interface."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

from briefchain.storage.base import (
    StoredObject,
    _ensure_base_path,
    _group_path,
    _object_path,
    generate_key,
    validate_group,
)


class LocalObjectStorage:
    """Object storage adapter that stores files in a local directory."""

    DEFAULT_GROUP = "default"
    META_SUFFIX = ".meta.json"

    def __init__(self, base_path: Path | str, base_url: str = "/storage") -> None:
        """Initialize the local storage adapter.

        Args:
            base_path: Root directory where objects are stored.
            base_url: Base URL used when generating object URLs.
        """
        self.base_path = Path(base_path).resolve()
        self.base_url = base_url.rstrip("/")
        _ensure_base_path(self.base_path)

    def _meta_path(self, group: str, key: str) -> Path:
        """Return the sidecar metadata path for an object."""
        return _object_path(self.base_path, group, f"{key}{self.META_SUFFIX}")

    def _write_meta(self, obj: StoredObject) -> None:
        """Persist object metadata to a sidecar JSON file."""
        meta_path = self._meta_path(obj.group, obj.key)
        meta = {
            "key": obj.key,
            "filename": obj.filename,
            "content_type": obj.content_type,
            "size": obj.size,
            "url": obj.url,
            "group": obj.group,
            "created_at": obj.created_at.isoformat(),
        }
        meta_path.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")

    def _read_meta(self, group: str, key: str) -> StoredObject | None:
        """Read object metadata from a sidecar JSON file."""
        meta_path = self._meta_path(group, key)
        if not meta_path.exists():
            return None
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return StoredObject(
            key=meta["key"],
            filename=meta["filename"],
            content_type=meta["content_type"],
            size=meta["size"],
            url=meta["url"],
            group=meta["group"],
            created_at=datetime.fromisoformat(meta["created_at"]),
        )

    def save(
        self,
        file: BinaryIO | bytes,
        filename: str,
        content_type: str,
        group: str | None = None,
    ) -> StoredObject:
        """Save an object to the local file system."""
        group = group or self.DEFAULT_GROUP
        validate_group(group)

        key = generate_key()
        group_dir = _group_path(self.base_path, group)
        group_dir.mkdir(parents=True, exist_ok=True)
        obj_path = group_dir / key

        if isinstance(file, bytes):
            data = file
            obj_path.write_bytes(data)
        else:
            data = file.read()
            obj_path.write_bytes(data)

        obj = StoredObject(
            key=key,
            filename=filename,
            content_type=content_type,
            size=len(data),
            url=self.get_url(key, group),
            group=group,
            created_at=datetime.now(UTC),
        )
        self._write_meta(obj)
        return obj

    def get(self, key: str, group: str | None = None) -> BinaryIO:
        """Return a readable stream for the object."""
        group = group or self.DEFAULT_GROUP
        obj_path = _object_path(self.base_path, group, key)
        if not obj_path.exists():
            msg = f"Object not found: {key} in group {group}"
            raise FileNotFoundError(msg)
        return open(obj_path, "rb")  # noqa: SIM115

    def delete(self, key: str, group: str | None = None) -> None:
        """Delete the object and its metadata from the local file system."""
        group = group or self.DEFAULT_GROUP
        obj_path = _object_path(self.base_path, group, key)
        meta_path = self._meta_path(group, key)
        if obj_path.exists():
            obj_path.unlink()
        if meta_path.exists():
            meta_path.unlink()

    def get_url(self, key: str, group: str | None = None) -> str:
        """Return a URL addressing the object."""
        group = group or self.DEFAULT_GROUP
        validate_group(group)
        return f"{self.base_url}/{group}/{key}"

    def list(self, group: str | None = None) -> list[StoredObject]:
        """List all objects in the given group."""
        group = group or self.DEFAULT_GROUP
        group_dir = _group_path(self.base_path, group)
        if not group_dir.exists():
            return []

        objects: list[StoredObject] = []
        for entry in group_dir.iterdir():
            if not entry.is_file() or entry.suffixes == [".meta", ".json"]:
                continue
            obj = self._read_meta(group, entry.name)
            if obj is not None:
                objects.append(obj)
        return objects
