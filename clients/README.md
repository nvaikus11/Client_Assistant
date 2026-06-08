# Clients — per-engagement data

Each client engagement is one folder under `clients/`, copied from `_template/`.
This keeps the **reusable tool** (code + prompt) cleanly separated from
**per-client data**, so the agent replicates to a new client in one command.

Client material is organized by **category folder**. You can add more folders any
time — they're auto-discovered and included as context with no code change.

```
clients/
├── _template/            ← the shape every engagement is copied from (tracked in git)
│   ├── sow-rfp/          ← SOW, RFP, proposals
│   ├── meeting-summaries/← summaries / transcripts (date-stamp filenames)
│   ├── exec-updates/     ← executive updates
│   ├── other/            ← anything else
│   └── outputs/          ← generated briefs / talk tracks / slide outlines
└── <client-name>/        ← one per client (gitignored — names AND data stay local)
```

## Onboard a new client

```bash
python scripts/new_client.py "Acme Corp"      # -> clients/acme-corp/
```

…or click **➕ New client** in the UI (`streamlit run ui/app.py`).

Then drop the client's files into the matching folder and generate:

```bash
# CLI
python tools/engagement-intelligence-agent/src/main.py --client acme-corp \
    --objective "Align on phase-2 scope" --audience "VP Data + 2 directors"
# …or just use the UI.
```

## Add your own category

Drop a new folder in (e.g. `clients/acme-corp/technical-specs/`) or use the UI's
**➕ Add a category folder** button. It's picked up automatically on the next run.

## Privacy

Everything under `clients/` is gitignored **except** `_template/` and this README —
client names and their data never enter git. Recordings must be transcribed to text
first (the Anthropic API reads text/PDF, not audio); date-stamp each transcript
filename so the agent can track the conversation over time.
