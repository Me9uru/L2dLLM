"""Persona library — markdown-defined character prompts.

A Persona is a markdown file with YAML frontmatter (``name`` + ``description``)
whose body becomes the active ``SystemMessage`` for the conversation. Unlike
skills (which are on-demand tools), a persona is always on for as long as it's
the selected one.
"""

from l2dllm.personas.loader import PersonaLoader
from l2dllm.personas.persona import Persona, parse_persona_file

__all__ = ["Persona", "PersonaLoader", "parse_persona_file"]
