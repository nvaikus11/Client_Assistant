# Pulling meeting notes from Granola

Instead of exporting transcripts by hand, the **`/sync-meetings`** command pulls your
Granola meeting notes straight into a client's `meeting-transcripts/` folder, where
`/prep` then picks them up automatically (oldest→newest by date).

This runs in **Claude Code** — the Granola MCP server is available to the agent, not to
the Python/Streamlit app. So this is part of the no-API Claude Code workflow.

## One-time setup: connect Granola to Claude Code

Granola exposes an MCP server. Add it to Claude Code once (per machine):

- **Easiest:** in Claude Code, open the connector directory (`/mcp`) and add **Granola**,
  then sign in to your Granola account. (Or add it from the Claude desktop app's
  Connectors settings.)
- **Or via CLI:** `claude mcp add` and follow the prompts to add the Granola connector.

Verify it's connected by asking Claude Code: *"List my Granola meetings from the last week."*

## Usage

```text
/sync-meetings vertiv            ← asks which meetings, then pulls them into clients/vertiv/
/sync-meetings vertiv Vertiv     ← pulls meetings whose title matches "Vertiv"
/sync-meetings acme since 2026-06-01
/sync-meetings acme last 5
```

It writes each meeting to
`clients/<client>/meeting-transcripts/<YYYY-MM-DD>-<title-slug>.md` and **skips files
that already exist**, so re-running only adds new meetings. Then run `/prep <client>`.

## Group by client, not "everything"

Your Granola likely has many engagements mixed together. `/sync-meetings` is designed to
pull **one client's** meetings into that client's folder (by title match or date range) —
not to dump everything into one place. Run it once per client.

## Free vs. paid Granola tier

- **Free tier:** `list_meetings` (titles + dates) and `get_meetings` (AI summary +
  private notes + attendees) work. The command uses these — the summaries are rich
  enough for prep. Meeting **folders** and **verbatim transcripts** are paid-only.
- **Paid tier:** adds `list_meeting_folders` and `get_meeting_transcript` (verbatim).
  The command uses transcripts when available and falls back to summaries otherwise.

## Privacy

Pulled notes land in `clients/<name>/` which is **gitignored** — your meeting content
stays on your machine and is never committed. (Running `/prep` over them still sends
that text to Claude; on a firm machine, use enterprise Claude Code, per `SETUP.md`.)
