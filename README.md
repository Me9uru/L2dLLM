# L2dLLM

A minimal LLM chat client with TUI, supporting OpenAI and Anthropic APIs.

## Installation

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url> L2dLLM
cd L2dLLM
uv sync
```

## Configuration

Copy the example config and fill in your API key:

```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your API key
```

Or set environment variables:

```bash
export L2DLLM_API_KEY="your-api-key"
# or
export OPENAI_API_KEY="your-api-key"
```

## Usage

```bash
uv run l2dllm
```

Or with a specific config file:

```bash
uv run l2dllm --config /path/to/config.yaml
```

Or run as a module:

```bash
uv run python -m l2dllm
```

## Features

- Streaming LLM responses
- Support for OpenAI and Anthropic APIs
- Textual TUI with Markdown rendering
- Simple YAML configuration

## Development

```bash
uv sync --all-extras   # install dev dependencies (pytest, ruff)
uv run ruff check .     # lint
uv run pytest           # test
```
