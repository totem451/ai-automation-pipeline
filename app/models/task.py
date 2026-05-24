from enum import Enum
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field
import uuid


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskCreate(BaseModel):
    instruction: str = Field(..., description="Natural language task instruction", min_length=5)


class TaskStep(BaseModel):
    thought: str
    action: str | None = None
    action_input: dict | None = None
    observation: str | None = None


class TaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    result: str | None = None
    error: str | None = None


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    instruction: str
    status: TaskStatus = TaskStatus.PENDING
    steps: list[TaskStep] = []
    result: str | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
