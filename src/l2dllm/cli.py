"""CLI entry point using typer."""

from __future__ import annotations

from pathlib import Path

import typer

from l2dllm import __version__

app = typer.Typer(
    name="l2dllm",
    help="L2dLLM - OpenAI-compatible LLM backend for clients like Open WebUI / LobeChat",
    add_completion=False,
)


@app.command()
def main(
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
    config: str | None = typer.Option(None, "--config", "-c", help="Config file path"),
    persona: str | None = typer.Option(
        None,
        "--persona",
        "-p",
        help="Persona used by the 'default' model (overrides config)",
    ),
    host: str | None = typer.Option(None, "--host", help="HTTP bind host (default 127.0.0.1)"),
    port: int | None = typer.Option(None, "--port", help="HTTP bind port (default 8000)"),
    reload: bool = typer.Option(False, "--reload", help="Auto-reload on code change (dev)"),
) -> None:
    """Start the L2dLLM OpenAI-compatible HTTP server."""
    if version:
        print(f"l2dllm {__version__}")
        raise typer.Exit()

    import uvicorn

    from l2dllm.agents.graph import build_agent_graph
    from l2dllm.config import load_settings
    from l2dllm.llm.factory import build_chat_model
    from l2dllm.personas.loader import PersonaLoader
    from l2dllm.server import create_app
    from l2dllm.skills.as_tool import skill_to_tool
    from l2dllm.skills.loader import SkillLoader
    from l2dllm.tools.registry import ToolRegistry, load_all_tools

    settings = load_settings(config)

    if not settings.api_key:
        print("Error: No API key configured.")
        print("Set it in config.yaml or via L2DLLM_API_KEY environment variable.")
        raise typer.Exit(1)

    model = build_chat_model(settings)

    registry = ToolRegistry()
    registry.extend(load_all_tools())

    skills_dir = (
        Path(settings.skills_dir)
        if settings.skills_dir
        else Path.cwd() / "skills"
    )
    for skill in SkillLoader(skills_dir).load():
        registry.register(skill_to_tool(skill))

    personas_dir = (
        Path(settings.personas_dir)
        if settings.personas_dir
        else Path.cwd() / "personas"
    )
    personas_by_name = {p.name: p for p in PersonaLoader(personas_dir).load()}

    # --persona / settings.persona designates which persona the "default" model
    # serves. Unknown name = abort, to surface typos.
    active_name = (persona or settings.persona or "").strip()
    if active_name:
        if active_name not in personas_by_name:
            available = ", ".join(sorted(personas_by_name)) or "(none found)"
            print(f"Error: persona {active_name!r} not found in {personas_dir}.")
            print(f"Available: {available}")
            raise typer.Exit(1)
        # Promote the picked persona's body to settings.system_prompt so the
        # 'default' model id behaves like that persona.
        settings.system_prompt = personas_by_name[active_name].body

    graph = build_agent_graph(model, registry.all(), settings.system_prompt, settings)
    fastapi_app = create_app(graph, settings, personas_by_name)

    bind_host = host or settings.host
    bind_port = port if port is not None else settings.port
    print(f"L2dLLM serving on http://{bind_host}:{bind_port}/v1")
    print(f"Models: default, {', '.join(sorted(personas_by_name)) or '(no personas)'}")
    uvicorn.run(fastapi_app, host=bind_host, port=bind_port, reload=reload)
