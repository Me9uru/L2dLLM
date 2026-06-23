"""Textual TUI application for L2dLLM chat."""

from __future__ import annotations

import json

from langchain_core.messages import BaseMessage, HumanMessage
from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header, Input, RichLog, Static


_TOOL_RESULT_PREVIEW_LIMIT = 200


class L2dLLMApp(App[None]):
    """L2dLLM chat application."""

    TITLE = "L2dLLM"
    CSS = """
    Screen {
        layout: vertical;
    }

    #transcript {
        height: 1fr;
        border: solid $accent;
    }

    #current-response {
        min-height: 3;
        max-height: 8;
        border: round $primary;
        padding: 0 1;
    }

    #composer {
        dock: bottom;
        height: 3;
        border: solid $accent;
    }
    """

    BINDINGS = [
        Binding("ctrl+l", "clear_conversation", "Clear"),
        Binding("ctrl+d", "quit_session", "Exit"),
    ]

    def __init__(self, graph, settings) -> None:
        super().__init__()
        self._graph = graph
        self._settings = settings
        self._lc_messages: list[BaseMessage] = []
        self._assistant_buffer: str = ""
        self._busy: bool = False
        self._last_current_response: object | None = None

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield RichLog(id="transcript", wrap=True, highlight=True, markup=True)
        yield Static("Ready.", id="current-response")
        yield Input(placeholder="Type your message... (Enter to send)", id="composer")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one("#composer", Input).focus()

    @on(Input.Submitted, "#composer")
    async def handle_submit(self, event: Input.Submitted) -> None:
        line = event.value
        event.input.value = ""
        await self._process_line(line)

    async def _process_line(self, line: str) -> None:
        if not line.strip() or self._busy:
            return
        self._busy = True
        composer = self.query_one("#composer", Input)
        composer.disabled = True
        self._append_line(Text.from_markup(f"[bold cyan]user>[/bold cyan] {line}"))
        self._set_current_response("[dim]Working...[/dim]")
        self._lc_messages.append(HumanMessage(content=line))
        self._assistant_buffer = ""

        final_state: dict | None = None
        try:
            async for event in self._graph.astream_events(
                {"messages": self._lc_messages},
                version="v2",
                config={"recursion_limit": self._settings.max_iterations},
            ):
                ev_type = event["event"]
                if ev_type == "on_chat_model_stream":
                    chunk = event["data"].get("chunk")
                    delta = _extract_text(chunk) if chunk is not None else ""
                    if delta:
                        self._assistant_buffer += delta
                        self._set_current_response(
                            Group(
                                Text.from_markup("[bold]assistant>[/bold]"),
                                Markdown(self._assistant_buffer),
                            )
                        )
                elif ev_type == "on_chat_model_end":
                    # An LLM turn just finished — settle whatever it streamed
                    # into the transcript before tools run or the next turn
                    # starts.
                    self._flush_assistant_buffer()
                elif ev_type == "on_tool_start":
                    name = event.get("name", "?")
                    raw_input = event["data"].get("input", {})
                    args_repr = _format_tool_args(raw_input)
                    self._append_line(
                        Text.from_markup(
                            f"[bold magenta]tool>[/bold magenta] {name}({args_repr})"
                        )
                    )
                elif ev_type == "on_tool_end":
                    output = event["data"].get("output")
                    preview = _format_tool_result(output)
                    self._append_line(
                        Text.from_markup(f"[dim]      → {preview}[/dim]")
                    )
                elif ev_type == "on_chain_end":
                    output = event["data"].get("output")
                    if isinstance(output, dict) and "messages" in output:
                        final_state = output

            # Flush whatever assistant text is left after the run completes.
            self._flush_assistant_buffer()

            # Sync the final message list back from graph state — this keeps
            # tool messages and AI tool_call messages in our history so the
            # next turn has full context.
            if final_state and isinstance(final_state.get("messages"), list):
                self._lc_messages = list(final_state["messages"])
            elif self._assistant_buffer.strip():
                # Fallback: at least preserve the final assistant reply.
                from langchain_core.messages import AIMessage

                self._lc_messages.append(AIMessage(content=self._assistant_buffer))

            self._set_current_response("Ready.")
        except Exception as exc:  # noqa: BLE001
            self._append_line(Text.from_markup(f"[bold red]error>[/bold red] {exc}"))
            self._assistant_buffer = ""
            self._set_current_response("Ready.")
        finally:
            self._busy = False
            composer.disabled = False
            composer.focus()

    def _flush_assistant_buffer(self) -> None:
        """Append the current assistant buffer to the transcript as a settled turn."""
        text = self._assistant_buffer
        if not text.strip():
            self._assistant_buffer = ""
            return
        self._append_line(
            Group(
                Text.from_markup("[bold green]assistant>[/bold green]"),
                Markdown(text),
            )
        )
        self._assistant_buffer = ""

    def action_clear_conversation(self) -> None:
        self.query_one("#transcript", RichLog).clear()
        self._lc_messages.clear()
        self._assistant_buffer = ""
        self._set_current_response("Conversation cleared.")

    def action_quit_session(self) -> None:
        self.exit()

    def _append_line(self, message) -> None:
        self.query_one("#transcript", RichLog).write(message)

    def _set_current_response(self, message) -> None:
        if message is self._last_current_response:
            return
        self.query_one("#current-response", Static).update(message)
        self._last_current_response = message


def _extract_text(chunk) -> str:
    """Pull plain text out of a LangChain chat chunk, ignoring tool-call deltas."""
    content = getattr(chunk, "content", None)
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    # Anthropic and some others yield a list of content blocks.
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text" and isinstance(block.get("text"), str):
                    parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(content)


def _format_tool_args(raw) -> str:
    """Render tool call arguments as a short readable string."""
    if not raw:
        return ""
    try:
        if isinstance(raw, dict):
            return ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in raw.items())
        return json.dumps(raw, ensure_ascii=False)
    except (TypeError, ValueError):
        return repr(raw)


def _format_tool_result(output) -> str:
    """Render a tool result for transcript display, truncating if needed."""
    if output is None:
        text = ""
    elif isinstance(output, str):
        text = output
    else:
        # ToolMessage or similar — pull .content if available.
        content = getattr(output, "content", None)
        text = content if isinstance(content, str) else str(output)

    text = text.replace("\n", " ⏎ ")
    if len(text) > _TOOL_RESULT_PREVIEW_LIMIT:
        text = text[:_TOOL_RESULT_PREVIEW_LIMIT] + "…"
    return text


def run_tui(graph, settings) -> None:
    """Run the TUI application."""
    app = L2dLLMApp(graph, settings)
    app.run()