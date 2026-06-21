#!/usr/bin/env python3
"""Onboard a new client by copying clients/_template into clients/<slug>.

One command = "replicate the agent for another client". Produces a fresh,
gitignored engagement folder with the category subfolders (sow, rfp,
meeting-transcripts, status-updates, misc) plus outputs/.

    python scripts/new_client.py "Acme Corp"      # -> clients/acme-corp/
    python scripts/new_client.py acme-corp

The folder name is slugified so it is safe to pass as --client to a tool.
Refuses to overwrite an existing client.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# scripts/new_client.py -> repo root; put it on sys.path so `shared` imports.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.clients import create_client, slugify  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Onboard a new client engagement.")
    parser.add_argument("name", help="client name (will be slugified)")
    args = parser.parse_args(argv)

    try:
        dest = create_client(args.name)
    except (FileExistsError, FileNotFoundError, ValueError) as exc:
        raise SystemExit(str(exc))

    slug = dest.name
    print(f"Created clients/{slug}/  (sow/ rfp/ meeting-transcripts/ status-updates/ misc/ outputs/)")
    print("Next: drop the client's files into the category folders, then run a tool with")
    print(f"  --client {slug}   (or use the UI: streamlit run ui/app.py)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
