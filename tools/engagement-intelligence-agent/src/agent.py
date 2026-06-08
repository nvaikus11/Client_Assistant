"""Engagement Intelligence Agent — core generation logic.

This is the single place that turns a client's engagement sources + a requested
output mode into a generated artifact. Both the CLI (`main.py`) and the Streamlit
UI call `generate_artifact()` so behavior stays identical across surfaces.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

# Make the repo root importable so `shared` resolves regardless of CWD.
# src/ -> agent/ -> tools/ -> <root>
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.claude_client import ClaudeClient  # noqa: E402
from shared.doc_parsing import Engagement, load_engagement  # noqa: E402
from shared.prompts import load_system_prompt  # noqa: E402

PROMPT_PATH = ROOT / "prompts" / "engagement-intelligence-agent-prompt.md"
CLIENTS_ROOT = ROOT / "clients"

# Output modes, mirroring the system prompt. Label -> mode token.
MODES: dict[str, str] = {
    "Default brief pack": "DEFAULT",
    "Engagement brief": "BRIEF",
    "Strategic framing": "FRAMING",
    "Talk track": "TALK TRACK",
    "Discovery questions": "DISCOVERY",
    "Prior-meeting recap": "RECAP",
    "Slide outline": "SLIDES",
    "Draft a named artifact": "ARTIFACT",
    "Risks & opportunities": "RISK/OPP",
    "Explain a concept (deep dive)": "DEEP DIVE",
}
VALID_MODES = set(MODES.values())


@dataclass
class GenerationResult:
    """Outcome of one generation run."""

    out_path: Path
    text: str
    mode: str
    input_tokens: int
    output_tokens: int
    model: str


def build_user_message(
    engagement: Engagement,
    *,
    objective: str | None,
    audience: str | None,
    mode: str,
    topic: str | None,
) -> str:
    """Assemble the user-turn message: sources, meeting meta, requested mode."""
    parts = [engagement.to_prompt(), "---", "## THIS MEETING"]

    meta = [
        f"OBJECTIVE: {objective}" if objective else "OBJECTIVE: (not provided)",
        f"AUDIENCE: {audience}" if audience else "AUDIENCE: (not provided)",
    ]
    if topic:
        meta.append(f"TOPIC / FOCUS: {topic}")
    parts.append("\n".join(meta))

    if mode == "DEFAULT":
        parts.append("OUTPUT MODE: DEFAULT — follow the prompt's default behavior.")
    else:
        parts.append(f"OUTPUT MODE: {mode} — produce this mode.")

    return "\n\n".join(parts)


def generate_artifact(
    *,
    client: str,
    mode: str = "DEFAULT",
    objective: str | None = None,
    audience: str | None = None,
    topic: str | None = None,
    model: str | None = None,
    max_tokens: int = 8000,
) -> GenerationResult:
    """Run the agent for one client and write the artifact to clients/<client>/outputs/.

    Fails loudly (raising) on unknown mode, missing client/docs, or missing API key.
    """
    mode = mode.strip().upper()
    if mode not in VALID_MODES:
        valid = ", ".join(sorted(VALID_MODES))
        raise ValueError(f"Unknown mode '{mode}'. Choose one of: {valid}.")

    engagement = load_engagement(CLIENTS_ROOT, client)
    system = load_system_prompt(PROMPT_PATH)
    user = build_user_message(
        engagement, objective=objective, audience=audience, mode=mode, topic=topic
    )

    cc = ClaudeClient(model=model)
    response = cc.complete(system=system, user=user, max_tokens=max_tokens)

    out_dir = CLIENTS_ROOT / client / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    slug = mode.lower().replace("/", "-").replace(" ", "-")
    out_path = out_dir / f"{stamp}-{slug}.md"
    out_path.write_text(response.text, encoding="utf-8")

    return GenerationResult(
        out_path=out_path,
        text=response.text,
        mode=mode,
        input_tokens=response.input_tokens,
        output_tokens=response.output_tokens,
        model=response.model,
    )
