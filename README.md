# L2dLLM

An OpenAI-compatible LLM backend with a switchable persona library and
LangGraph-powered tool calling. Designed to be plugged into any OpenAI client
(Open WebUI, LobeChat, the official `openai` SDK, …) as the model provider.

## Installation

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone git@github.com:Me9uru/L2dLLM.git
cd L2dLLM
uv sync
```

## Configuration

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your API key, model, base_url, etc.
```

Or set environment variables:

```bash
export L2DLLM_API_KEY="your-api-key"
# or OPENAI_API_KEY / ANTHROPIC_API_KEY
```

## Running the server

```bash
uv run l2dllm                          # 127.0.0.1:8000
uv run l2dllm --host 0.0.0.0 --port 9000
uv run l2dllm --config /path/to/config.yaml
uv run l2dllm --persona cat            # promote 'cat' to be the default model
```

The server exposes the OpenAI Chat Completions surface at `/v1`:

- `GET  /v1/models` — lists `default` plus one entry per persona.
- `POST /v1/chat/completions` — streaming (SSE) and non-streaming.

Each persona becomes a model id; selecting the model in your UI is how you
switch character.

## Personas

Drop markdown files under `./personas/`. Each is a YAML-frontmatter +
markdown-body card:

```markdown
---
name: cat
description: A playful cat-girl persona.
---

你是一只爱卖萌的猫娘，名叫小喵…
```

`name` must match `[A-Za-z0-9_-]+`. The body becomes the system prompt for that
model id. Two sample personas (`cat`, `assistant`) ship in `./personas/`.

## Skills

Drop markdown files under `./skills/` to expose them as on-demand tools the
model can call. Skills follow the same frontmatter shape as personas; calling
one returns its body as a tool result the model reads next turn.

## Connecting Open WebUI

In Open WebUI: **Admin → Settings → Connections → Add Connection** (OpenAI
type), set:

- **Base URL**: `http://localhost:8000/v1` (use `http://host.docker.internal:8000/v1`
  if Open WebUI runs in Docker).
- **API Key**: any string — the server doesn't validate it.

Hit the refresh icon and `default`, `cat`, `assistant`, … should appear in the
model dropdown.

## Quick smoke test

```bash
# list models
curl -s http://localhost:8000/v1/models | python -m json.tool

# non-streaming
curl -s http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"cat","messages":[{"role":"user","content":"你好"}]}' \
  | python -m json.tool

# streaming
curl --no-buffer -N http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"cat","messages":[{"role":"user","content":"你好"}],"stream":true}'
```

## Security note

The server has no built-in auth and defaults to binding on `127.0.0.1`. For
remote exposure, put it behind a reverse proxy (nginx, Caddy) with a token
check.

## Web frontend (dev)

A minimal Vite + Vue 3 chat UI lives in `web/`. It talks to this backend via
the OpenAI-compatible API — same protocol used for any other client.

```bash
# In a separate terminal, keep the backend running (uv run l2dllm).
cd web
npm install
npm run dev          # http://localhost:5173
```

Vite proxies `/v1/*` to `http://localhost:8000`, so the page picks up models
and streams responses without any CORS dance. This is the foundation for
Live2D + TTS work — the current build only does plain LLM chat.

## Development

```bash
uv sync --all-extras
uvx ruff check src/l2dllm/
uv run pytest
```
