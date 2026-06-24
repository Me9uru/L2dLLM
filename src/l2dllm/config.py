"""Configuration loading from YAML files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel


class Settings(BaseModel):
    """L2dLLM configuration."""

    provider: Literal["openai", "anthropic"] = "openai"
    api_key: str = ""
    base_url: str = ""
    model: str = "gpt-4o"
    system_prompt: str = "You are a helpful assistant."
    max_tokens: int = 4096
    temperature: float = 0.7
    skills_dir: str = ""
    personas_dir: str = ""
    persona: str = ""
    max_iterations: int = 10
    host: str = "127.0.0.1"
    port: int = 8000

    # TTS (mimo-tts)
    tts_api_key: str = ""
    tts_base_url: str = "https://api.xiaomimimo.com/v1"
    tts_model: str = "mimo-v2.5-tts"
    tts_sample_rate: int = 24000
    tts_default_voice: str = "mimo_default"


_CONFIG_SEARCH_PATHS = [
    Path.cwd() / "config.yaml",
    Path.cwd() / "config.yml",
    Path.home() / ".config" / "l2dllm" / "config.yaml",
    Path.home() / ".config" / "l2dllm" / "config.yml",
]


def load_settings(config_path: str | None = None) -> Settings:
    """Load settings from a YAML config file.

    Search order:
    1. Explicit config_path argument
    2. ./config.yaml
    3. ~/.config/l2dllm/config.yaml
    4. Defaults
    """
    if config_path:
        return _load_from_file(Path(config_path))

    # Check environment variable
    env_path = os.environ.get("L2DLLM_CONFIG")
    if env_path:
        return _load_from_file(Path(env_path))

    for path in _CONFIG_SEARCH_PATHS:
        if path.exists():
            return _load_from_file(path)

    # Try env vars for API key
    api_key = os.environ.get("L2DLLM_API_KEY") or os.environ.get(
        "OPENAI_API_KEY", ""
    )
    if api_key:
        return Settings(api_key=api_key)

    return Settings()


def _load_from_file(path: Path) -> Settings:
    """Load settings from a YAML file."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    # Allow env var override for api_key
    if not data.get("api_key"):
        env_key = os.environ.get("L2DLLM_API_KEY")
        if data.get("provider") == "anthropic":
            env_key = env_key or os.environ.get("ANTHROPIC_API_KEY")
        else:
            env_key = env_key or os.environ.get("OPENAI_API_KEY")
        if env_key:
            data["api_key"] = env_key

    # Allow env var override for tts_api_key
    if not data.get("tts_api_key"):
        env_tts_key = os.environ.get("MIMO_API_KEY") or os.environ.get("TTS_API_KEY")
        if env_tts_key:
            data["tts_api_key"] = env_tts_key

    return Settings(**data)
