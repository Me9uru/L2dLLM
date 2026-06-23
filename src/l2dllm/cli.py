"""CLI entry point using typer."""

from __future__ import annotations

from pathlib import Path

import typer

from l2dllm import __version__

app = typer.Typer(
    name="l2dllm",
    help="L2dLLM - A minimal LLM chat client with TUI",
    add_completion=False,
)


@app.command()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
    config: str | None = typer.Option(None, "--config", "-c", help="Config file path"),
) -> None:
    """Start L2dLLM chat session."""
    if version:
        print(f"l2dllm {__version__}")
        raise typer.Exit()

    from l2dllm.agents.graph import build_agent_graph
    from l2dllm.config import load_settings
    from l2dllm.llm.factory import build_chat_model
    from l2dllm.skills.as_tool import skill_to_tool
    from l2dllm.skills.loader import SkillLoader
    from l2dllm.tools.registry import ToolRegistry, load_builtin_tools
    from l2dllm.tui.app import run_tui

    settings = load_settings(config)

    if not settings.api_key:
        print("Error: No API key configured.")
        print("Set it in config.yaml or via L2DLLM_API_KEY environment variable.")
        raise typer.Exit(1)

    model = build_chat_model(settings)

    registry = ToolRegistry()
    registry.extend(load_builtin_tools())

    skills_dir = (
        Path(settings.skills_dir)
        if settings.skills_dir
        else Path.cwd() / "skills"
    )
    for skill in SkillLoader(skills_dir).load():
        registry.register(skill_to_tool(skill))

    graph = build_agent_graph(model, registry.all(), settings.system_prompt)
    run_tui(graph, settings)