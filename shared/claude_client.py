"""Single Anthropic API wrapper shared by every tool in this workspace.

Why this exists: the workspace constitution (CLAUDE.md) requires that all
API-calling logic live in `shared/` and that tools import it rather than each
constructing their own client. This keeps model choice, key handling, and error
behavior consistent — and keeps us locked to the Anthropic API only.

Usage:
    from shared.claude_client import ClaudeClient

    client = ClaudeClient()
    reply = client.complete(
        system=Path("prompts/engagement-intelligence-agent-prompt.md").read_text(),
        user="...document text...",
    )
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

try:  # Fail loudly with a helpful message if the SDK isn't installed.
    import anthropic
except ModuleNotFoundError as exc:  # pragma: no cover - import guard
    raise ModuleNotFoundError(
        "The 'anthropic' package is required. Install deps with "
        "`pip install -r requirements.txt`."
    ) from exc


# Conservative default; override per call or via the ANTHROPIC_MODEL env var.
DEFAULT_MODEL = "claude-opus-4-8"
DEFAULT_MAX_TOKENS = 4096


@dataclass
class ClaudeResponse:
    """A model reply plus the metadata a caller usually wants."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    stop_reason: str | None


class ClaudeClient:
    """Thin, opinionated wrapper around the Anthropic Messages API.

    The key is read once from the environment (loaded from `.env`). We raise
    immediately if it is missing rather than letting a confusing error surface
    deep inside an API call.
    """

    def __init__(self, model: str | None = None) -> None:
        load_dotenv()  # no-op if there's no .env; real env vars still win

        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Add it to your .env file "
                "(see .env.example). The workspace never hardcodes keys."
            )

        self.model = model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
        self._client = anthropic.Anthropic(api_key=api_key)

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = 0.2,
        model: str | None = None,
    ) -> ClaudeResponse:
        """Run a single-turn completion and return the text plus usage.

        `system` is the canonical prompt (load it from `prompts/`); `user` is the
        content to act on (e.g. concatenated document text). Temperature defaults
        low because these tools value faithful, grounded output over creativity.
        """
        if not system.strip():
            raise ValueError("system prompt is empty — load it from prompts/.")
        if not user.strip():
            raise ValueError("user content is empty — nothing to send to the model.")

        try:
            message = self._client.messages.create(
                model=model or self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except anthropic.APIError as exc:  # rate limit, overloaded, auth, etc.
            raise RuntimeError(f"Anthropic API call failed: {exc}") from exc

        text = "".join(
            block.text for block in message.content if block.type == "text"
        )
        return ClaudeResponse(
            text=text,
            model=message.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            stop_reason=message.stop_reason,
        )
