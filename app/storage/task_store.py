import asyncio
from typing import Optional
from app.models.task import Task


class TaskStore:
    """Thread-safe in-memory task store backed by a plain dict + asyncio.Lock."""

    def __init__(self):
        self._store: dict[str, Task] = {}
        self._lock = asyncio.Lock()

    async def save(self, task: Task) -> Task:
        """Insert or update a task."""
        async with self._lock:
            self._store[task.id] = task
        return task

    async def get(self, task_id: str) -> Optional[Task]:
        """Return task by ID, or None if not found."""
        async with self._lock:
            return self._store.get(task_id)

    async def list_all(self) -> list[Task]:
        """Return all tasks sorted by creation time (newest last)."""
        async with self._lock:
            return sorted(self._store.values(), key=lambda t: t.created_at)


# Singleton instance shared across the application
task_store = TaskStore()
