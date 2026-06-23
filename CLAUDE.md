# AI Tools Workspace

## Purpose
A personal workspace of standalone AI tools that assist with consulting delivery.
Each tool is an independent agent built on the Anthropic API. The first tool is the
**Engagement Intelligence Agent** (consulting meeting prep from SOW/RFP/supporting docs).
More tools will be added over time, so structure must scale to many tools.

## Critical constraints
- **Claude (Anthropic) only.** Every tool reaches Claude through `shared/claude_client.py`,
  which uses one of two Anthropic transports: the Anthropic API/SDK, or the local Claude
  Code CLI (`claude`) for a no-API-key path. Do not introduce other model providers,
  frameworks, or orchestration layers unless I ask.
- **Local and isolated.** This runs on my machine as standalone code. Do NOT add AWS,
  cloud deployment, client infrastructure, Docker, or serverless. The client's platform
  is theirs; this project never touches it.
- **No client data or secrets in git.** Client documents (SOW, RFP, decks, transcripts)
  and API keys are never committed. Each engagement lives in a gitignored
  `clients/<name>/` folder (names *and* data stay local); keys live in `.env` and are
  read at runtime.
- **Never fabricate client specifics.** If a fact isn't in the provided documents, the
  code and prompts must flag it as a gap, not invent it.

## Tech stack (default — ask before changing)
- Language: Python 3.11+
- Anthropic SDK: `anthropic`
- Config: `.env` loaded via `python-dotenv`; never hardcode keys
- Dependencies: one `requirements.txt` per tool, plus a shared one at root

## Repo layout
- `prompts/` — canonical system prompts; the source of truth for each agent's behavior
- `shared/` — reusable code across tools (API client wrapper, document parsing, prompt loading)
- `tools/<tool-name>/` — one folder per tool, each with its own `CLAUDE.md` and `src/`.
  Tools hold **code only** — no client data.
- `clients/<name>/` — one folder per client engagement (gitignored), organized by
  **material category** (the five minimum): `sow/`, `rfp/`, `meeting-transcripts/`,
  `status-updates/`, `misc/`, plus `outputs/` (generated artifacts). Any extra subfolder
  is auto-discovered as a category — no code change needed. Copied from `clients/_template/`.
  This separation is
  what lets the agents be replicated across clients: the tool is written once, the
  client folder is created per engagement.
- `ui/` — local Streamlit control panel (`streamlit run ui/app.py`): pick a client,
  drop files into the category folders, and generate. Localhost only, no cloud.
- `scripts/` — workspace utilities (e.g. `new_client.py` to onboard an engagement)
- `.claude/rules/` — topic-specific rules that load on demand when relevant files are touched

## Replicating an agent for a new client
The tools are client-agnostic; client material is passed in by folder. To run any tool
against a new client:
1. Onboard: `python scripts/new_client.py "Client Name"` (or the ➕ New client button in
   the UI) → creates `clients/<slug>/` from the template.
2. Drop the client's files into the matching category folder (`sow/`, `rfp/`,
   `meeting-transcripts/`, `status-updates/`, `misc/`, or a folder you add — extras are
   auto-discovered).
3. Generate via the UI, or run a tool with `--client <slug>`; artifacts land in
   `clients/<slug>/outputs/`.

## Coding standards
- Small, readable functions with clear names over cleverness.
- Type hints on public functions; docstrings explain *why*, not *what*.
- Keep all API-calling logic in `shared/`; tools import it rather than re-implementing.
- Fail loudly on missing inputs, documents, or keys — never silently proceed.

## Tools index
| Tool | Path | Status |
|------|------|--------|
| Engagement Intelligence Agent | `tools/engagement-intelligence-agent/` | Runnable (v0) |

## Adding a new tool
1. Create `tools/<name>/` with `src/` and its own `CLAUDE.md` (code only — no client data).
2. Put its system prompt in `prompts/<name>-prompt.md`.
3. Reuse `shared/` for API calls, parsing, and prompt loading; do not duplicate.
4. Read client material from `clients/<name>/` via `--client`; never hardcode a client.
5. Add a row to the Tools index above.
