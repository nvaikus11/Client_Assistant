# Engagement Intelligence Agent — Tool Context

> Tool-specific context. The root `CLAUDE.md` is the constitution; this file adds
> detail for *this* tool only.

## Purpose
Prepare a Manager to lead a client meeting by reading an engagement's source
documents (SOW, RFP, supporting decks/notes) **and prior meeting transcripts**, then
producing grounded, meeting-ready artifacts via named output modes (BRIEF, FRAMING,
TALK TRACK, DISCOVERY, RECAP, SLIDES, ARTIFACT, RISK/OPP, DEEP DIVE).

## How it works
1. The client's material lives in `clients/<name>/` (gitignored), organized by category
   folder: `sow/`, `rfp/`, `meeting-transcripts/`, `status-updates/`, `misc/` (and any
   folder you add — auto-discovered).
2. `shared/doc_parsing.load_engagement()` discovers every category folder, extracts and
   labels the files, and orders meeting transcripts oldest→newest so the agent can track
   the conversation over time.
3. `shared/prompts.load_system_prompt()` loads the canonical prompt
   (`prompts/engagement-intelligence-agent-prompt.md`); `src/agent.py` adds the meeting
   objective, audience, and requested mode.
4. The combined message is sent to Claude via `shared/claude_client.py`.
5. The artifact is written to `clients/<name>/outputs/<timestamp>-<mode>.md`.

## Run it
```bash
# UI (recommended): pick client, drop files, click Generate
streamlit run ui/app.py

# …or CLI
python tools/engagement-intelligence-agent/src/main.py --client <slug> \
    --objective "Align on phase-2 scope" \
    --audience "Client VP of Data + 2 directors" \
    --mode DEFAULT
```
Onboard a new client first with `python scripts/new_client.py "Client Name"` (or the
UI's ➕ New client button).

## Layout
- `src/agent.py` — core generation logic (`generate_artifact()`), shared by the CLI and
  the UI so behavior is identical across surfaces.
- `src/main.py` — thin CLI wrapper over `agent.py`.
- API, parsing, and prompt-loading logic live in `shared/`; this tool imports them,
  never re-implements them. This tool holds **no client data** — that lives in
  `clients/<name>/`.

## Rules specific to this tool
- **Ground everything.** Every client-specific fact must trace to a document or
  transcript. Gaps are flagged ([ASSUMPTION] / gap), never invented.
- **Never re-ask what a transcript already answered** — that's the core value here.
- The system prompt in `prompts/` is the source of truth for behavior. Change behavior
  there, not by hardcoding strings in `src/`.
- Use the shared `ClaudeClient`; do not construct an Anthropic client here.
- Fail loudly if the client folder has no docs/transcripts or the API key is missing.

## Status
Runnable (v0) — single-shot CLI. Possible next steps: per-tool `requirements.txt`,
tests for `shared/doc_parsing.py`, and an interactive mode that prompts for missing
objective/audience.
