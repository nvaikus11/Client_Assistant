# Setup — running this workspace on a new machine

How to bring the workspace up on a fresh machine (e.g. a work laptop) and run it
locally. Everything here is local-only — no cloud deploy, no Docker, no client
infrastructure (per `CLAUDE.md`).

---

## ⚠️ Read first: client data leaves the machine at generation time

This tool is **local**, but generating an artifact **sends your document text
(SOW / RFP / transcripts) to the Anthropic API** — i.e. off the machine to a third
party. The code, the gitignore, and the tests guarantee no client data or secrets
are ever committed to git — but they do **not** stop the API call itself.

Before running **real client material** on a firm-managed machine, confirm with your
organization's AI-governance / risk / IT:

- Is sending client-confidential data to the Anthropic API an **approved** path?
- Should this run under a **firm-managed Anthropic account/key**, not a personal one?
- **Rotate any API key** that has been shared in chat/email/screenshare.

The repo is safe to move and clone. The judgment call is routing client text to the API.

---

## Prerequisites

- **Python 3.11+** (`python3 --version`). If you can't install it, use a firm-approved
  Python distribution or ask IT.
- **git** (to clone). If git/GitHub is blocked, see the ZIP option below.
- Network egress to **PyPI** (for `pip install`) and to **`api.anthropic.com`**
  (for generation). Behind a corporate proxy, see [Corporate network](#corporate-network-gotchas).

---

## 1. Get the code

The repo is **private** (`github.com/nvaikus11/Client_Assistant`). Pick whatever your
IT allows:

```bash
# A) GitHub CLI
gh auth login
gh repo clone nvaikus11/Client_Assistant

# B) HTTPS + Personal Access Token (paste the token when prompted for password)
git clone https://github.com/nvaikus11/Client_Assistant.git

# C) No git access: download the repo as a ZIP from the GitHub web UI, then unzip.
```

```bash
cd Client_Assistant
```

> **Note:** a clone contains **only `clients/_template/`** — no client data comes
> across (it's gitignored). You recreate engagements locally on this machine
> (step 5), and they stay here.

## 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows (PowerShell): .venv\Scripts\Activate.ps1
                                   # Windows (cmd):        .venv\Scripts\activate.bat
```

## 3. Install dependencies

```bash
pip install -r requirements.txt          # runtime: anthropic, streamlit, doc parsers
pip install -r requirements-dev.txt      # optional: pytest (to run the test suite)
```

## 4. Configure your API key

```bash
cp .env.example .env
```

Then edit `.env` and set your key (this file is gitignored — never commit it):

```
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-opus-4-8
```

## 5. Run it

```bash
streamlit run ui/app.py            # opens http://localhost:8501
```

In the app: **➕ New client** → drop the engagement's files into the material folders
(sidebar) → **Start session** → chat to refine. Or use the CLI:

```bash
python tools/engagement-intelligence-agent/src/main.py --client <slug> \
    --objective "..." --audience "..." --mode DEFAULT
```

## 6. (Optional) Developer setup

```bash
pytest                             # should report 36 passed
./scripts/install-hooks.sh         # enable the pre-commit hook (runs pytest on commit)
```

`./scripts/install-hooks.sh` is needed once per clone — the hook lives in `githooks/`
but `core.hooksPath` is local git config that doesn't travel with the repo.

---

## Corporate network gotchas

Locked-down machines usually trip on one of these:

- **Python version** — must be 3.11+. A system Python that's older won't run the code.
- **pip behind a proxy** — set proxy env vars, or pass `--proxy`, or use an internal
  index:
  ```bash
  export HTTPS_PROXY=http://user:pass@proxy.corp:8080
  pip install -r requirements.txt --proxy "$HTTPS_PROXY"
  # or an internal mirror:
  pip install -r requirements.txt -i https://pypi.internal.corp/simple
  ```
- **API egress** — the runtime must reach `https://api.anthropic.com`. If the firewall
  blocks it, the UI loads but generation fails. The Anthropic SDK honors standard
  `HTTPS_PROXY` env vars; set them in the same shell that runs Streamlit.
- **Admin rights** — installing Python or creating a venv may need IT approval.

---

## Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `ANTHROPIC_API_KEY is not set` | `.env` missing or key blank — see step 4. |
| `ModuleNotFoundError: streamlit` / `anthropic` | venv not activated, or deps not installed (steps 2–3). |
| Generation hangs or connection error | API egress blocked / proxy not set — see Corporate network. |
| `command not found: python3` | Use `python` (Windows) or install Python 3.11+. |
| A scanned PDF yields an empty document | `pypdf` extracts text only (no OCR) — use text-based PDFs/DOCX or OCR first. |
| Pre-commit hook not running | Run `./scripts/install-hooks.sh` once on this clone. |
