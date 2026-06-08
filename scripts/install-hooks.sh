#!/usr/bin/env bash
# One-time per clone: point git at the tracked githooks/ directory so the
# pre-commit hook (runs pytest) is active. Safe to re-run.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
git -C "$ROOT" config core.hooksPath githooks
echo "Configured core.hooksPath=githooks — pre-commit will run pytest."
