"""Tests for backend selection and CLI prompt rendering (no CLI execution)."""

from __future__ import annotations

import shared.claude_client as cc


def _setup(monkeypatch, *, key=None, cli=False, mode=None):
    if key is None:
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    else:
        monkeypatch.setenv("ANTHROPIC_API_KEY", key)
    if mode is None:
        monkeypatch.delenv("EIA_BACKEND", raising=False)
    else:
        monkeypatch.setenv("EIA_BACKEND", mode)
    monkeypatch.setattr(
        cc.shutil, "which",
        lambda name: "/usr/local/bin/claude" if (cli and name == "claude") else None,
    )


# --- detect_backend ----------------------------------------------------------

def test_auto_prefers_api_when_key_present(monkeypatch):
    _setup(monkeypatch, key="sk-ant-x", cli=True)
    assert cc.detect_backend()[0] == "api"


def test_auto_uses_cli_when_no_key(monkeypatch):
    _setup(monkeypatch, key=None, cli=True)
    assert cc.detect_backend()[0] == "cli"


def test_auto_none_when_neither(monkeypatch):
    _setup(monkeypatch, key=None, cli=False)
    backend, reason = cc.detect_backend()
    assert backend is None and "no" in reason.lower()


def test_force_cli_without_cli_is_none(monkeypatch):
    _setup(monkeypatch, key="sk-ant-x", cli=False, mode="cli")
    assert cc.detect_backend()[0] is None


def test_force_api_without_key_is_none(monkeypatch):
    _setup(monkeypatch, key=None, cli=True, mode="api")
    assert cc.detect_backend()[0] is None


def test_force_cli_with_key_present_still_cli(monkeypatch):
    _setup(monkeypatch, key="sk-ant-x", cli=True, mode="cli")
    assert cc.detect_backend()[0] == "cli"


# --- _render_cli_prompt ------------------------------------------------------

def test_render_single_user_has_no_role_labels():
    p = cc._render_cli_prompt("SYSTEM RULES", [{"role": "user", "content": "hello world"}])
    assert p.startswith("SYSTEM RULES")
    assert "hello world" in p
    assert "[USER]" not in p  # single-turn stays clean


def test_render_multiturn_has_labels_and_trailing_assistant():
    msgs = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "reply"},
        {"role": "user", "content": "second"},
    ]
    p = cc._render_cli_prompt("SYS", msgs)
    assert "[USER]" in p and "[ASSISTANT]" in p
    assert "first" in p and "reply" in p and "second" in p
    assert p.rstrip().endswith("[ASSISTANT]")


def test_cli_model_alias_map():
    assert cc._CLI_MODEL_ALIAS["claude-opus-4-8"] == "opus"
    assert cc._CLI_MODEL_ALIAS["claude-sonnet-4-6"] == "sonnet"
    assert cc._CLI_MODEL_ALIAS["claude-haiku-4-5"] == "haiku"
