"""Tests for shared.doc_parsing — category-aware engagement ingestion."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from shared.doc_parsing import (
    DocType,
    Engagement,
    category_label,
    is_supported,
    load_engagement,
    parse_document,
)


def _write(path: Path, text: str = "content") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# --- small units -------------------------------------------------------------

def test_category_label_known_and_derived():
    assert category_label("sow-rfp") == "SOW / RFP"
    assert category_label("exec-updates") == "Executive updates"
    assert category_label("technical-specs") == "Technical Specs"  # derived


def test_parse_document_reads_text_and_date(tmp_path: Path):
    f = _write(tmp_path / "2026-06-03-vp-sync.md", "# notes")
    doc = parse_document(f, doc_type=DocType.TRANSCRIPT, category="meeting-summaries")
    assert doc.text == "# notes"
    assert doc.doc_type is DocType.TRANSCRIPT
    assert doc.doc_date == date(2026, 6, 3)
    assert doc.category == "meeting-summaries"


def test_parse_document_unsupported_type_raises(tmp_path: Path):
    f = _write(tmp_path / "thing.exe", "x")
    with pytest.raises(ValueError):
        parse_document(f)


def test_parse_document_missing_file_raises(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        parse_document(tmp_path / "ghost.md")


def test_is_supported_skips_gitkeep_and_unknown(tmp_path: Path):
    assert is_supported(_write(tmp_path / "a.md"))
    assert not is_supported(_write(tmp_path / ".gitkeep", ""))
    assert not is_supported(_write(tmp_path / "b.exe"))


# --- load_engagement ---------------------------------------------------------

def _make_client(clients_root: Path, name: str) -> Path:
    cdir = clients_root / name
    # Mirror a template-copied client: all category folders exist (incl. empty
    # 'other' and 'outputs'), then real files are dropped in.
    for cat in ("sow-rfp", "meeting-summaries", "exec-updates", "other", "outputs"):
        _write(cdir / cat / ".gitkeep", "")
    _write(cdir / "sow-rfp" / "Acme_SOW.md", "Scope of work")
    _write(cdir / "sow-rfp" / "Acme_RFP.md", "Request for proposal")
    _write(cdir / "meeting-summaries" / "2026-06-01-followup.md", "later")
    _write(cdir / "meeting-summaries" / "2026-05-20-kickoff.md", "earlier")
    _write(cdir / "exec-updates" / "2026-06-05-status.md", "status")
    _write(cdir / "technical-specs" / "arch.txt", "lakehouse")  # custom folder
    return cdir


def test_load_engagement_discovers_categories_in_order(clients_root: Path):
    _make_client(clients_root, "acme")
    eng = load_engagement(clients_root, "acme")
    # known categories first (in preferred order), custom folder after; empty
    # 'other' from the template is included too.
    assert list(eng.categories) == [
        "sow-rfp", "meeting-summaries", "exec-updates", "other", "technical-specs"
    ]


def test_load_engagement_infers_and_forces_doc_types(clients_root: Path):
    _make_client(clients_root, "acme")
    eng = load_engagement(clients_root, "acme")

    sow_types = {d.filename: d.doc_type for d in eng.categories["sow-rfp"]}
    assert sow_types["Acme_SOW.md"] is DocType.SOW   # inferred per file
    assert sow_types["Acme_RFP.md"] is DocType.RFP

    assert all(d.doc_type is DocType.TRANSCRIPT for d in eng.categories["meeting-summaries"])
    assert all(d.doc_type is DocType.EXEC_UPDATE for d in eng.categories["exec-updates"])
    assert all(d.doc_type is DocType.OTHER for d in eng.categories["technical-specs"])


def test_meeting_summaries_sorted_oldest_first(clients_root: Path):
    _make_client(clients_root, "acme")
    eng = load_engagement(clients_root, "acme")
    names = [d.filename for d in eng.categories["meeting-summaries"]]
    assert names == ["2026-05-20-kickoff.md", "2026-06-01-followup.md"]


def test_to_prompt_has_sections_and_filenames(clients_root: Path):
    _make_client(clients_root, "acme")
    text = load_engagement(clients_root, "acme").to_prompt()
    for heading in ["SOW / RFP".upper(), "MEETING SUMMARIES", "EXECUTIVE UPDATES",
                    "TECHNICAL SPECS"]:
        assert heading in text
    assert "Acme_SOW.md" in text
    assert "CLIENT: acme" in text


def test_empty_client_raises(clients_root: Path):
    # template-only structure, no documents
    (clients_root / "empty" / "sow-rfp").mkdir(parents=True)
    with pytest.raises(ValueError):
        load_engagement(clients_root, "empty")


def test_missing_client_raises(clients_root: Path):
    with pytest.raises(FileNotFoundError):
        load_engagement(clients_root, "nobody")


def test_outputs_folder_is_not_a_category(clients_root: Path):
    cdir = clients_root / "acme"
    _write(cdir / "sow-rfp" / "SOW.md", "x")
    _write(cdir / "outputs" / "2026-06-07-brief.md", "generated")  # must be excluded
    eng = load_engagement(clients_root, "acme")
    assert "outputs" not in eng.categories
