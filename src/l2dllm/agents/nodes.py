"""Agent graph node factories and routing."""

from __future__ import annotations

from typing import Literal

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode

from l2dllm.agents.state import AgentState


def agent_node(model_with_tools, system_prompt: str):
    """Return an async node function that calls the LLM.

    The returned callable conforms to the ``StateGraph`` node signature:
    ``(state, config) -> dict[str, list[AIMessage]]``.

    A ``SystemMessage`` is prepended when the message list doesn't already
    contain one. The ``RunnableConfig`` LangGraph passes in must be forwarded
    to ``ainvoke`` so the parent ``astream_events`` run tree can see the LLM
    callbacks (``on_chat_model_start`` / ``stream`` / ``end``) — without it
    the TUI gets no streaming text and no end-of-turn signal.
    """

    async def _agent(state: AgentState, config: RunnableConfig) -> dict:
        messages = list(state["messages"])
        # LangGraph accumulates messages across turns — only inject the system
        # prompt on the very first turn when no system message exists yet.
        has_system = any(
            isinstance(m, SystemMessage) for m in messages
        )
        if not has_system and system_prompt:
            messages.insert(0, SystemMessage(content=system_prompt))

        response = await model_with_tools.ainvoke(messages, config)
        return {"messages": [response]}

    return _agent


def build_tool_node(tools):
    """Return a ``ToolNode`` pre-loaded with *tools*."""
    return ToolNode(tools)


def route_after_agent(state: AgentState) -> Literal["tools", "tts", "__end__"]:
    """Decide whether to continue to tool execution, TTS, or end the conversation."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    if state.get("tts_enabled"):
        return "tts"
    return "__end__"