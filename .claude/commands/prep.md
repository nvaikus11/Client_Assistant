---
description: Run the Engagement Intelligence Agent over a client's folders (no API key — runs inside Claude Code)
argument-hint: <client-slug> [MODE] [meeting objective…]
allowed-tools: Read, Glob, Grep, Write
---

You are running the **Engagement Intelligence Agent** directly inside Claude Code.
This is the no-API path: you read the files yourself and produce the output — there
is no Anthropic API key and no Streamlit app involved.

## Arguments
`$ARGUMENTS`

Parse them as:
- **First token** = the client folder slug under `clients/` (e.g. `aurora-grocery-demo`).
- **Remaining text** (optional) = a MODE and/or a meeting objective/audience. Recognized
  modes: `BRIEF`, `FRAMING`, `TALK TRACK`, `DISCOVERY`, `RECAP`, `SLIDES`, `ARTIFACT`,
  `RISK/OPP`, `DEEP DIVE`. If no mode is given, use the prompt's DEFAULT behavior.

If no client slug was provided, list the subfolders of `clients/` (excluding
`_template`) and ask which client to prep, then stop.

## Steps

1. **Adopt the agent's behavior.** Read `prompts/engagement-intelligence-agent-prompt.md`
   and follow the instructions inside its fenced code block as your operating system
   prompt — the role, the `<output_modes>`, the `<default_behavior>`, and especially:
   - Ground every claim in the provided files. Label each as `[FACT]` (stated in a
     document/transcript), `[INFERENCE]` (reasoned from sources), or `[ASSUMPTION]`
     (a gap you are filling — verify it). **Never fabricate** client specifics.
   - **Never surface a question or talking point that a prior meeting already
     answered.** Track decisions, commitments, and open threads across meetings.

2. **Load the engagement.** Read every supported file (`.md .txt .pdf .docx .pptx`) under
   `clients/<slug>/` across its category folders — typically `sow-rfp/`,
   `meeting-summaries/`, `exec-updates/`, `other/` (skip `outputs/` and `.gitkeep`).
   Use Glob to discover folders so any extra category is included. **Order
   `meeting-summaries/` oldest → newest** by the `YYYY-MM-DD` date in each filename so you
   can reason about how the engagement evolved. If a folder is empty, note it as a gap.

3. **Produce the requested output.** Run the named MODE, or the DEFAULT brief pack if none
   was given (short BRIEF → RECAP of what's settled vs. open → Manager-level FRAMING →
   recommended TALK TRACK for the stated objective → 3–5 highest-value DISCOVERY questions,
   excluding anything already answered → flagged gaps/assumptions). Lead with the point;
   be executive-concise.

4. **Offer to save.** After the output, offer to write it to
   `clients/<slug>/outputs/<YYYY-MM-DD>-<mode>.md` (lowercase mode, `/`→`-`, spaces→`-`).
   Only write the file if the user confirms, or if they included the word `save` in the
   arguments.

If the meeting objective and audience are unclear and a TALK TRACK is requested, ask one
short clarifying question first, then proceed.
