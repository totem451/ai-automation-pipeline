from duckduckgo_search import DDGS


def web_search(query: str, max_results: int = 3) -> str:
    """Search the web using DuckDuckGo and return summarised results.

    Args:
        query: The search query string.
        max_results: Maximum number of results to include (default 3).

    Returns:
        A formatted string with titles and snippets for each result,
        or a message indicating no results were found.
    """
    if not query or not query.strip():
        return "No query provided."

    max_results = max(1, min(max_results, 10))  # clamp to [1, 10]

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query.strip(), max_results=max_results))
    except Exception as exc:
        return f"Search failed: {exc}"

    if not results:
        return "No results found."

    parts: list[str] = []
    for i, r in enumerate(results, start=1):
        title = r.get("title", "No title")
        body = r.get("body", "No description available.")
        href = r.get("href", "")
        entry = f"**[{i}] {title}**\n{body}"
        if href:
            entry += f"\nSource: {href}"
        parts.append(entry)

    return "\n\n".join(parts)
