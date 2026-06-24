"""Shared fixtures for L2dLLM tests."""

import pytest

from l2dllm.config import Settings, load_settings


@pytest.fixture
def settings() -> Settings:
    """Load real settings from config file or environment."""
    return load_settings()


@pytest.fixture
def tts_settings(settings: Settings) -> Settings:
    """Settings with TTS configured."""
    if not settings.tts_api_key:
        pytest.skip("TTS API key not configured (set MIMO_API_KEY)")
    return settings
