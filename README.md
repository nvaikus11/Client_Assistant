# Client Assistant — AI Tools Workspace

[![tests](https://github.com/nvaikus11/Client_Assistant/actions/workflows/tests.yml/badge.svg)](https://github.com/nvaikus11/Client_Assistant/actions/workflows/tests.yml)

A personal workspace of standalone AI tools that assist with consulting delivery.
Each tool is an independent agent built on the [Anthropic API](https://docs.anthropic.com/).

> See [CLAUDE.md](CLAUDE.md) for the workspace constitution (constraints, layout, and
> conventions). That file is the source of truth; this README is the quick start.

## Tools

| Tool | Path | Status |
|------|------|--------|
| Engagement Intelligence Agent | [`tools/engagement-intelligence-agent/`](tools/engagement-intelligence-agent/) | In design |

The **Engagement Intelligence Agent** prepares consulting meetings from an engagement's
SOW / RFP / supporting docs — producing briefs, talk tracks, and slide outlines.

## Setup

Requires **Python 3.11+**.

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install shared dependencies (each tool may add its own requirements.txt)
pip install -r requirements.txt

# 3. Add your Anthropic API key
cp .env.example .env   # if present; otherwise create .env
#   then edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

`.env` is gitignored and read at runtime via `python-dotenv`. Never hardcode keys.

## Using it

Tools are client-agnostic: client material lives in `clients/<name>/`, organized by
material category. Onboard a client once, then generate from the UI or the CLI.

### Option A — the UI (recommended)

```bash
streamlit run ui/app.py        # opens http://localhost:8501
```

Pick a client (or create one), drop files into the matching folder (SOW / RFP,
Meeting summaries, Executive updates, Other — or add your own), choose what you need
(Brief / Recap / Talk track / Slides / …), and click **Generate**. See
[`ui/README.md`](ui/README.md).

### Option B — the CLI

```bash
# 1. Onboard a client (creates clients/<slug>/ from the template — gitignored)
python scripts/new_client.py "Acme Corp"            # -> clients/acme-corp/

# 2. Add the client's material to the matching category folder
cp ~/path/to/SOW.pdf            clients/acme-corp/sow-rfp/
cp ~/path/to/2026-06-03-sync.md clients/acme-corp/meeting-summaries/   # text transcripts

# 3. Run the agent from the repo root
python tools/engagement-intelligence-agent/src/main.py --client acme-corp \
    --objective "Align on phase-2 scope" \
    --audience "VP of Data + 2 directors" \
    --mode DEFAULT
```

Artifacts are written to `clients/acme-corp/outputs/<timestamp>-<mode>.md`.
See [`clients/README.md`](clients/README.md) for the per-engagement folder model.

## Ground rules (summary)

- **Anthropic API only** — no other model providers or orchestration frameworks.
- **Local and isolated** — no cloud, Docker, or client infrastructure.
- **No client data or secrets in git** — engagements live in gitignored `clients/<name>/`, keys in `.env`.
- **Never fabricate client specifics** — if a fact isn't in the provided documents, flag it as a gap.

## Development

```bash
pip install -r requirements-dev.txt     # test runner
pytest                                   # run the suite (shared/ + gitignore safety)
./scripts/install-hooks.sh               # one-time: enable the pre-commit hook
```

The `tests/` suite covers the shared layer and includes a **gitignore-safety test**
that fails if `.env` or client data would ever be tracked. A **pre-commit hook**
(`githooks/pre-commit`, activated via `core.hooksPath`) runs `pytest` before each
commit and blocks it on failure. Bypass in a pinch with `git commit --no-verify`.

## Adding a new tool

1. Create `tools/<name>/` with `src/` and its own `CLAUDE.md` (code only — no client data).
2. Put its system prompt in `prompts/<name>-prompt.md`.
3. Reuse `shared/` for API calls, parsing, and prompt loading — do not duplicate.
4. Read client material from `clients/<name>/` via `--client`; never hardcode a client.
5. Add a row to the Tools index above (and in `CLAUDE.md`).
