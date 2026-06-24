"""FastAPI application exposing an OpenAI-compatible Chat Completions API.

Each persona is published as a distinct model id; selecting the model in the
client is how the user switches characters. A request that names an unknown
model falls back to the ``default`` model (no persona, uses
``settings.system_prompt``).

This module is deliberately small — the heavy lifting (agent loop, tool
calling, streaming) is delegated to the existing LangGraph plumbing.
"""

from __future__ import annotations

import json
import time
import uuid
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from langchain_core.messages import BaseMessage, SystemMessage

from l2dllm.personas.persona import Persona
from l2dllm.server.converters import extract_text, openai_messages_to_lc
from l2dllm.server.schemas import (
    ChatCompletionChunk,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    Choice,
    Delta,
    ModelInfo,
    ModelList,
    SpeechRequest,
)
from l2dllm.tts import generate_tts


DEFAULT_MODEL_ID = "default"


def create_app(graph, settings, personas_by_name: dict[str, Persona]) -> FastAPI:
    """Build the FastAPI app.

    Parameters
    ----------
    graph
        Compiled LangGraph state machine (from :func:`build_agent_graph`).
    settings
        Loaded :class:`Settings`. Used for ``system_prompt`` (the ``default``
        model's prompt) and ``max_iterations`` (graph recursion limit).
    personas_by_name
        All loaded personas, keyed by name.
    """
    app = FastAPI(title="L2dLLM", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def _resolve_system_prompt(model_id: str) -> str:
        """Look up the system prompt for a model id.

        ``default`` and any unknown id both fall through to
        ``settings.system_prompt`` — Open WebUI sometimes probes models we
        don't expose and we'd rather respond than 404.
        """
        if model_id == DEFAULT_MODEL_ID:
            return settings.system_prompt
        persona = personas_by_name.get(model_id)
        if persona is None:
            return settings.system_prompt
        return persona.body

    def _resolve_voice_instructions(model_id: str, user_instructions: str | None) -> str:
        """Get TTS voice instructions from persona or user override."""
        if user_instructions:
            return user_instructions
        if model_id != DEFAULT_MODEL_ID and model_id in personas_by_name:
            persona = personas_by_name[model_id]
            return f"用这个角色的语气说话：{persona.body}"
        return "Give me a young male tone."

    def _build_message_list(req: ChatCompletionRequest) -> list[BaseMessage]:
        """Translate OpenAI messages → LangChain messages with persona injected.

        Persona / default system prompt is always prepended. To avoid
        duplicating the same SystemMessage on every turn (clients often replay
        the full history including our previous system message), any inbound
        ``system`` message whose content exactly matches the active prompt is
        dropped before conversion.
        """
        sys_prompt = _resolve_system_prompt(req.model)
        filtered = [
            m for m in req.messages
            if not (m.role == "system" and (m.content or "") == sys_prompt)
        ]
        lc_messages = openai_messages_to_lc(filtered)
        return [SystemMessage(content=sys_prompt), *lc_messages]

    async def _run_agent_text_stream(
        req: ChatCompletionRequest,
    ) -> AsyncIterator[str | None]:
        """Yield text deltas, then None when done (signals completion).

        We forward every ``on_chat_model_stream`` event's text content. Tool
        calls happen inside the graph; the client never sees ``on_tool_*``
        events. If the model speaks before calling a tool ("Let me check…"),
        that text is streamed too — matches how OpenAI's own function calling
        looks to a client.
        """
        messages = _build_message_list(req)
        state = {
            "messages": messages,
            "tts_enabled": req.tts,
            "tts_voice": req.voice or settings.tts_default_voice,
            "tts_voice_instructions": req.voice_instructions,
        }
        async for event in graph.astream_events(
            state,
            version="v2",
            config={"recursion_limit": settings.max_iterations},
        ):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk is not None:
                    text = extract_text(chunk)
                    if text:
                        yield text
        yield None

    async def _run_agent_with_tts(
        req: ChatCompletionRequest,
    ) -> tuple[str, str | None]:
        """Run agent to completion and return (full_text, tts_audio_b64)."""
        messages = _build_message_list(req)
        state = {
            "messages": messages,
            "tts_enabled": req.tts,
            "tts_voice": req.voice or settings.tts_default_voice,
            "tts_voice_instructions": req.voice_instructions,
        }
        result = await graph.ainvoke(
            state,
            config={"recursion_limit": settings.max_iterations},
        )
        full_text = ""
        for msg in result.get("messages", []):
            if hasattr(msg, "content") and msg.content:
                full_text = msg.content
        return full_text, result.get("tts_audio")

    @app.get("/")
    async def root() -> dict:
        return {
            "name": "l2dllm",
            "openai_compatible": True,
            "endpoints": ["/v1/models", "/v1/chat/completions"],
        }

    @app.get("/v1")
    async def v1_root() -> dict:
        return {
            "endpoints": ["/v1/models", "/v1/chat/completions"],
            "hint": "GET /v1/models to list available models",
        }

    @app.get("/v1/models", response_model=ModelList)
    async def list_models() -> ModelList:
        models: list[ModelInfo] = [ModelInfo(id=DEFAULT_MODEL_ID)]
        models.extend(ModelInfo(id=name) for name in sorted(personas_by_name))
        return ModelList(data=models)

    @app.post("/v1/audio/speech")
    async def create_speech(req: SpeechRequest):
        if not settings.tts_api_key:
            raise HTTPException(
                status_code=501,
                detail="TTS not configured. Set tts_api_key in config or MIMO_API_KEY env var.",
            )

        voice_instruction = req.instructions or "Give me a young male tone."
        wav_bytes, sample_rate = generate_tts(req.input, settings, voice_instruction, req.voice)

        if not wav_bytes:
            raise HTTPException(status_code=500, detail="TTS generation failed.")

        if req.response_format == "wav":
            media_type = "audio/wav"
        elif req.response_format == "mp3":
            media_type = "audio/mpeg"
        elif req.response_format == "opus":
            media_type = "audio/opus"
        elif req.response_format == "aac":
            media_type = "audio/aac"
        elif req.response_format == "flac":
            media_type = "audio/flac"
        else:
            media_type = "audio/wav"

        return Response(content=wav_bytes, media_type=media_type)

    @app.post("/v1/chat/completions")
    async def chat_completions(req: ChatCompletionRequest, request: Request):
        if not req.messages:
            raise HTTPException(status_code=400, detail="messages must not be empty")

        completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
        created = int(time.time())

        if req.stream:
            return StreamingResponse(
                _sse_stream(req, completion_id, created, request),
                media_type="text/event-stream",
                # Disable proxy buffering so clients see tokens as they arrive.
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        # Non-streaming: drain the same generator into a single response body.
        full = ""
        async for delta in _run_agent_text_stream(req):
            if delta is None:
                break
            full += delta

        audio_b64 = None
        if req.tts and settings.tts_api_key and full:
            voice_instructions = _resolve_voice_instructions(req.model, req.voice_instructions)
            voice = req.voice or settings.tts_default_voice
            wav_bytes, _ = generate_tts(full, settings, voice_instructions, voice)
            if wav_bytes:
                import base64
                audio_b64 = base64.b64encode(wav_bytes).decode("ascii")

        return ChatCompletionResponse(
            id=completion_id,
            created=created,
            model=req.model,
            choices=[
                Choice(
                    index=0,
                    message=ChatMessage(role="assistant", content=full),
                    finish_reason="stop",
                    audio=audio_b64,
                )
            ],
        )

    async def _sse_stream(
        req: ChatCompletionRequest,
        completion_id: str,
        created: int,
        request: Request,
    ) -> AsyncIterator[bytes]:
        """Emit OpenAI-style SSE: a role-only opener, content deltas, then [DONE]."""
        opener = ChatCompletionChunk(
            id=completion_id,
            created=created,
            model=req.model,
            choices=[Choice(index=0, delta=Delta(role="assistant"))],
        )
        yield _sse(opener)

        full_text = ""
        try:
            async for text in _run_agent_text_stream(req):
                if await request.is_disconnected():
                    return
                if text is None:
                    break
                full_text += text
                chunk = ChatCompletionChunk(
                    id=completion_id,
                    created=created,
                    model=req.model,
                    choices=[Choice(index=0, delta=Delta(content=text))],
                )
                yield _sse(chunk)
        finally:
            audio_b64 = None
            if req.tts and settings.tts_api_key and full_text:
                voice_instructions = _resolve_voice_instructions(req.model, req.voice_instructions)
                voice = req.voice or settings.tts_default_voice
                wav_bytes, _ = generate_tts(full_text, settings, voice_instructions, voice)
                if wav_bytes:
                    import base64
                    audio_b64 = base64.b64encode(wav_bytes).decode("ascii")

            if audio_b64:
                audio_chunk = ChatCompletionChunk(
                    id=completion_id,
                    created=created,
                    model=req.model,
                    choices=[Choice(index=0, delta=Delta(audio=audio_b64))],
                )
                yield _sse(audio_chunk)

            closer = ChatCompletionChunk(
                id=completion_id,
                created=created,
                model=req.model,
                choices=[Choice(index=0, delta=Delta(), finish_reason="stop")],
            )
            yield _sse(closer)
            yield b"data: [DONE]\n\n"

    return app


def _sse(chunk: ChatCompletionChunk) -> bytes:
    """Format one OpenAI chat completion chunk as an SSE event."""
    payload = chunk.model_dump(exclude_none=True)
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")
