"""Conditional external documentation grounding via Tavily AI Search."""

import os
import re
from tavily import TavilyClient

try:
    from .runner import TestFailure
    from .config import TAVILY_API_KEY
except (ImportError, ValueError):
    from runner import TestFailure
    TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")


def is_external_error(failure: TestFailure) -> bool:
    """Determine if a TestFailure is caused by an external dependency or deprecation."""
    err_type = failure.error_type or ""
    msg = failure.message or ""
    full_text = f"{err_type}: {msg}".lower()

    # 1. Direct package / import errors
    if err_type in {"ModuleNotFoundError", "ImportError", "PackageNotFoundError"}:
        return True

    # 2. Standard library / third-party deprecation warnings
    if any(k in err_type.lower() for k in ("deprecation", "futurewarning")):
        return True
    if any(k in msg.lower() for k in ("deprecated", "deprecation")):
        return True

    # 3. Module-level attribute failures (e.g. AttributeError: module 'x' has no attribute 'y')
    if err_type == "AttributeError" and "module" in msg.lower():
        return True

    # 4. Keyword patterns indicating missing or incompatible libraries
    external_patterns = (
        r"\bno module named\b",
        r"\bcannot import name\b",
        r"\bwas removed in\b",
        r"\bhas no attribute\b.*?\bmodule\b",
        r"\bmodule\b.*?\bhas no attribute\b",
    )
    if any(re.search(pat, full_text) for pat in external_patterns):
        return True

    return False


def ground_error(
    failure: TestFailure,
    client: TavilyClient | None = None,
    api_key: str | None = None,
) -> list[str] | None:
    """Conditionally ground an external test failure using Tavily search."""
    if not is_external_error(failure):
        return None

    query = (
        f"{failure.error_type}: {failure.message} python"
        if failure.message
        else f"{failure.error_type} python"
    )

    if client is None:
        client = TavilyClient(api_key=api_key or os.environ.get("TAVILY_API_KEY"))

    response = client.search(query=query, max_results=2)
    results = response.get("results", []) if isinstance(response, dict) else []
    snippets = [
        r["content"].strip()
        for r in results
        if isinstance(r, dict) and r.get("content")
    ][:2]
    return snippets


ground = ground_error
ground_failure = ground_error
search_external = ground_error
