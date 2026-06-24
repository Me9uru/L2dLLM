"""Shell command execution tool."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from pydantic import BaseModel, Field

from l2dllm.tools.base import L2dTool


class ShellInput(BaseModel):
    """Input schema for shell command execution."""

    command: str = Field(description="The shell command to execute.")
    timeout: int = Field(
        default=30,
        description="Timeout in seconds for the command. Default is 30 seconds.",
    )
    cwd: str | None = Field(
        default=None,
        description="Working directory for command execution. Uses current directory if not specified.",
    )


class ShellTool(L2dTool):
    """Tool for executing shell commands."""

    @property
    def tool_name(self) -> str:
        return "shell"

    @property
    def tool_description(self) -> str:
        return (
            "Execute a shell command and return its output. "
            "Use this to run system commands, check file contents, "
            "install packages, or perform any terminal operations."
        )

    @property
    def input_schema(self) -> type[BaseModel]:
        return ShellInput

    async def _execute(
        self, command: str, timeout: int = 30, cwd: str | None = None, **kwargs: Any
    ) -> str:
        """Execute a shell command with timeout."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd or os.getcwd(),
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            output_parts = []
            if stdout:
                output_parts.append(f"STDOUT:\n{stdout.decode('utf-8', errors='replace')}")
            if stderr:
                output_parts.append(f"STDERR:\n{stderr.decode('utf-8', errors='replace')}")

            exit_code = process.returncode
            output_parts.append(f"EXIT_CODE: {exit_code}")

            return "\n\n".join(output_parts) if output_parts else "Command executed with no output."

        except asyncio.TimeoutError:
            return f"Error: Command timed out after {timeout} seconds."
        except Exception as e:
            return f"Error executing command: {type(e).__name__}: {e}"
