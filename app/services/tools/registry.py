"""Tool registry: wraps Python tool functions as Gemini FunctionDeclarations."""
from typing import Any

import google.generativeai as genai
from google.generativeai.types import Tool, FunctionDeclaration

from app.services.tools.calculator import calculate
from app.services.tools.datetime_tool import get_current_datetime
from app.services.tools.web_search import web_search

# ---------------------------------------------------------------------------
# Gemini FunctionDeclarations
# ---------------------------------------------------------------------------

_CALCULATOR_DECL = FunctionDeclaration(
    name="calculate",
    description=(
        "Evaluate a mathematical expression and return the numeric result. "
        "Supports +, -, *, /, //, %, ** and parentheses. "
        "Use this tool whenever you need to perform arithmetic."
    ),
    parameters={
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": (
                    "A mathematical expression to evaluate, e.g. '(3 + 5) * 2' or '2 ** 10'."
                ),
            }
        },
        "required": ["expression"],
    },
)

_DATETIME_DECL = FunctionDeclaration(
    name="get_current_datetime",
    description=(
        "Return the current date and time in UTC. "
        "Use this tool whenever you need to know today's date or the current time."
    ),
    parameters={
        "type": "object",
        "properties": {
            "timezone_name": {
                "type": "string",
                "description": "Timezone identifier (default: 'UTC').",
            }
        },
        "required": [],
    },
)

_WEB_SEARCH_DECL = FunctionDeclaration(
    name="web_search",
    description=(
        "Search the web using DuckDuckGo and return the top results with titles "
        "and descriptions. Use this tool to look up current information, facts, "
        "news, definitions, or anything that requires up-to-date knowledge."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to look up.",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (1-10, default 3).",
            },
        },
        "required": ["query"],
    },
)

# ---------------------------------------------------------------------------
# Registry: name → callable
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, Any] = {
    "calculate": calculate,
    "get_current_datetime": get_current_datetime,
    "web_search": web_search,
}


def get_tools() -> list[Tool]:
    """Return the list of Gemini Tool objects to pass to GenerativeModel."""
    return [
        Tool(
            function_declarations=[
                _CALCULATOR_DECL,
                _DATETIME_DECL,
                _WEB_SEARCH_DECL,
            ]
        )
    ]


def execute_tool(name: str, args: dict[str, Any]) -> str:
    """Dispatch a tool call by name and return a string observation.

    Args:
        name: The function name as declared in Gemini.
        args: Keyword arguments extracted from the model's function_call.

    Returns:
        String result from the tool.

    Raises:
        ValueError: If the tool name is not registered.
    """
    if name not in TOOL_REGISTRY:
        raise ValueError(
            f"Unknown tool '{name}'. Available tools: {list(TOOL_REGISTRY.keys())}"
        )
    func = TOOL_REGISTRY[name]
    try:
        result = func(**args)
        return str(result)
    except Exception as exc:
        return f"Tool '{name}' raised an error: {exc}"
