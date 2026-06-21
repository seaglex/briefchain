"""Object storage adapters for BriefChain.

This package provides a storage-agnostic interface for saving, reading, and
deleting arbitrary files. The default ``LocalObjectStorage`` adapter stores
files under the project directory's ``.storage/`` folder and supports
group-based isolation similar to cloud storage buckets or prefixes.
"""

from briefchain.storage.base import ObjectStorage, StoredObject
from briefchain.storage.factory import create_storage
from briefchain.storage.local import LocalObjectStorage

__all__ = [
    "ObjectStorage",
    "StoredObject",
    "LocalObjectStorage",
    "create_storage",
]
