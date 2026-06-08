#!/usr/bin/env python3
"""Engagement Intelligence Agent — CLI entry point.

Thin wrapper over agent.generate_artifact() (shared with the Streamlit UI). Reads
one client's engagement sources, generates a meeting-prep artifact, and writes it
to that client's outputs/ folder.

Run from anywhere (paths resolve relative to the repo root):

    python tools/engagement-intelligence-agent/src/main.py --client acme-corp \\
        --objective "Align on phase-2 scope" \\
        --audience "Client VP of Data + 2 directors" \\
        --mode DEFAULT

Modes: DEFAULT, BRIEF, FRAMING, "TALK TRACK", DISCOVERY, RECAP, SLIDES, ARTIFACT,
"RISK/OPP", "DEEP DIVE".
"""

from __future__ import annotations

import argparse
import sys

# agent.py lives next to this file; importing it puts the repo root on sys.path.
from agent import VALID_MODES, generate_artifact  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Engagement Intelligence Agent")
    parser.add_argument("--client", required=True, help="client folder name under clients/")
    parser.add_argument("--objective", help="the meeting objective")
    parser.add_argument("--audience", help="who is in the room (role/seniority)")
    parser.add_argument("--topic", help="specific topic/focus or named artifact")
    parser.add_argument("--mode", default="DEFAULT", help="output mode (see prompt)")
    parser.add_argument("--model", help="override the Anthropic model id")
    parser.add_argument("--max-tokens", type=int, default=8000)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    mode = args.mode.strip().upper()
    if mode not in VALID_MODES:
        valid = ", ".join(sorted(VALID_MODES))
        raise SystemExit(f"Unknown --mode '{args.mode}'. Choose one of: {valid}.")

    result = generate_artifact(
        client=args.client,
        mode=mode,
        objective=args.objective,
        audience=args.audience,
        topic=args.topic,
        model=args.model,
        max_tokens=args.max_tokens,
    )

    print(
        f"Wrote {result.out_path.relative_to(result.out_path.parents[3])}  "
        f"({result.input_tokens} in / {result.output_tokens} out tokens, "
        f"model {result.model}).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
