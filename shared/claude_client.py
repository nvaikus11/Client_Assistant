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

    def _params(
        self,
        *,
        system: str,
        messages: list[dict],
        max_tokens: int,
        temperature: float | None,
        model: str | None,
    ) -> dict:
        """Build the Messages API kwargs, omitting temperature by default.

        The pinned model (Opus 4.8) removed the sampling parameters and returns a
        400 if `temperature`/`top_p`/`top_k` are sent. We include `temperature`
        only when a caller explicitly sets one (e.g. for an older model).
        """
        params: dict = {
            "model": model or self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if temperature is not None:
            params["temperature"] = temperature
        return params

    def chat(
        self,
        *,
        system: str,
        messages: list[dict],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float | None = None,
        model: str | None = None,
    ) -> ClaudeResponse:
        """Run a multi-turn (or single-turn) completion and return text + usage.

        `messages` is the full conversation history as a list of
        `{"role": ..., "content": ...}` dicts (the API is stateless — send it all
        each turn). The first message must be `user`.
        """
        if not system.strip():
            raise ValueError("system prompt is empty — load it from prompts/.")
        if not messages:
            raise ValueError("messages is empty — nothing to send to the model.")

        params = self._params(
            system=system, messages=messages, max_tokens=max_tokens,
            temperature=temperature, model=model,
        )
        try:
            message = self._client.messages.create(**params)
        except anthropic.APIError as exc:  # rate limit, overloaded, auth, etc.
            raise RuntimeError(f"Anthropic API call failed: {exc}") from exc

        text = "".join(b.text for b in message.content if b.type == "text")
        return ClaudeResponse(
            text=text,
            model=message.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            stop_reason=message.stop_reason,
        )

    def stream_chat(
        self,
        *,
        system: str,
        messages: list[dict],
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float | None = None,
        model: str | None = None,
    ) -> "ChatStream":
        """Stream a multi-turn completion. Returns an iterable of text chunks.

        Iterate it to consume text deltas (e.g. Streamlit's `st.write_stream`);
        after iteration completes, `.response` holds the final ClaudeResponse
        (text + token usage). Streaming avoids HTTP timeouts on long inputs/outputs.
        """
        if not system.strip():
            raise ValueError("system prompt is empty — load it from prompts/.")
        if not messages:
            raise ValueError("messages is empty — nothing to send to the model.")

        params = self._params(
            system=system, messages=messages, max_tokens=max_tokens,
            temperature=temperature, model=model,
        )
        return ChatStream(self._client, params)

    def complete(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float | None = None,
        model: str | None = None,
    ) -> ClaudeResponse:
        """Single-turn convenience wrapper over `chat()` (used by the CLI)."""
        if not user.strip():
            raise ValueError("user content is empty — nothing to send to the model.")
        return self.chat(
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
        )


class ChatStream:
    """An iterable of text chunks from a streamed completion.

    Iterate to consume text deltas; after the iterator is exhausted, `.response`
    holds the final ClaudeResponse (text + token usage). Designed to plug into
    Streamlit's `st.write_stream`, which iterates it and returns the joined text.
    """

    def __init__(self, client: "anthropic.Anthropic", params: dict) -> None:
        self._client = client
        self._params = params
        self.response: ClaudeResponse | None = None

    def __iter__(self):
        try:
            with self._client.messages.stream(**self._params) as stream:
                for text in stream.text_stream:
                    yield text
                final = stream.get_final_message()
        except anthropic.APIError as exc:  # rate limit, overloaded, auth, etc.
            raise RuntimeError(f"Anthropic API call failed: {exc}") from exc

        text = "".join(b.text for b in final.content if b.type == "text")
        self.response = ClaudeResponse(
            text=text,
            model=final.model,
            input_tokens=final.usage.input_tokens,
            output_tokens=final.usage.output_tokens,
            stop_reason=final.stop_reason,
        )
