"""Build a LangChain ChatModel from L2dLLM settings."""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from l2dllm.config import Settings


def build_chat_model(settings: Settings) -> BaseChatModel:
    """Construct a LangChain chat model for the configured provider.

    Tool binding is the caller's responsibility — call `.bind_tools(tools)`
    on the returned model when wiring up the agent graph.
    """
    if settings.provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        kwargs: dict = {
            "model": settings.model,
            "api_key": settings.api_key,
            "temperature": settings.temperature,
            "max_tokens": settings.max_tokens,
            "streaming": True,
        }
        if settings.base_url:
            kwargs["base_url"] = settings.base_url
        return ChatAnthropic(**kwargs)

    # default: openai-compatible
    from langchain_openai import ChatOpenAI

    kwargs = {
        "model": settings.model,
        "api_key": settings.api_key,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
        "streaming": True,
    }
    if settings.base_url:
        kwargs["base_url"] = settings.base_url
    return ChatOpenAI(**kwargs)
