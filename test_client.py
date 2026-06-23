"""Quick test for LLM client connectivity."""

import asyncio
from l2dllm.config import load_settings
from l2dllm.llm.client import create_client
from l2dllm.llm import Message


async def main():
    settings = load_settings()
    print(f"Provider: {settings.provider}")
    print(f"Base URL: {settings.base_url}")
    print(f"Model: {settings.model}")
    print(f"API key: {settings.api_key[:8]}...")
    print()

    client = create_client(settings)
    messages = [Message(role="user", content="Say hi in one sentence.")]

    print("Streaming response:")
    full = []
    try:
        async for chunk in client.stream_chat(messages=messages):
            print(chunk, end="", flush=True)
            full.append(chunk)
    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        return

    print(f"\n\nTotal length: {len(''.join(full))}")


if __name__ == "__main__":
    asyncio.run(main())
