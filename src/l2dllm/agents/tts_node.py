"""TTS node for LangGraph agent."""

from __future__ import annotations

import base64

from langchain_core.messages import AIMessage

from l2dllm.agents.state import AgentState
from l2dllm.config import Settings
from l2dllm.tts import generate_tts


def build_tts_node(settings: Settings):
    """Return a node function that generates TTS audio from the final response."""

    async def _tts(state: AgentState) -> dict:
        if not state.get("tts_enabled") or not settings.tts_api_key:
            return {}

        # Find the last AI message with content (skip tool calls/results)
        text = ""
        for msg in reversed(state["messages"]):
            if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
                text = msg.content
                break

        if not text:
            return {}

        voice = state.get("tts_voice") or settings.tts_default_voice
        voice_instructions = state.get("tts_voice_instructions") or "用自然的语气说话"

        wav_bytes, _ = generate_tts(text, settings, voice_instructions, voice)

        if not wav_bytes:
            return {}

        audio_b64 = base64.b64encode(wav_bytes).decode("ascii")
        return {"tts_audio": audio_b64}

    return _tts
