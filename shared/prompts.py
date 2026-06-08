"""Load canonical system prompts from `prompts/<tool-name>-prompt.md`.

Why this exists: prompt files in this workspace are human-readable Markdown that
wrap the actual prompt in a fenced ``` block, surrounded by usage notes and
rationale (see prompts/engagement-intelligence-agent-prompt.md). Tools must send
the *prompt itself* to the model, not the surrounding commentary — so extraction
lives here, shared, rather than being re-implemented per tool.
"""

from __future__ import annotations

import re
from pathlib import Path

# First fenced code block: ```[lang]\n ... \n```
_FENCE = re.compile(r"```[^\n]*\n(.*?)\n```", re.DOTALL)


def load_system_prompt(path: Path) -> str:
    """Return the system prompt text from a prompt Markdown file.

    If the file contains a fenced code block, return the first one's contents
    (the canonical prompt). Otherwise return the whole file. Raises if the file
    is missing or empty — a tool must never run on a blank prompt.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {path}. System prompts live in prompts/."
        )

    raw = path.read_text(encoding="utf-8")
    match = _FENCE.search(raw)
    prompt = match.group(1) if match else raw

    prompt = prompt.strip()
    if not prompt:
        raise ValueError(f"Prompt file is empty: {path}.")
    return prompt
