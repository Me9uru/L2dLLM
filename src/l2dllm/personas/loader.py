"""Discover personas on disk.

Layout matches :class:`l2dllm.skills.loader.SkillLoader`: either flat
``personas/<name>.md`` files or nested ``personas/<name>/PERSONA.md``.
Malformed files are skipped with a warning rather than aborting startup.
"""

from __future__ import annotations

import logging
from pathlib import Path

from l2dllm.personas.persona import Persona, parse_persona_file

log = logging.getLogger(__name__)


class PersonaLoader:
    """Scan a directory tree for persona definitions."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def load(self) -> list[Persona]:
        """Return all personas found under ``self.root``.

        Missing directory → empty list. Name conflicts → later wins, warn.
        Malformed files are logged and skipped rather than aborting.
        """
        if not self.root.exists():
            return []

        candidates: list[Path] = sorted(self.root.glob("**/PERSONA.md"))
        # Also accept flat layout: <root>/<name>.md
        for md in sorted(self.root.glob("*.md")):
            if md.name != "PERSONA.md":
                candidates.append(md)

        seen: dict[str, Persona] = {}
        for path in candidates:
            try:
                persona = parse_persona_file(path)
            except ValueError as exc:
                log.warning("skipping persona %s: %s", path, exc)
                continue
            if persona.name in seen:
                log.warning(
                    "persona name conflict: %r at %s overrides %s",
                    persona.name,
                    path,
                    seen[persona.name].path,
                )
            seen[persona.name] = persona

        return list(seen.values())
