---
description: Pull meeting transcripts from Granola into a client's meeting-transcripts/ folder
argument-hint: <client-slug> [granola folder | search term | since YYYY-MM-DD | last N]
allowed-tools: Read, Glob, Write, mcp__*get_meetings, mcp__*list_meetings, mcp__*query_granola_meetings, mcp__*list_meeting_folders, mcp__*get_meeting_transcript
---

Pull meeting transcripts from **Granola** (via its MCP server) and save them into a
client's `meeting-transcripts/` folder, so you don't export transcripts by hand. This
runs inside Claude Code (the Granola MCP is available to the agent, not to the Python app).

## Arguments
`$ARGUMENTS`

Parse as:
- **First token** = the client folder slug under `clients/` (e.g. `aurora-grocery`).
  If missing, list the clients (subfolders of `clients/` except `_template`) and ask which.
- **Remaining text** (optional) = how to pick meetings: a Granola **folder name**, a
  **search term** (client/company name), `since YYYY-MM-DD`, or `last N`. If omitted,
  ask which meetings to sync rather than pulling everything.

## Steps

1. **Check Granola is connected.** Confirm the Granola MCP tools are available
   (`list_meetings` / `query_granola_meetings` / `list_meeting_folders` /
   `get_meeting_transcript`). If not, stop and tell the user to connect the Granola
   connector in Claude Code first (see `docs/granola-sync.md`), then re-run.

2. **Find the meetings.** Use `list_meetings` (optionally `time_range: custom` with
   `custom_start`/`custom_end`) and match titles to the filter (company/client name),
   or use `query_granola_meetings` for a natural-language search. (`list_meeting_folders`
   is a paid-tier feature — fall back to title matching on the free tier.) **Show the
   user the matched list (title + date) and confirm before downloading**, unless they
   passed an explicit filter.

3. **Download each meeting.** For each matched meeting, call `get_meeting_transcript`
   for the verbatim transcript. **If that returns a paid-tier error, fall back to
   `get_meetings`** (max 10 ids per call), which returns the AI summary + private notes
   + attendees — that content is fully usable here.

4. **Write into the client folder.** Save each as
   `clients/<slug>/meeting-transcripts/<YYYY-MM-DD>-<short-title-slug>.md`, where the
   date is the meeting date and the title is slugified (lowercase, hyphens). Start each
   file with a short header, then the transcript body:
   ```
   # <Meeting title>
   **Date:** <YYYY-MM-DD>  **Source:** Granola  **Attendees:** <if available>

   <transcript text>
   ```
   **Skip files that already exist** (idempotent) so re-running only adds new meetings.

5. **Report.** List what was added vs. skipped, then remind: run `/prep <slug>` to use them.

## Notes
- Only write text/markdown. Keep the meeting **date** accurate — `/prep` orders
  transcripts oldest→newest by the date in the filename.
- This pulls the user's real meeting data; respect their scope (don't bulk-download
  unrelated clients' meetings into one folder).
