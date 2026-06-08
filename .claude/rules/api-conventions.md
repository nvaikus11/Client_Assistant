# Rule: Anthropic API conventions

Loads on demand when working with API-calling code (`shared/claude_client.py`,
anything that imports it, or new tool entry points). Keeps every tool consistent
and aligned with the workspace constitution in `CLAUDE.md`.

## One client, shared
- All Anthropic API calls go through `shared/claude_client.py`. Tools **import** it;
  they never construct an `anthropic.Anthropic()` client or call `messages.create`
  directly.
- If a tool needs new API behavior (streaming, tool use, vision), add it to the
  shared wrapper rather than inlining it in the tool.

## Keys & config
- The API key is read at runtime from `.env` via `python-dotenv`
  (`ANTHROPIC_API_KEY`). Never hardcode keys or accept them as plaintext args.
- Fail loudly if the key is missing — raise a clear error at startup, do not
  silently fall back or proceed.
- Default model comes from `ANTHROPIC_MODEL` (see `.env.example`), overridable
  per call. Pin model IDs explicitly; do not rely on aliases that drift.

## Provider lock-in
- **Anthropic only.** Do not add OpenAI, Gemini, local models, LangChain, or any
  other provider/orchestration layer. If a task seems to need one, stop and ask.

## Prompts
- System prompts live in `prompts/<tool-name>-prompt.md` and are the source of
  truth for behavior. Load them from file at runtime; do not paste prompt text
  into Python.
- Prompts must instruct the model to **flag gaps, never fabricate** client
  specifics that aren't in the provided documents.

## Calls & reliability
- Set a sensible `max_tokens` per call and surface token usage where useful.
- Catch and surface API errors (rate limits, overloaded, auth) with actionable
  messages; do not swallow exceptions.
- Keep request/response logging free of client-confidential content unless the
  user explicitly opts in — logs are not a place for SOW/RFP text.
