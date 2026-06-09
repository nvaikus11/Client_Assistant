# Examples — sample engagement for demos & testing

A **100% fictional** engagement you can use to demo or test the tool **without any
real client data**. This is also a selling point: you can show the full capability
on synthetic material, which keeps demos clean from a governance standpoint.

> **"Aurora Grocery Group" is invented.** These files contain no Deloitte or client
> confidential information. Safe to commit, share, and screen-record.

## What's inside — `aurora-grocery/`

A retail data-modernization engagement (Deloitte AI & Data helping a fictional
grocer build a lakehouse + ML demand forecasting), with material spread across the
same category folders the tool uses:

```
aurora-grocery/
├── sow-rfp/
│   ├── AGG_Statement_of_Work_Phase1.md   # scope, deliverables, timeline, $1.2M, team
│   └── AGG_RFP_Excerpt.md                # the client's original ask + eval criteria
├── meeting-summaries/                    # the "continuity" story (date-stamped)
│   ├── 2026-04-08-kickoff.md             # platform + budget + go-live decided
│   ├── 2026-04-29-architecture-review.md # batch vs real-time decided; ERP risk raised
│   └── 2026-05-20-steering-committee.md  # MLflow chosen; CFO wants ROI; Phase 2 scope open
└── exec-updates/
    └── 2026-05-27-exec-status.md         # RAG status one-pager
```

The meetings are **intentionally connected**: decisions get made (and should *not* be
re-asked), risks evolve, and open threads carry forward — so a **Recap** or **Talk
track** for the next meeting (Steering #3 on June 10) really shows the tool off.

## Load it into a client (to run the demo)

```bash
python scripts/new_client.py "Aurora Grocery (Demo)"     # -> clients/aurora-grocery-demo/
cp examples/aurora-grocery/sow-rfp/*            clients/aurora-grocery-demo/sow-rfp/
cp examples/aurora-grocery/meeting-summaries/*  clients/aurora-grocery-demo/meeting-summaries/
cp examples/aurora-grocery/exec-updates/*       clients/aurora-grocery-demo/exec-updates/
```

Then `streamlit run ui/app.py`, pick **aurora-grocery-demo**, and start a session.
See **[DEMO_SCRIPT.md](DEMO_SCRIPT.md)** for a 5-minute recording storyboard.

## Make your own samples

Need different industries or scenarios? Ask Claude to generate them — e.g.
*"Write a fictional SOW + 3 dated meeting summaries for a bank doing a fraud-ML
engagement, with a decision in meeting 1 and an open ROI question by meeting 3."*
Drop the results into the matching folders. Keep them clearly fictional.
