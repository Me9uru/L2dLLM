"""Skill data model and frontmatter parser."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Skill:
    """A Claude-Code-style markdown skill.

    The body is what gets returned to the LLM when the skill is invoked — it
    should read as instructions the model can follow on its next turn.
    """

    name: str
    description: str
    body: str
    path: Path
    allowed_tools: list[str] | None = field(default=None)


def parse_skill_file(path: Path) -> Skill:
    """Parse a SKILL.md file with YAML frontmatter.

    Expected shape:

        ---
        name: greeter
        description: ...
        allowed-tools: [foo, bar]   # optional
        ---
        <body markdown ...>

    Raises ValueError on malformed frontmatter or missing required fields.
    """
    raw = path.read_text(encoding="utf-8")

    if not raw.startswith("---"):
        raise ValueError(f"{path}: missing '---' frontmatter delimiter at start of file")

    # Split off the frontmatter block — between the first two `---` lines.
    parts = raw.split("\n---", 1)
    if len(parts) != 2:
        raise ValueError(f"{path}: no closing '---' delimiter for frontmatter")
    fm_text = parts[0].lstrip("-").lstrip("\n")
    body = parts[1].lstrip("\n")

    try:
        meta = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: invalid YAML frontmatter — {exc}") from exc

    name = meta.get("name")
    description = meta.get("description")
    if not name or not description:
        raise ValueError(f"{path}: frontmatter must declare both 'name' and 'description'")

    allowed = meta.get("allowed-tools") or meta.get("allowed_tools")
    if allowed is not None and not isinstance(allowed, list):
        raise ValueError(f"{path}: 'allowed-tools' must be a list of tool names")

    return Skill(
        name=str(name),
        description=str(description),
        body=body,
        path=path,
        allowed_tools=allowed,
    )