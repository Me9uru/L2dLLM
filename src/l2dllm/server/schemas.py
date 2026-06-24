"""Pydantic schemas mirroring the OpenAI Chat Completions API.

Only the fields we actually accept / emit are modeled. Unknown fields in
inbound requests are ignored (Pydantic v2 default) so newer client features
don't break the endpoint outright.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """One message in a chat completion request or response."""

    role: Literal["system", "user", "assistant", "tool"]
    content: str | None = None
    name: str | None = None
    tool_call_id: str | None = None
    # Inbound assistant messages may carry tool_calls; we accept and ignore them
    # (the graph re-derives tool calls per turn).
    tool_calls: list[dict[str, Any]] | None = None


class ChatCompletionRequest(BaseModel):
    """Subset of the OpenAI Chat Completions request body we honor."""

    model: str
    messages: list[ChatMessage]
    stream: bool = False
    temperature: float | None = None
    max_tokens: int | None = None
    tts: bool = False
    voice: str | None = None
    voice_instructions: str | None = None
    # The remaining OpenAI params (top_p, n, stop, presence_penalty, etc.) are
    # accepted-and-ignored — the underlying ChatModel is preconfigured via
    # settings; per-request overrides would require rebuilding the model.


class Delta(BaseModel):
    role: Literal["assistant"] | None = None
    content: str | None = None
    audio: dict[str, Any] | str | None = None


class Choice(BaseModel):
    index: int = 0
    message: ChatMessage | None = None
    delta: Delta | None = None
    finish_reason: str | None = None
    audio: str | None = None


class Usage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[Choice]
    usage: Usage = Field(default_factory=Usage)


class ChatCompletionChunk(BaseModel):
    id: str
    object: Literal["chat.completion.chunk"] = "chat.completion.chunk"
    created: int
    model: str
    choices: list[Choice]


class ModelInfo(BaseModel):
    id: str
    object: Literal["model"] = "model"
    created: int = 0
    owned_by: str = "l2dllm"


class ModelList(BaseModel):
    object: Literal["list"] = "list"
    data: list[ModelInfo]


class SpeechRequest(BaseModel):
    """Request body for POST /v1/audio/speech (OpenAI TTS-compatible)."""

    model: str = "mimo-v2.5-tts"
    input: str
    voice: str = "mimo_default"
    response_format: Literal["mp3", "opus", "aac", "flac", "wav", "pcm"] = "wav"
    speed: float = 1.0
    instructions: str | None = None
