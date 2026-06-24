"""Agent state definition."""

from __future__ import annotations

from langgraph.graph.message import MessagesState


class AgentState(MessagesState):
    """State carried through the LangGraph agent.

    ``messages`` (the only field) is managed by the built-in ``add_messages``
    reducer — every node that returns ``{"messages": [msg]}`` appends to the
    list and deduplicates by message ID.
    """

    tts_enabled: bool = False
    tts_voice: str = "mimo_default"
    tts_voice_instructions: str | None = None
    tts_audio: str | None = None