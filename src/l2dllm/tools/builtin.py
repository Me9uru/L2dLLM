"""Built-in demo tools for the skeleton agent."""

from __future__ import annotations

from datetime import datetime, timezone

from langchain_core.tools import tool


@tool
def get_time() -> str:
    """Return the current local time in ISO-8601 format."""
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@tool
def echo(text: str) -> str:
    """Echo the input text back unchanged. Useful for testing that tool calls work."""
    return text