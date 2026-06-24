"""Persona data model and frontmatter parser.

The on-disk shape mirrors :mod:`l2dllm.skills.skill` deliberately — same YAML
frontmatter, same body-after-``---`` layout — but a Persona is semantically
different: its body becomes a ``SystemMessage`` injected for the whole
conversation, not a tool result returned on demand. We keep the types
separate so this difference stays visible in the code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml


# Persona names get typed into the TUI as `/persona <name>` — disallow anything
# that would make tokenization ambiguous (spaces, slashes, quotes…).
_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass
class Persona:
    """A character/role definition loaded from a markdown file.

    ``body`` is the verbatim system prompt — what the model is told to be.
    """

    name: str
    description: str
    body: str
    path: Path


def parse_persona_file(path: Path) -> Persona:
    """Parse a persona markdown file with YAML frontmatter.

    Expected shape::

        ---
        name: cat
        description: A playful cat-girl persona.
        ---
        你是一只爱卖萌的猫娘…

    Raises ``ValueError`` on malformed frontmatter, missing required fields,
    invalid ``name`` characters, or an empty body. The body must be non-empty —
    an empty ``SystemMessage`` is worse than no system message at all.
    """
    raw = path.read_text(encoding="utf-8")

    if not raw.startswith("---"):
        raise ValueError(f"{path}: missing '---' frontmatter delimiter at start of file")

    parts = raw.split("\n---", 1)
    if len(parts) != 2:
        raise ValueError(f"{path}: no closing '---' delimiter for frontmatter")
    fm_text = parts[0].lstrip("-").lstrip("\n")
    body = parts[1].lstrip("\n").rstrip()

    try:
        meta = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"{path}: invalid YAML frontmatter — {exc}") from exc

    name = meta.get("name")
    description = meta.get("description")
    if not name or not description:
        raise ValueError(f"{path}: frontmatter must declare both 'name' and 'description'")

    name = str(name)
    if not _NAME_RE.match(name):
        raise ValueError(
            f"{path}: persona name {name!r} must match [A-Za-z0-9_-]+ "
            "(no spaces, so /persona <name> stays unambiguous)"
        )

    if not body:
        raise ValueError(f"{path}: persona body is empty — nothing to use as system prompt")

    return Persona(
        name=name,
        description=str(description),
        body=body,
        path=path,
    )
