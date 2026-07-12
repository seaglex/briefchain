"""Factory for creating the configured task queue backend."""

from __future__ import annotations

from briefchain.api.config import settings
from briefchain.arbiter.queue.base import TaskQueue
from briefchain.arbiter.queue.database import DatabaseTaskQueue

# Supported backend identifiers.
_DATABASE_BACKEND = "database"


class UnsupportedQueueBackendError(ValueError):
    """Raised when ``QUEUE_BACKEND`` references an unsupported backend."""



def create_queue() -> TaskQueue:
    """Create a task queue instance based on the current configuration."""
    backend = (settings.queue_backend or _DATABASE_BACKEND).lower()
    if backend == _DATABASE_BACKEND:
        return DatabaseTaskQueue()
    raise UnsupportedQueueBackendError(f"Unsupported queue backend: {backend}")
