"""Unit tests for the object storage abstraction."""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

import pytest

from briefchain.storage import LocalObjectStorage, create_storage
from briefchain.storage.base import StoredObject, validate_group


@pytest.fixture
def storage(tmp_path: Path) -> LocalObjectStorage:
    """Create a local storage adapter backed by a temporary directory."""
    return LocalObjectStorage(base_path=tmp_path, base_url="/files")


def test_save_returns_metadata(storage: LocalObjectStorage) -> None:
    """Saving a file returns complete metadata."""
    data = b"hello world"
    obj = storage.save(BytesIO(data), "hello.txt", "text/plain")

    assert isinstance(obj, StoredObject)
    assert obj.filename == "hello.txt"
    assert obj.content_type == "text/plain"
    assert obj.size == len(data)
    assert obj.group == "default"
    assert obj.url.startswith("/files/default/")


def test_save_bytes_input(storage: LocalObjectStorage) -> None:
    """Saving raw bytes works the same as a binary stream."""
    data = b"raw bytes"
    obj = storage.save(data, "raw.bin", "application/octet-stream")

    retrieved = storage.get(obj.key).read()
    assert retrieved == data


def test_get_retrieves_file_content(storage: LocalObjectStorage) -> None:
    """get returns a readable stream with the original content."""
    data = b"retrievable content"
    obj = storage.save(BytesIO(data), "doc.md", "text/markdown")

    with storage.get(obj.key) as stream:
        assert stream.read() == data


def test_get_missing_object_raises(storage: LocalObjectStorage) -> None:
    """get raises FileNotFoundError for a non-existent key."""
    with pytest.raises(FileNotFoundError):
        storage.get(str(uuid4()))


def test_delete_removes_file(storage: LocalObjectStorage) -> None:
    """delete removes the stored object."""
    obj = storage.save(BytesIO(b"to delete"), "delete.me", "text/plain")
    storage.delete(obj.key)

    with pytest.raises(FileNotFoundError):
        storage.get(obj.key)


def test_delete_missing_object_is_noop(storage: LocalObjectStorage) -> None:
    """delete is a no-op for a non-existent key."""
    storage.delete(str(uuid4()))


def test_get_url_includes_group_and_key(storage: LocalObjectStorage) -> None:
    """get_url composes base URL, group, and key."""
    obj = storage.save(BytesIO(b"x"), "x.txt", "text/plain", group="avatars")
    url = storage.get_url(obj.key, group="avatars")

    assert url == f"/files/avatars/{obj.key}"


def test_same_filename_gets_distinct_keys(storage: LocalObjectStorage) -> None:
    """Two files with the same original name receive different keys."""
    obj1 = storage.save(BytesIO(b"first"), "same.txt", "text/plain")
    obj2 = storage.save(BytesIO(b"second"), "same.txt", "text/plain")

    assert obj1.key != obj2.key
    assert storage.get(obj1.key).read() == b"first"
    assert storage.get(obj2.key).read() == b"second"


def test_group_isolation(storage: LocalObjectStorage) -> None:
    """Objects in different groups are isolated on disk."""
    obj_a = storage.save(BytesIO(b"a"), "file.txt", "text/plain", group="group-a")
    obj_b = storage.save(BytesIO(b"b"), "file.txt", "text/plain", group="group-b")

    assert storage.get(obj_a.key, group="group-a").read() == b"a"
    assert storage.get(obj_b.key, group="group-b").read() == b"b"
    with pytest.raises(FileNotFoundError):
        storage.get(obj_a.key, group="group-b")


def test_list_objects_in_group(storage: LocalObjectStorage) -> None:
    """list returns all objects in the requested group."""
    storage.save(BytesIO(b"1"), "one.txt", "text/plain", group="docs")
    storage.save(BytesIO(b"2"), "two.txt", "text/plain", group="docs")
    storage.save(BytesIO(b"3"), "three.txt", "text/plain", group="images")

    docs = storage.list(group="docs")
    assert len(docs) == 2
    assert {obj.filename for obj in docs} == {"one.txt", "two.txt"}

    images = storage.list(group="images")
    assert len(images) == 1


def test_list_empty_group(storage: LocalObjectStorage) -> None:
    """list returns an empty list for a group that has no objects."""
    assert storage.list(group="empty") == []


def test_validate_group_rejects_invalid_names() -> None:
    """Group names containing path separators or parent references are rejected."""
    invalid_names = ["", ".", "..", "a/b", "a\\b", "../foo", "foo/../bar"]
    for name in invalid_names:
        with pytest.raises(ValueError):
            validate_group(name)


def test_factory_returns_local_adapter_by_default(tmp_path: Path) -> None:
    """create_storage returns a LocalObjectStorage instance by default."""
    adapter = create_storage(base_path=tmp_path)
    assert isinstance(adapter, LocalObjectStorage)


def test_factory_rejects_unsupported_storage_type(tmp_path: Path) -> None:
    """create_storage raises ValueError for unsupported storage types."""
    with pytest.raises(ValueError):
        create_storage(storage_type="s3", base_path=tmp_path)
