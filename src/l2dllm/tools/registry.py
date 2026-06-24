"""Tool registry — a boring container of LangChain tools."""

from __future__ import annotations

import logging
from typing import Union

from langchain_core.tools import BaseTool

from l2dllm.tools.base import L2dTool

log = logging.getLogger(__name__)

ToolLike = Union[BaseTool, L2dTool]


class ToolRegistry:
    """Mutable collection of tools that the agent can call."""

    def __init__(self) -> None:
        self._tools: list[BaseTool] = []

    def register(self, tool: ToolLike) -> None:
        """Add a single tool. Replaces any existing tool with the same name."""
        if isinstance(tool, L2dTool):
            langchain_tool = tool.to_langchain_tool()
        else:
            langchain_tool = tool

        existing = [idx for idx, t in enumerate(self._tools) if t.name == langchain_tool.name]
        if existing:
            self._tools[existing[0]] = langchain_tool
            log.debug("Replaced existing tool %r", langchain_tool.name)
        else:
            self._tools.append(langchain_tool)

    def extend(self, tools: list[ToolLike]) -> None:
        """Register every tool in *tools*."""
        for t in tools:
            self.register(t)

    def all(self) -> list[BaseTool]:
        """Return a snapshot of the current tool set."""
        return list(self._tools)


def load_builtin_tools() -> list[L2dTool]:
    """Return the default set of built-in demo tools."""
    from l2dllm.tools.builtin import EchoTool, GetTimeTool

    return [GetTimeTool(), EchoTool()]


def load_all_tools() -> list[L2dTool]:
    """Return all available tools including built-in and utility tools."""
    from l2dllm.tools.builtin import EchoTool, GetTimeTool
    from l2dllm.tools.shell import ShellTool

    return [GetTimeTool(), EchoTool(), ShellTool()]
