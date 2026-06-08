"""Tests for shared.clients — client filesystem helpers.

Uses the `patched_clients` fixture so every operation runs against a throwaway
clients/ directory, never the real (gitignored) one.
"""

from __future__ import annotations

import pytest

from shared.clients import slugify


# --- slugify -----------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("Acme Corp", "acme-corp"),
    ("  A/B & C!! ", "a-b-c"),
    ("Globex, Inc.", "globex-inc"),
    ("already-slug", "already-slug"),
])
def test_slugify(raw, expected):
    assert slugify(raw) == expected


def test_slugify_empty_raises():
    with pytest.raises(ValueError):
        slugify("   !!!  ")


# --- create / list -----------------------------------------------------------

def test_create_client_scaffolds_categories(patched_clients):
    dest = patched_clients.create_client("Acme Corp")
    assert dest.name == "acme-corp"
    assert set(patched_clients.list_categories("acme-corp")) == {
        "sow-rfp", "meeting-summaries", "exec-updates", "other"
    }
    # 'outputs' exists on disk but is never an input category
    assert (dest / "outputs").exists()
    assert "outputs" not in patched_clients.list_categories("acme-corp")


def test_create_duplicate_client_raises(patched_clients):
    patched_clients.create_client("Acme")
    with pytest.raises(FileExistsError):
        patched_clients.create_client("Acme")


def test_list_clients_excludes_template(patched_clients):
    patched_clients.create_client("Beta")
    patched_clients.create_client("Alpha")
    assert patched_clients.list_clients() == ["alpha", "beta"]  # sorted, no _template


# --- uploads -----------------------------------------------------------------

def test_save_upload_writes_file(patched_clients):
    patched_clients.create_client("Acme")
    dest = patched_clients.save_upload("acme", "sow-rfp", "SOW.md", b"# scope")
    assert dest.read_text() == "# scope"
    assert [p.name for p in patched_clients.list_files("acme", "sow-rfp")] == ["SOW.md"]


def test_save_upload_rejects_unsupported_type(patched_clients):
    patched_clients.create_client("Acme")
    with pytest.raises(ValueError):
        patched_clients.save_upload("acme", "other", "malware.exe", b"x")


def test_save_upload_strips_path_traversal(patched_clients):
    patched_clients.create_client("Acme")
    dest = patched_clients.save_upload("acme", "other", "../../../evil.md", b"x")
    # filename is reduced to its basename and stays inside the category folder
    assert dest.name == "evil.md"
    assert dest.parent == patched_clients.client_dir("acme") / "other"


def test_list_files_ignores_gitkeep(patched_clients):
    patched_clients.create_client("Acme")
    assert patched_clients.list_files("acme", "other") == []  # only .gitkeep present


# --- categories & outputs ----------------------------------------------------

def test_add_category(patched_clients):
    patched_clients.create_client("Acme")
    folder = patched_clients.add_category("acme", "Technical Specs")
    assert folder.name == "technical-specs"
    assert (folder / ".gitkeep").exists()
    assert "technical-specs" in patched_clients.list_categories("acme")


def test_add_category_rejects_outputs(patched_clients):
    patched_clients.create_client("Acme")
    with pytest.raises(ValueError):
        patched_clients.add_category("acme", "outputs")


def test_list_outputs_newest_first(patched_clients):
    patched_clients.create_client("Acme")
    out = patched_clients.client_dir("acme") / "outputs"
    (out / "2026-06-01-a.md").write_text("old")
    (out / "2026-06-07-b.md").write_text("new")
    names = [p.name for p in patched_clients.list_outputs("acme")]
    assert names == ["2026-06-07-b.md", "2026-06-01-a.md"]
