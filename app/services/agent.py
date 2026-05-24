"""ReAct agent loop: Reason → Act → Observe → repeat."""
import logging
from datetime import datetime
from typing import Any

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

from app.core.config import settings
from app.models.task import Task, TaskStatus, TaskStep
from app.services.gemini_client import get_gemini_client
from app.services.tools.registry import execute_tool
from app.storage.task_store import TaskStore

logger = logging.getLogger(__name__)


def _build_user_message(instruction: str) -> dict[str, Any]:
    """Wrap the task instruction as a user turn."""
    return {"role": "user", "parts": [{"text": instruction}]}


def _extract_text(response: GenerateContentResponse) -> str | None:
    """Return the first text part from the response, or None."""
    try:
        candidate = response.candidates[0]
        for part in candidate.content.parts:
            if hasattr(part, "text") and part.text:
                return part.text.strip()
    except (IndexError, AttributeError):
        pass
    return None


def _extract_function_call(
    response: GenerateContentResponse,
) -> tuple[str, dict[str, Any]] | None:
    """Return (function_name, args_dict) if the response contains a function call."""
    try:
        candidate = response.candidates[0]
        for part in candidate.content.parts:
            if hasattr(part, "function_call") and part.function_call:
                fc = part.function_call
                # Convert MapComposite to a plain dict
                args = dict(fc.args) if fc.args else {}
                return fc.name, args
    except (IndexError, AttributeError):
        pass
    return None


def _response_to_content(response: GenerateContentResponse) -> dict[str, Any]:
    """Convert the model response into a Gemini Content dict for the history."""
    try:
        candidate = response.candidates[0]
        parts = []
        for part in candidate.content.parts:
            if hasattr(part, "function_call") and part.function_call:
                parts.append({"function_call": part.function_call})
            elif hasattr(part, "text") and part.text:
                parts.append({"text": part.text})
        return {"role": "model", "parts": parts}
    except (IndexError, AttributeError):
        return {"role": "model", "parts": [{"text": ""}]}


async def run_agent(task: Task, store: TaskStore) -> None:
    """Execute the ReAct agent loop for a given task.

    The loop proceeds as follows:
    1. Send the task instruction (+ full conversation history) to Gemini.
    2. If the model responds with a function_call → execute the tool,
       record the step, append the function result to history, and iterate.
    3. If the model responds with plain text → treat it as the final answer
       and mark the task COMPLETED.
    4. If max_iterations is reached without a final answer → mark FAILED.

    Args:
        task: The Task object to execute (mutated in place).
        store: The TaskStore used to persist status updates.
    """
    client = get_gemini_client()

    # Mark as running
    task.status = TaskStatus.RUNNING
    task.updated_at = datetime.utcnow()
    await store.save(task)

    # Conversation history in Gemini Content format
    history: list[dict[str, Any]] = [_build_user_message(task.instruction)]

    max_iterations = settings.max_agent_iterations

    try:
        for iteration in range(max_iterations):
            logger.info(
                "Task %s – iteration %d/%d", task.id, iteration + 1, max_iterations
            )

            # ----------------------------------------------------------------
            # Call Gemini
            # ----------------------------------------------------------------
            response: GenerateContentResponse = await client.generate(history)

            # ----------------------------------------------------------------
            # Check finish reason / safety
            # ----------------------------------------------------------------
            try:
                finish_reason = response.candidates[0].finish_reason
                # finish_reason == 1 means STOP (normal), 2 means MAX_TOKENS, etc.
                # We continue processing regardless; safety blocks are handled below.
            except (IndexError, AttributeError):
                finish_reason = None

            # ----------------------------------------------------------------
            # Detect function call
            # ----------------------------------------------------------------
            fc = _extract_function_call(response)
            if fc is not None:
                tool_name, tool_args = fc
                logger.info("Task %s – calling tool '%s' with %s", task.id, tool_name, tool_args)

                # Execute the tool
                observation = execute_tool(tool_name, tool_args)
                logger.info("Task %s – observation: %s", task.id, observation[:200])

                # Record the step
                step = TaskStep(
                    thought=f"Iteration {iteration + 1}: Calling tool '{tool_name}'",
                    action=tool_name,
                    action_input=tool_args,
                    observation=observation,
                )
                task.steps.append(step)
                task.updated_at = datetime.utcnow()
                await store.save(task)

                # Append model turn + function result to history
                history.append(_response_to_content(response))
                history.append(
                    {
                        "role": "user",
                        "parts": [
                            {
                                "function_response": {
                                    "name": tool_name,
                                    "response": {"result": observation},
                                }
                            }
                        ],
                    }
                )
                # Continue the loop
                continue

            # ----------------------------------------------------------------
            # No function call → expect a final text answer
            # ----------------------------------------------------------------
            final_text = _extract_text(response)
            if final_text:
                # Record the final reasoning step
                step = TaskStep(
                    thought=f"Iteration {iteration + 1}: Final answer produced.",
                    action=None,
                    action_input=None,
                    observation=final_text,
                )
                task.steps.append(step)
                task.result = final_text
                task.status = TaskStatus.COMPLETED
                task.updated_at = datetime.utcnow()
                await store.save(task)
                logger.info("Task %s – completed successfully.", task.id)
                return

            # Edge case: no function call AND no text – model may have produced
            # an empty response.  Record and continue; Gemini will usually
            # self-correct on the next turn.
            logger.warning("Task %s – empty response at iteration %d.", task.id, iteration + 1)
            step = TaskStep(
                thought=f"Iteration {iteration + 1}: Received empty response from model.",
            )
            task.steps.append(step)
            task.updated_at = datetime.utcnow()
            await store.save(task)

            # Ask the model to continue
            history.append(_response_to_content(response))
            history.append(
                {
                    "role": "user",
                    "parts": [{"text": "Please continue and provide your final answer."}],
                }
            )

        # Exhausted all iterations without a final answer
        task.status = TaskStatus.FAILED
        task.error = (
            f"Agent did not produce a final answer within {max_iterations} iterations."
        )
        task.updated_at = datetime.utcnow()
        await store.save(task)
        logger.warning("Task %s – failed: max iterations reached.", task.id)

    except Exception as exc:
        logger.exception("Task %s – unhandled exception: %s", task.id, exc)
        task.status = TaskStatus.FAILED
        task.error = f"Unexpected error: {exc}"
        task.updated_at = datetime.utcnow()
        await store.save(task)
