"""TTS module using mimo-tts service via OpenAI-compatible API."""

from __future__ import annotations

import base64
from typing import AsyncIterator

import httpx
import numpy as np

from l2dllm.config import Settings


def _get_tts_headers(settings: Settings) -> dict[str, str]:
    """Build headers for MiMo TTS API (uses api-key header)."""
    return {
        "api-key": settings.tts_api_key,
        "Content-Type": "application/json",
    }


def generate_tts_stream(
    text: str,
    settings: Settings,
    voice_instruction: str = "Give me a young male tone.",
    voice: str | None = None,
) -> AsyncIterator[bytes]:
    """Generate TTS audio from text using mimo-tts, yielding PCM16 chunks.

    Yields raw PCM16LE bytes in 24kHz mono format.
    """
    import json

    voice = voice or settings.tts_default_voice

    messages = [
        {"role": "user", "content": voice_instruction},
        {"role": "assistant", "content": text},
    ]

    payload = {
        "model": settings.tts_model,
        "messages": messages,
        "audio": {"format": "pcm16", "voice": voice},
        "stream": True,
    }

    headers = _get_tts_headers(settings)

    with httpx.Client(timeout=300.0) as client:
        with client.stream(
            "POST",
            f"{settings.tts_base_url}/chat/completions",
            headers=headers,
            json=payload,
        ) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        if not chunk.get("choices"):
                            continue
                        delta = chunk["choices"][0].get("delta", {})
                        audio = delta.get("audio")
                        if audio and isinstance(audio, dict) and "data" in audio:
                            pcm_bytes = base64.b64decode(audio["data"])
                            yield pcm_bytes
                    except json.JSONDecodeError:
                        continue


def generate_tts(
    text: str,
    settings: Settings,
    voice_instruction: str = "Give me a young male tone.",
    voice: str | None = None,
) -> tuple[bytes, int]:
    """Generate TTS audio from text using mimo-tts.

    Returns (wav_bytes, sample_rate).
    """
    import io

    import soundfile as sf

    all_pcm: list[np.ndarray] = []
    for pcm_bytes in generate_tts_stream(text, settings, voice_instruction, voice):
        np_pcm = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        all_pcm.append(np_pcm)

    if not all_pcm:
        return b"", settings.tts_sample_rate

    collected = np.concatenate(all_pcm)
    buf = io.BytesIO()
    sf.write(buf, collected, samplerate=settings.tts_sample_rate, format="WAV")
    buf.seek(0)
    return buf.read(), settings.tts_sample_rate
