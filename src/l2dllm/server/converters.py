"""OpenAI ↔ LangChain message conversions.

Used by the HTTP layer to translate inbound chat completion requests into
LangGraph state, and to repackage streaming chunks into OpenAI delta format.
"""

from __future__ import annotations

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from l2dllm.server.schemas import ChatMessage


def openai_messages_to_lc(messages: list[ChatMessage]) -> list[BaseMessage]:
    """Translate OpenAI-shaped messages into LangChain messages.

    Empty content is normalized to an empty string — the LangChain message
    classes reject ``None``. Tool calls on assistant messages are dropped on
    purpose: the graph re-derives them each turn, and reflecting stale calls
    back to the model just confuses it.
    """
    out: list[BaseMessage] = []
    for msg in messages:
        content = msg.content or ""
        if msg.role == "system":
            out.append(SystemMessage(content=content))
        elif msg.role == "user":
            out.append(HumanMessage(content=content))
        elif msg.role == "assistant":
            out.append(AIMessage(content=content))
        elif msg.role == "tool":
            # ToolMessage requires a tool_call_id — if missing we fall back to
            # a placeholder rather than crashing on a malformed history.
            out.append(
                ToolMessage(
                    content=content,
                    tool_call_id=msg.tool_call_id or "unknown",
                )
            )
    return out


def extract_text(chunk) -> str:
    """Pull plain text out of a LangChain chat chunk, ignoring tool-call deltas.

    Mirrors the logic the (now-removed) TUI used. Anthropic streams content as
    a list of typed blocks; OpenAI streams plain strings.
    """
    content = getattr(chunk, "content", None)
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)
