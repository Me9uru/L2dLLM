"""Adapt a Skill into a LangChain tool."""

from __future__ import annotations

from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel

from l2dllm.skills.skill import Skill


class _NoArgs(BaseModel):
    """Empty argument schema — skills take no parameters when invoked."""


def skill_to_tool(skill: Skill) -> BaseTool:
    """Wrap a Skill so the LLM can call it as a regular tool.

    Calling the tool returns the skill's markdown body, which the model then
    reads on its next turn as a set of instructions to follow.
    """
    body = skill.body

    def _invoke() -> str:
        return body

    description = f"Invoke skill: {skill.name}. {skill.description}"

    return StructuredTool.from_function(
        func=_invoke,
        name=skill.name,
        description=description,
        args_schema=_NoArgs,
    )