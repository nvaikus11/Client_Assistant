"""Pytest configuration shared across the suite.

Placing this at the repo root puts the root on sys.path (pytest's default
"prepend" import mode), so tests can `import shared...` without installing the
project. Also defines fixtures for building throwaway client folders so tests
never touch the real (gitignored) clients/ directory.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Category folders the template ships with (the five minimum categories).
TEMPLATE_CATEGORIES = ("sow", "rfp", "meeting-transcripts", "status-updates", "misc")


def build_template(clients_root: Path) -> Path:
    """Create a clients/_template tree under `clients_root`. Returns the root."""
    template = clients_root / "_template"
    for category in (*TEMPLATE_CATEGORIES, "outputs"):
        folder = template / category
        folder.mkdir(parents=True, exist_ok=True)
        (folder / ".gitkeep").touch()
    return clients_root


@pytest.fixture
def clients_root(tmp_path: Path) -> Path:
    """A throwaway clients/ directory containing a fresh _template."""
    root = tmp_path / "clients"
    build_template(root)
    return root


@pytest.fixture
def patched_clients(clients_root, monkeypatch):
    """Point shared.clients at the throwaway clients/ root for the test's duration."""
    from shared import clients as cfs

    monkeypatch.setattr(cfs, "CLIENTS_ROOT", clients_root)
    monkeypatch.setattr(cfs, "TEMPLATE", clients_root / "_template")
    return cfs
