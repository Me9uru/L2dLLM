"""Tests for chat completion with TTS integration."""

import pytest

from l2dllm.config import Settings


class TestChatCompletionTTS:
    """Test TTS integration in chat completions (requires running server)."""

    @pytest.fixture(autouse=True)
    def setup_client(self, tts_settings: Settings):
        """Create test client with TTS enabled."""
        from fastapi.testclient import TestClient

        from l2dllm.agents.graph import build_agent_graph
        from l2dllm.llm.factory import build_chat_model
        from l2dllm.server import create_app
        from l2dllm.tools.registry import ToolRegistry

        model = build_chat_model(tts_settings)
        registry = ToolRegistry()
        graph = build_agent_graph(model, registry.all(), tts_settings.system_prompt, tts_settings)
        self.app = create_app(graph, tts_settings, {})
        self.client = TestClient(self.app)
        self.settings = tts_settings

    def test_chat_completion_with_tts(self):
        """Chat completion with tts=true should include audio in response."""
        response = self.client.post(
            "/v1/chat/completions",
            json={
                "model": "default",
                "messages": [{"role": "user", "content": "Say hello"}],
                "tts": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0

        choice = data["choices"][0]
        assert "message" in choice
        assert "audio" in choice
        assert choice["audio"] is not None
        assert len(choice["audio"]) > 0

    def test_chat_completion_without_tts(self):
        """Chat completion without tts should not include audio."""
        response = self.client.post(
            "/v1/chat/completions",
            json={
                "model": "default",
                "messages": [{"role": "user", "content": "Say hello"}],
            },
        )
        assert response.status_code == 200
        data = response.json()
        choice = data["choices"][0]
        assert choice.get("audio") is None
