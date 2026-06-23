"""Discover skills on disk."""

from __future__ import annotations

import logging
from pathlib import Path

from l2dllm.skills.skill import Skill, parse_skill_file

log = logging.getLogger(__name__)


class SkillLoader:
    """Scan a directory tree for SKILL.md files (or top-level .md files)."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def load(self) -> list[Skill]:
        """Return all skills found under `self.root`.

        Missing directory → empty list.  Skill-name conflicts → later wins, warn.
        Malformed files are skipped with a warning rather than aborting load.
        """
        if not self.root.exists():
            return []

        candidates: list[Path] = sorted(self.root.glob("**/SKILL.md"))
        # also accept flat layout: <root>/<name>.md
        for md in sorted(self.root.glob("*.md")):
            if md.name != "SKILL.md":
                candidates.append(md)

        seen: dict[str, Skill] = {}
        for path in candidates:
            try:
                skill = parse_skill_file(path)
            except ValueError as exc:
                log.warning("skipping skill %s: %s", path, exc)
                continue
            if skill.name in seen:
                log.warning(
                    "skill name conflict: %r at %s overrides %s",
                    skill.name,
                    path,
                    seen[skill.name].path,
                )
            seen[skill.name] = skill

        return list(seen.values())