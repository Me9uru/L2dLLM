"""Built-in demo tools for the skeleton agent."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from l2dllm.tools.base import L2dTool


class GetTimeInput(BaseModel):
    """Input schema for get_time tool."""

    pass


class GetTimeTool(L2dTool):
    """Tool that returns the current local time."""

    @property
    def tool_name(self) -> str:
        return "get_time"

    @property
    def tool_description(self) -> str:
        return "Return the current local time in ISO-8601 format."

    @property
    def input_schema(self) -> type[BaseModel]:
        return GetTimeInput

    async def _execute(self, **kwargs: Any) -> str:
        return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


class EchoInput(BaseModel):
    """Input schema for echo tool."""

    text: str = Field(description="The text to echo back unchanged.")


class EchoTool(L2dTool):
    """Tool that echoes input text back unchanged."""

    @property
    def tool_name(self) -> str:
        return "echo"

    @property
    def tool_description(self) -> str:
        return "Echo the input text back unchanged. Useful for testing that tool calls work."

    @property
    def input_schema(self) -> type[BaseModel]:
        return EchoInput

    async def _execute(self, text: str, **kwargs: Any) -> str:
        return text


def get_builtin_tools() -> list[L2dTool]:
    """Return all built-in tools."""
    return [GetTimeTool(), EchoTool()]
