# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

L2dLLM is a minimal LLM chat client with a Textual TUI, featuring an agentic loop built on LangGraph. It uses LangChain ChatModel (ChatOpenAI / ChatAnthropic) for LLM access and supports tool calling and Claude-Code-style markdown skills.

## Project commands

```bash
uv sync                                    # Install all dependencies
uv run l2dllm                              # Launch the chat TUI
uv run l2dllm --config /path/to/config.yaml
uv run python -m l2dllm                    # Run as module
uvx ruff check src/l2dllm/                 # Lint
uv run pytest                              # Run tests (if any exist)
```

Configuration: copy `config.example.yaml` → `config.yaml`, set `api_key`. Alternatively, set `L2DLLM_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` env vars.

## Architecture

The project lives under `src/l2dllm/` with the following package structure:

### Entry point

**`cli.py`** — Typer CLI. Constructs the LangGraph agent and passes it to the TUI:

1. `build_chat_model(settings)` → LangChain `BaseChatModel`
2. `ToolRegistry` collects built-in tools + markdown skills from `./skills/`
3. `build_agent_graph(model, tools, system_prompt)` → compiled `StateGraph`
4. `run_tui(graph, settings)` — starts the Textual app with the graph

### `llm/` — LLM integration

- `factory.py` — `build_chat_model(settings)`: constructs `ChatOpenAI` or `ChatAnthropic` from config
- `__init__.py` — legacy `Message` dataclass for backward compat

### `tools/` — Tool system

- `registry.py` — `ToolRegistry`: mutable collection of LangChain `BaseTool` objects
- `builtin.py` — built-in demo tools (`get_time`, `echo`) using `@tool` decorator
- To add tools: create a function with `@tool` decorator and register it

### `skills/` — Markdown skills

- `skill.py` — `Skill` dataclass + `parse_skill_file()`: parses frontmatter (`name`, `description`, `allowed-tools`) + markdown body from SKILL.md
- `loader.py` — `SkillLoader`: scans a directory for `**/SKILL.md` or `*.md` files
- `as_tool.py` — `skill_to_tool()`: wraps a `Skill` into a `StructuredTool` that returns the skill body when called by the LLM
- Skills live in `./skills/<name>/SKILL.md` (project directory), configured via `settings.skills_dir`

### `agents/` — LangGraph agent loop

- `state.py` — `AgentState(MessagesState)`: message list with `add_messages` reducer
- `nodes.py` — `agent_node()` (calls ChatModel), `build_tool_node()` (LangGraph ToolNode), `route_after_agent` (conditional edge: if tool_calls → "tools", else → END)
- `graph.py` — `build_agent_graph()`: hand-written `StateGraph`:

```
agent →─ has tool_calls? ──→ tools →─→ agent
         └─ no tool_calls ─→ END
```

### `tui/` — Textual chat UI

- `app.py` — `L2dLLMApp(App[None])`: RichLog transcript + Static current-response panel + Input composer
- Uses `graph.astream_events(version="v2")` for streaming: `on_chat_model_stream` (text deltas to `current-response`), `on_chat_model_end` (flush to transcript), `on_tool_start` / `on_tool_end` (tool call logs to transcript)
- `run_tui(graph, settings)` — entry point called from `cli.py`

### `config.py` — Settings

`Settings(BaseModel)` with fields: `provider`, `api_key`, `base_url`, `model`, `system_prompt`, `max_tokens`, `temperature`, `skills_dir`, `max_iterations`.

Loads from `./config.yaml`, `~/.config/l2dllm/config.yaml`, or env vars.

## Key data flow

```
User input → TUI (_process_line)
  → HumanMessage appended to _lc_messages
  → graph.astream_events({"messages": _lc_messages})
    → agent_node calls .ainvoke() on ChatModel
    → if tool_calls → ToolNode executes → agent_node loops
    → if no tool_calls → END
  → Events streamed back to TUI for rendering
  → Final messages synced back to _lc_messages for next turn
```

## Tool vs Skill

- **Tools** are Python functions (`@tool` decorator) the model can call directly — stateless, synchronous operations
- **Skills** are markdown files with frontmatter metadata, exposed as tools — calling a skill returns instruction text for the LLM to follow on its next turn