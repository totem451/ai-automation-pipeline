from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.models.task import Task, TaskCreate
from app.services.agent import run_agent
from app.storage.task_store import TaskStore, task_store

router = APIRouter(tags=["tasks"])


def get_store() -> TaskStore:
    """Dependency that returns the shared in-memory TaskStore."""
    return task_store


@router.post(
    "/tasks",
    response_model=Task,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create and enqueue a new task",
    description=(
        "Accepts a natural-language instruction, persists a Task record with "
        "status=pending, schedules the ReAct agent to run it in the background, "
        "and immediately returns the task (status 202 Accepted)."
    ),
)
async def create_task(
    body: TaskCreate,
    background_tasks: BackgroundTasks,
    store: TaskStore = Depends(get_store),
) -> Task:
    task = Task(instruction=body.instruction)
    await store.save(task)
    background_tasks.add_task(run_agent, task, store)
    return task


@router.get(
    "/tasks/{task_id}",
    response_model=Task,
    summary="Get a task by ID",
)
async def get_task(
    task_id: str,
    store: TaskStore = Depends(get_store),
) -> Task:
    task = await store.get(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task '{task_id}' not found.",
        )
    return task


@router.get(
    "/tasks",
    response_model=list[Task],
    summary="List all tasks",
)
async def list_tasks(
    store: TaskStore = Depends(get_store),
) -> list[Task]:
    return await store.list_all()
