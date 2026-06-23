"""Agent graph node factories and routing."""

from __future__ import annotations

from typing import Literal

from langchain_core.messages import SystemMessage
from langgraph.prebuilt import ToolNode

from l2dllm.agents.state import AgentState


def agent_node(model_with_tools, system_prompt: str):
    """Return an async node function that calls the LLM.

    The returned callable conforms to the ``StateGraph`` node signature:
    ``(state: AgentState) -> dict[str, list[AIMessage]]``.

    A ``SystemMessage`` is prepended when the message list doesn't already
    contain one.
    """

    async def _agent(state: AgentState) -> dict:
        messages = list(state["messages"])
        # LangGraph accumulates messages across turns — only inject the system
        # prompt on the very first turn when no system message exists yet.
        has_system = any(
            isinstance(m, SystemMessage) for m in messages
        )
        if not has_system and system_prompt:
            messages.insert(0, SystemMessage(content=system_prompt))

        response = await model_with_tools.ainvoke(messages)
        return {"messages": [response]}

    return _agent


def build_tool_node(tools):
    """Return a ``ToolNode`` pre-loaded with *tools*."""
    return ToolNode(tools)


def route_after_agent(state: AgentState) -> Literal["tools", "__end__"]:
    """Decide whether to continue to tool execution or end the conversation."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "__end__"