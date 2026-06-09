# Demo script — 5-minute recording storyboard

A tight, repeatable demo using the fictional **Aurora Grocery** engagement. The goal:
show that the tool makes a Manager walk into a client meeting fully prepped — and
never re-asking what a prior meeting already settled.

## Pre-flight (before you hit record)
- [ ] `.env` has a working `ANTHROPIC_API_KEY`.
- [ ] Demo client loaded (see examples/README.md → "Load it into a client").
- [ ] `streamlit run ui/app.py` is up; **aurora-grocery-demo** selected.
- [ ] Browser zoom ~110%; close noisy tabs/notifications.
- [ ] (Optional) Pre-run once so any first-call latency is warm.

## The narrative spine (say this)
> "Before a client meeting, a Manager burns 60–90 minutes re-reading the deal room.
> This agent does it in two minutes — grounded only in our actual documents, and
> crucially, it tracks what prior meetings already decided so we never re-ask a
> settled question and look uninformed."

## Beats

**1. The setup (~30s).** Show the sidebar: "Here's a fictional retail engagement —
no real client data. SOW, RFP, three dated meeting summaries, an exec update, sorted
into folders." Open one meeting summary briefly.

**2. The brief pack (~75s) — the money shot.** Start a session → mode
**Default brief pack** → objective: *"Prep for the June 10 steering committee"* →
audience: *"CFO + VP Data + Supply Chain Director."* Model: **Auto**. Generate.
(The default pack is a strategic task, so Auto picks **Opus 4.8** — best quality, and
it pins the whole session to that model.) Call out as it streams: the **Recap**
section pulls decisions across all three meetings — Databricks, $1.2M budget, MLflow,
July 3 go-live — and separates what's still open: the ROI model, Phase 2 scope, the
Bakery question. Point at the caption: *"It chose the model from task complexity —
for a quick recap on a small doc set it would've used the fast, low-cost model
instead."*

**3. DISCOVERY — what NOT to ask (~45s).** In the chat box, type:
*"Give me the 5 highest-value questions for June 10 — and explicitly skip anything
already decided."* Highlight that it does **not** re-ask budget or platform (settled),
and surfaces real open items (ROI inputs, pricing-optimization scope).

**4. TALK TRACK + live refine (~60s).** Chat: *"Now draft a 4-minute talk track to
open that meeting for the CFO."* Then refine live: *"Tighten it and lead with the ROI
number."* This shows the **conversation** — answering/iterating, not one-shot.

**5. Turn it into a deliverable (~45s).** Chat: *"Redo the key points as a 5-slide
outline."* Then click **💾 Save latest reply** → "and it's saved to the client's
outputs folder."

**6. Trust & governance close (~30s).** Scroll to any `[FACT]`/`[INFERENCE]`/
`[ASSUMPTION]` label: *"Everything is labeled by how sure it is — it flags gaps
instead of inventing client specifics."* Then: *"It runs locally, client files stay
in a gitignored folder, and model choice keeps cost in check."*

## What to emphasize (the differentiators)
- **Continuity across meetings** — won't re-ask answered questions (vs. generic chat).
- **Grounded, no hallucination** — FACT / INFERENCE / ASSUMPTION; flags gaps.
- **One tool, many deliverables** — recap, discovery, talk track, slides, risks.
- **Replicable per client** in one command; **local + governed**; **cost-aware** model routing.

## Recording tips
- 4–6 minutes total. Keep prompts on screen long enough to read.
- If a generation runs long, cut to the finished output in edit.
- End on the saved output + the governance line — that's what an approver remembers.
