"""Tool registry — a boring container of LangChain tools."""

from __future__ import annotations

import logging

from langchain_core.tools import BaseTool

log = logging.getLogger(__name__)


class ToolRegistry:
    """Mutable collection of tools that the agent can call."""

    def __init__(self) -> None:
        self._tools: list[BaseTool] = []

    def register(self, tool: BaseTool) -> None:
        """Add a single tool.  Replaces any existing tool with the same name."""
        existing = [idx for idx, t in enumerate(self._tools) if t.name == tool.name]
        if existing:
            self._tools[existing[0]] = tool
            log.debug("Replaced existing tool %r", tool.name)
        else:
            self._tools.append(tool)

    def extend(self, tools: list[BaseTool]) -> None:
        """Register every tool in *tools*."""
        for t in tools:
            self.register(t)

    def all(self) -> list[BaseTool]:
        """Return a snapshot of the current tool set."""
        return list(self._tools)


def load_builtin_tools() -> list[BaseTool]:
    """Return the default set of built-in demo tools."""
    from l2dllm.tools.builtin import echo, get_time

    return [get_time, echo]