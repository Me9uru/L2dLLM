# AGENTS.md

## What is this project

L2dLLM: OpenAI-compatible LLM backend with persona library and LangGraph tool calling. Plugs into Open WebUI, LobeChat, or any OpenAI client.

## Quick start

```bash
uv sync                                    # Install dependencies
cp config.example.yaml config.yaml         # Set api_key in config.yaml
uv run l2dllm                              # Start server at 127.0.0.1:8000
```

## Key commands

| Task | Command |
|------|---------|
| Lint | `uvx ruff check src/l2dllm/` |
| Test | `uv run pytest` |
| Start server | `uv run l2dllm [--host 0.0.0.0 --port 9000]` |
| With persona | `uv run l2dllm --persona cat` |

Config search: `./config.yaml` → `~/.config/l2dllm/config.yaml` → env vars (`L2DLLM_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`).

## Architecture

```
CLI (cli.py) → FastAPI server (server/app.py) → LangGraph agent (agents/graph.py) → LangChain model
```

- **Personas** (`personas/*.md`): YAML frontmatter + markdown body → exposed as model IDs in `/v1/models`
- **Skills** (`skills/*.md`): Markdown files with frontmatter → wrapped as LangChain tools via `skill_to_tool()`
- **Tools** (`tools/builtin.py`): Python functions with `@tool` decorator

## API surface

- `GET /v1/models` — lists `default` + persona model IDs
- `POST /v1/chat/completions` — streaming (SSE) and non-streaming

Selecting a model ID in your client switches persona. Unknown model IDs fall back to `default`.

## Web frontend

Vue 3 + Vite app in `web/`. Separate dev server:

```bash
cd web && npm install && npm run dev  # http://localhost:5173
```

Vite proxies `/v1/*` to `localhost:8000`.

## Gotchas

- Server has no auth — put behind reverse proxy for remote access
- System prompt is always prepended; duplicate system messages from clients are filtered out
- Graph recursion limit: `settings.max_iterations` (default 10)
