# UI — Engagement Intelligence control panel

A local [Streamlit](https://streamlit.io/) app for running the tools without the
command line. Runs entirely on your machine (localhost); the only network call is
to the Anthropic API when you click **Generate**.

## Run

```bash
pip install -r requirements.txt        # first time (installs streamlit)
streamlit run ui/app.py                 # opens http://localhost:8501
```

## What it does

1. **Pick a client** at the top, or create one with **➕ New client** (scaffolds
   `clients/<slug>/` from the template).
2. **Drop files** into the matching material folder (SOW / RFP, Meeting summaries,
   Executive updates, Other — or add your own folder). Uploads land in the client's
   gitignored folder.
3. **Generate** — choose what you need (Brief, Recap, Talk track, Slides, …), add a
   meeting objective/audience, and click **Generate**. Every file in the client's
   folders is bundled as context. The result is shown, offered as a download, and
   saved to `clients/<slug>/outputs/`.

## Notes

- This is a thin front end. All generation goes through
  `tools/engagement-intelligence-agent/src/agent.py`, and all file handling through
  `shared/clients.py` — the same code the CLI uses.
- If `ANTHROPIC_API_KEY` isn't set in `.env`, you can still manage files; generation
  will fail loudly with a clear message until you add it.
