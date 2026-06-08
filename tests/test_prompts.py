"""Tests for shared.prompts — system-prompt loading.

The canonical prompt files wrap the real prompt in a fenced ``` block surrounded
by commentary. The loader must return only the prompt, never the commentary.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shared.prompts import load_system_prompt

ROOT = Path(__file__).resolve().parents[1]


def test_extracts_only_the_fenced_block(tmp_path: Path):
    md = tmp_path / "p.md"
    md.write_text(
        "# Title\n\nSome commentary.\n\n```\nYOU ARE THE PROMPT\n```\n\n## How to use\nblah\n"
    )
    prompt = load_system_prompt(md)
    assert prompt == "YOU ARE THE PROMPT"
    assert "commentary" not in prompt
    assert "How to use" not in prompt


def test_returns_whole_file_when_no_fence(tmp_path: Path):
    md = tmp_path / "p.md"
    md.write_text("just a plain prompt, no fences")
    assert load_system_prompt(md) == "just a plain prompt, no fences"


def test_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_system_prompt(tmp_path / "nope.md")


def test_empty_file_raises(tmp_path: Path):
    md = tmp_path / "empty.md"
    md.write_text("   \n  ")
    with pytest.raises(ValueError):
        load_system_prompt(md)


def test_real_engagement_prompt_loads_and_is_clean():
    """The shipped prompt loads, and its commentary is excluded."""
    prompt = load_system_prompt(ROOT / "prompts" / "engagement-intelligence-agent-prompt.md")
    assert prompt.startswith("<role>")
    assert "How to use it" not in prompt  # commentary, must be excluded
    assert len(prompt) > 500
