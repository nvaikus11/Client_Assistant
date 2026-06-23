"""Single Claude wrapper shared by every tool in this workspace.

Why this exists: the workspace constitution (CLAUDE.md) requires that all
model-calling logic live in `shared/` and that tools import it rather than each
constructing their own client. This keeps model choice, key handling, and error
behavior consistent.

Two backends, same interface:
- **api** — the Anthropic API/SDK (`anthropic`). Used when `ANTHROPIC_API_KEY` is set.
- **cli** — the local `claude` command (Claude Code). Used when there is no API key
  but the `claude` CLI is installed. This runs on your existing Claude Code login /
  enterprise license — no API key and no metered API billing.

The backend is auto-detected (override with `EIA_BACKEND=api|cli`). Both are Claude;
the CLI path is the Anthropic Claude Code tool, not a third-party provider.

Usage:
    from shared.claude_client import ClaudeClient
    reply = ClaudeClient().complete(system=PROMPT, user="...document text...")
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
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

# Our pinned model ids -> Claude Code CLI aliases (`claude --model <alias>`).
# Aliases are robust across CLI versions/licenses; unknown ids are passed through.
_CLI_MODEL_ALIAS = {
    "claude-opus-4-8": "opus",
    "claude-opus-4-7": "opus",
    "claude-sonnet-4-6": "sonnet",
    "claude-haiku-4-5": "haiku",
}


def detect_backend() -> tuple[str | None, str]:
    """Decide which backend to use from the environment, without constructing it.

    Returns (backend, human-readable reason). backend is "api", "cli", or None
    (nothing usable). Callers should `load_dotenv()` first. Override with
    `EIA_BACKEND=api|cli`.
    """
    mode = os.environ.get("EIA_BACKEND", "auto").strip().lower()
    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_cli = shutil.which("claude") is not None

    if mode == "api":
        return ("api", "Anthropic API (forced via EIA_BACKEND)") if has_key \
            else (None, "EIA_BACKEND=api but ANTHROPIC_API_KEY is not set")
    if mode == "cli":
        return ("cli", "Claude Code CLI (forced via EIA_BACKEND)") if has_cli \
            else (None, "EIA_BACKEND=cli but the `claude` CLI was not found on PATH")

    # auto: prefer the API when a key is present, else fall back to the CLI.
    if has_key:
        return "api", "Anthropic API (ANTHROPIC_API_KEY found)"
    if has_cli:
        return "cli", "Claude Code CLI (no API key — using your Claude Code login)"
    return None, "no ANTHROPIC_API_KEY and no `claude` CLI found"


@dataclass
class ClaudeResponse:
    """A model reply plus the metadata a caller usually wants."""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    stop_reason: str | None


def _render_cli_prompt(system: str, messages: list[dict]) -> str:
    """Flatten system + conversation into a single prompt for `claude -p`.

    The CLI is invoked statelessly per turn, so we render the whole conversation
    each time (same as the API's stateless model).
    """
    parts = [system.strip()]
    if len(messages) == 1 and messages[0].get("role") == "user":
        parts.append("\n\n---\n")
        parts.append(messages[0]["content"])
    else:
        parts.append(
            "\n\n---\nBelow is the conversation so far. Write ONLY the assistant's "
            "next reply — no role labels, no preamble.\n"
        )
        for m in messages:
            label = "USER" if m.get("role") == "user" else "ASSISTANT"
            parts.append(f"\n[{label}]\n{m.get('content', '')}")
        parts.append("\n[ASSISTANT]\n")
    return "\n".join(parts)


class ClaudeClient:
    """Backend-agnostic Claude wrapper. Picks the API or the `claude` CLI."""

    def __init__(self, model: str | None = None) -> None:
        load_dotenv()  # no-op if there's no .env; real env vars still win

        backend, reason = detect_backend()
        if backend is None:
            raise RuntimeError(
                f"No Claude backend available: {reason}. Either add ANTHROPIC_API_KEY "
                "to your .env, or install Claude Code (`claude`) to run without an API "
                "key. Force one with EIA_BACKEND=api|cli."
            )

        self.backend = backend
        self.reason = reason
        self.model = model or os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL)
        self._client: anthropic.Anthropic | None = None
        self._cli: str | None = None
        if backend == "api":
            self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        else:
            self._cli = shutil.which("claude")

    # --- shared param builder (API) -----------------------------------------
    def _params(self, *, system, messages, max_tokens, temperature, model) -> dict:
        """Build the Messages API kwargs, omitting temperature by default.

        The pinned model (Opus 4.8) removed the sampling parameters and 400s if
        `temperature`/`top_p`/`top_k` are sent; include it only if asked.
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

    # --- public interface ----------------------------------------------------
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

        `messages` is the full conversation history (the call is stateless — send
        it all each turn). The first message must be `user`.
        """
        if not system.strip():
            raise ValueError("system prompt is empty — load it from prompts/.")
        if not messages:
            raise ValueError("messages is empty — nothing to send to the model.")

        if self.backend == "cli":
            return self._chat_cli(system, messages, model)

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
    ):
        """Stream a completion. Returns an iterable of text chunks; after it's
        exhausted, `.response` holds the final ClaudeResponse.

        The API backend streams token-by-token. The CLI backend has no token
        stream, so it yields the whole reply once (the caller can show a spinner).
        """
        if not system.strip():
            raise ValueError("system prompt is empty — load it from prompts/.")
        if not messages:
            raise ValueError("messages is empty — nothing to send to the model.")

        if self.backend == "cli":
            return CliChatStream(self, system, messages, model)

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
        """Single-turn convenience wrapper over `chat()` (used by the CLI tool)."""
        if not user.strip():
            raise ValueError("user content is empty — nothing to send to the model.")
        return self.chat(
            system=system,
            messages=[{"role": "user", "content": user}],
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
        )

    # --- CLI backend ---------------------------------------------------------
    def _chat_cli(self, system: str, messages: list[dict], model: str | None) -> ClaudeResponse:
        """Generate via the local `claude` CLI in headless print mode."""
        prompt = _render_cli_prompt(system, messages)
        alias = _CLI_MODEL_ALIAS.get(model or self.model)
        cmd = [self._cli or "claude", "-p", "--output-format", "json"]
        if alias:
            cmd += ["--model", alias]

        try:
            proc = subprocess.run(
                cmd, input=prompt, capture_output=True, text=True, timeout=600,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("`claude` CLI not found on PATH.") from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("The claude CLI timed out (>10 min).") from exc

        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            if "another Claude Code session" in err:
                raise RuntimeError(
                    "Can't call the claude CLI from inside a Claude Code session. "
                    "Run `streamlit run ui/app.py` in a normal terminal instead."
                )
            raise RuntimeError(f"claude CLI failed (exit {proc.returncode}): {err}")

        out = proc.stdout.strip()
        try:
            data = json.loads(out)
        except json.JSONDecodeError:
            if not out:
                raise RuntimeError("claude CLI returned no output.")
            return ClaudeResponse(text=out, model=alias or "claude",
                                  input_tokens=0, output_tokens=0, stop_reason=None)

        if data.get("is_error"):
            raise RuntimeError(f"claude CLI error: {data.get('result') or data}")
        usage = data.get("usage") or {}
        return ClaudeResponse(
            text=data.get("result") or "",
            model=data.get("model") or alias or "claude (Claude Code)",
            input_tokens=int(usage.get("input_tokens", 0) or 0),
            output_tokens=int(usage.get("output_tokens", 0) or 0),
            stop_reason=data.get("subtype"),
        )


class ChatStream:
    """Token stream from the API backend.

    Iterate to consume text deltas; after the iterator is exhausted, `.response`
    holds the final ClaudeResponse. Designed for Streamlit's `st.write_stream`.
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


class CliChatStream:
    """CLI backend 'stream': runs the `claude` CLI once and yields the whole reply.

    Same shape as ChatStream so the UI code is identical — there's just no
    token-by-token streaming, so callers should show a spinner.
    """

    def __init__(self, client: "ClaudeClient", system: str, messages: list[dict],
                 model: str | None) -> None:
        self._client = client
        self._system = system
        self._messages = messages
        self._model = model
        self.response: ClaudeResponse | None = None

    def __iter__(self):
        resp = self._client._chat_cli(self._system, self._messages, self._model)
        self.response = resp
        yield resp.text
