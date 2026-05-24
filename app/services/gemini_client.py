"""Async wrapper around the Google Generative AI SDK."""
import asyncio
from typing import Any

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

from app.core.config import settings
from app.services.tools.registry import get_tools


class GeminiClient:
    """Thin async wrapper around google.generativeai.GenerativeModel."""

    def __init__(self):
        genai.configure(api_key=settings.gemini_api_key)
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            tools=get_tools(),
            system_instruction=(
                "You are an AI automation agent. Your job is to complete tasks given by users "
                "by reasoning step by step and using the available tools when needed.\n\n"
                "Available tools:\n"
                "- calculate(expression): Evaluate math expressions safely.\n"
                "- get_current_datetime(timezone_name): Get the current date/time.\n"
                "- web_search(query, max_results): Search the web via DuckDuckGo.\n\n"
                "Follow this loop:\n"
                "1. Think about what you need to do next.\n"
                "2. If you need external information or calculation, call a tool.\n"
                "3. Use the tool result to inform your next thought.\n"
                "4. When you have enough information, provide a clear final answer.\n\n"
                "Be concise, accurate, and always base your answer on actual tool results."
            ),
        )

    async def generate(
        self,
        messages: list[dict[str, Any]],
        generation_config: dict[str, Any] | None = None,
    ) -> GenerateContentResponse:
        """Send a list of messages to Gemini and return the response.

        The SDK's `generate_content_async` method is used so callers can
        ``await`` this method without blocking the event loop.

        Args:
            messages: Conversation history in Gemini's Content format.
                      Each element is a dict with "role" and "parts".
            generation_config: Optional generation parameters (temperature, etc.).

        Returns:
            A GenerateContentResponse from the Gemini API.
        """
        kwargs: dict[str, Any] = {}
        if generation_config:
            kwargs["generation_config"] = generation_config

        response: GenerateContentResponse = await self.model.generate_content_async(
            messages,
            **kwargs,
        )
        return response


# Module-level singleton – created lazily to avoid import-time side-effects
# when GEMINI_API_KEY is not yet set (e.g. during test collection).
_client: GeminiClient | None = None


def get_gemini_client() -> GeminiClient:
    """Return the shared GeminiClient singleton, creating it on first call."""
    global _client
    if _client is None:
        _client = GeminiClient()
    return _client
