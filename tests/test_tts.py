"""Tests for TTS service connectivity."""

import os
import subprocess

from l2dllm.config import Settings
from l2dllm.tts import generate_tts, generate_tts_stream


def _play_audio(path: str):
    """Play audio file using ffplay (non-blocking)."""
    subprocess.Popen(
        ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class TestTTSConnectivity:
    """Verify mimo-tts service is reachable and returns audio."""

    def test_generate_tts_returns_wav(self, tts_settings: Settings):
        """TTS should return non-empty WAV bytes."""
        wav_bytes, sample_rate = generate_tts(
            "你好，世界！",
            tts_settings,
            voice_instruction="Give me a young female tone.",
        )
        assert len(wav_bytes) > 0
        assert sample_rate == 24000
        assert wav_bytes[:4] == b"RIFF"

        os.makedirs("tmp", exist_ok=True)
        path = "tmp/tts_test.wav"
        with open(path, "wb") as f:
            f.write(wav_bytes)
        print(f"\nAudio saved to {path} ({len(wav_bytes)} bytes)")
        _play_audio(path)

    def test_generate_tts_stream_yields_pcm(self, tts_settings: Settings):
        """TTS stream should yield PCM chunks."""
        chunks = list(
            generate_tts_stream(
                "测试语音",
                tts_settings,
                voice_instruction="Give me a young male tone.",
            )
        )
        assert len(chunks) > 0
        total_bytes = sum(len(c) for c in chunks)
        assert total_bytes > 0

    def test_generate_tts_cat_persona(self, tts_settings: Settings):
        """TTS with cat persona voice instruction."""
        wav_bytes, sample_rate = generate_tts(
            "Hello master!",
            tts_settings,
            voice_instruction="Give me a cute young female tone.",
        )
        assert len(wav_bytes) > 0
        assert wav_bytes[:4] == b"RIFF"

        os.makedirs("tmp", exist_ok=True)
        path = "tmp/tts_test_cat.wav"
        with open(path, "wb") as f:
            f.write(wav_bytes)
        print(f"\nAudio saved to {path} ({len(wav_bytes)} bytes)")
        _play_audio(path)
