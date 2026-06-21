# UI — Engagement Intelligence control panel

A local [Streamlit](https://streamlit.io/) **chat** app for running the tools
without the command line. Runs entirely on your machine (localhost); the only
network calls are to the Anthropic API during the conversation.

## Run

```bash
pip install -r requirements.txt        # first time (installs streamlit)
streamlit run ui/app.py                 # opens http://localhost:8501
```

## What it does

1. **Pick a client** in the sidebar, or create one with **➕ New client** (scaffolds
   `clients/<slug>/` from the template).
2. **Drop files** (sidebar) into the matching material folder — SOW, RFP, Meeting
   Transcripts, Status Updates, Misc, or a folder you add. Uploads land in the
   client's gitignored folder.
3. **Start a session** — pick what you need first (Brief, Recap, Talk track, Slides,
   …), add a meeting objective/audience, and choose a **model** (see below). Every
   file in the client's folders is loaded as context for the whole conversation.
4. **Chat to refine** — the model produces a first draft, then you converse: answer
   its clarifying questions, ask it to expand a section, redo as slides, tighten the
   talk track, etc. Replies stream in live.
5. **Save** any reply to `clients/<slug>/outputs/` with one click. **↺ New** starts a
   fresh session (e.g. after adding more files).

## Model selection

The **Model** dropdown defaults to **Auto (by complexity)**, which picks a model from
the task and how much context is loaded — and shows you which it chose and why:

- Strategic/generative tasks (Default pack, Framing, Talk track, Slides, Artifact,
  Risks/Opps, Deep dive) → **Opus 4.8** (most capable).
- Lighter tasks (Brief, Recap, Discovery) → **Haiku 4.5** (small context),
  **Sonnet 4.6** (moderate), or **Opus 4.8** (very large).

Override to a specific model any time. The chosen model is used for the whole session.

## Notes

- This is a thin front end. Generation and routing go through
  `tools/engagement-intelligence-agent/src/agent.py`; the API wrapper is
  `shared/claude_client.py`; file handling is `shared/clients.py` — the same code the
  CLI uses.
- Context is snapshotted when you **Start session**. Added a file mid-conversation?
  Click **↺ New** to reload it.
- If `ANTHROPIC_API_KEY` isn't set in `.env`, you can still manage files; generation
  fails loudly with a clear message until you add it.
