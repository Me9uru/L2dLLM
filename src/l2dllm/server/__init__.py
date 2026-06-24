"""OpenAI-compatible HTTP server exposing the LangGraph agent.

The server speaks the OpenAI Chat Completions API so any OpenAI-compatible
client (Open WebUI, LobeChat, OpenAI SDK, etc.) can talk to L2dLLM as if it
were OpenAI itself. Each persona is published as a distinct model id.
"""

from l2dllm.server.app import create_app

__all__ = ["create_app"]
