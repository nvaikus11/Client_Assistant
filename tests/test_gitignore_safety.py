"""Privacy guarantee, enforced as a test.

The workspace constitution (CLAUDE.md) requires that **no client data or secrets
ever enter git**. That promise lives in the root .gitignore — a file one careless
edit could quietly break, silently committing an API key or a client's SOW.

This test makes the guarantee executable. It builds a *throwaway* git repo, copies
the real .gitignore into it, plants a fake secret (.env) and a fake client folder
with a fake SOW, then asks git what it would actually track. It FAILS if anything
sensitive would be committed — or if the shareable template/READMEs stop being
tracked. If someone weakens .gitignore, this test goes red before the data leaks.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REAL_GITIGNORE = ROOT / ".gitignore"

pytestmark = pytest.mark.skipif(
    shutil.which("git") is None, reason="git not available"
)


def _git(args, cwd):
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )


def _tracked_files(repo: Path) -> set[str]:
    """Files git would commit (staged after `git add -A`), as POSIX paths."""
    _git(["init", "-q"], repo)
    _git(["add", "-A"], repo)
    out = _git(["ls-files"], repo).stdout
    return set(out.splitlines())


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """A throwaway repo mirroring the real ignore rules + a realistic file tree."""
    assert REAL_GITIGNORE.exists(), "root .gitignore is missing"
    (tmp_path / ".gitignore").write_text(REAL_GITIGNORE.read_text())

    # Secrets and the committed example
    (tmp_path / ".env").write_text("ANTHROPIC_API_KEY=sk-ant-SECRET")
    (tmp_path / ".env.example").write_text("ANTHROPIC_API_KEY=")

    # Shareable scaffold (must stay tracked)
    (tmp_path / "clients").mkdir()
    (tmp_path / "clients" / "README.md").write_text("guide")
    for cat in ("sow", "rfp", "meeting-transcripts", "status-updates", "misc", "outputs"):
        d = tmp_path / "clients" / "_template" / cat
        d.mkdir(parents=True)
        (d / ".gitkeep").touch()

    # A real client (name AND data must be ignored)
    acme = tmp_path / "clients" / "acme-corp"
    (acme / "sow").mkdir(parents=True)
    (acme / "sow" / "SOW.pdf").write_text("confidential scope of work")
    (acme / "meeting-transcripts").mkdir(parents=True)
    (acme / "meeting-transcripts" / "2026-06-03-vp-sync.md").write_text("private notes")
    (acme / "outputs").mkdir(parents=True)
    (acme / "outputs" / "2026-06-07-brief.md").write_text("generated brief")

    # Local cruft that should never be tracked
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "x.pyc").write_text("bytecode")

    return tmp_path


def test_secrets_are_never_tracked(fake_repo: Path):
    tracked = _tracked_files(fake_repo)
    assert ".env" not in tracked, "SECRET LEAK: .env would be committed"
    assert ".env.example" in tracked, ".env.example should be tracked"


def test_client_names_and_data_are_never_tracked(fake_repo: Path):
    tracked = _tracked_files(fake_repo)
    leaked = {p for p in tracked if p.startswith("clients/acme-corp/")}
    assert not leaked, f"CLIENT DATA LEAK: {sorted(leaked)} would be committed"


def test_template_and_readme_stay_tracked(fake_repo: Path):
    tracked = _tracked_files(fake_repo)
    # The whole point of the template is that it IS shared.
    assert "clients/README.md" in tracked
    assert "clients/_template/sow/.gitkeep" in tracked
    assert "clients/_template/outputs/.gitkeep" in tracked


def test_pycache_not_tracked(fake_repo: Path):
    tracked = _tracked_files(fake_repo)
    assert not any(p.endswith(".pyc") for p in tracked)
