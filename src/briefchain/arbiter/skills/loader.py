"""Skill loading utilities for the Arbiter worker."""

from __future__ import annotations

from pathlib import Path

from google.adk.skills import load_skill_from_dir
from google.adk.skills.models import Skill

_SKILL_DIR = Path(__file__).parent.parent.parent / "skills" / "brief-review"


def load_brief_review_skill(skill_dir: Path | str | None = None) -> Skill:
    """Load the ``brief-review`` skill from disk using Google ADK.

    Args:
        skill_dir: Optional override path to the skill directory. Defaults to
            ``src/briefchain/skills/brief-review``.

    Returns:
        A Google ADK ``Skill`` object containing the frontmatter and instructions.
    """
    directory = Path(skill_dir) if skill_dir is not None else _SKILL_DIR
    return load_skill_from_dir(directory)
