"""Quick test for LLM client connectivity."""

import pytest

from l2dllm.config import Settings
from l2dllm.llm.factory import build_chat_model


class TestLLMConnectivity:
    """Verify LLM service is reachable."""

    def test_build_model(self, settings: Settings):
        """Should build a chat model from settings."""
        model = build_chat_model(settings)
        assert model is not None

    @pytest.mark.asyncio
    async def test_model_invoke(self, settings: Settings):
        """Model should respond to a simple prompt."""
        model = build_chat_model(settings)
        from langchain_core.messages import HumanMessage

        response = await model.ainvoke([HumanMessage(content="Say hi in one word.")])
        assert response.content
        assert len(response.content) > 0
