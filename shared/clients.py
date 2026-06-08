"""Filesystem helpers for client engagements under clients/<name>/.

Why this exists: both the onboarding script and the Streamlit UI need to create
clients, list category folders, and save uploaded files. Centralizing it here (per
CLAUDE.md) keeps that logic in one place and consistent across surfaces.

Everything is local and gitignored — see clients/README.md.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from shared.doc_parsing import (
    OUTPUTS_DIRNAME,
    SUPPORTED_SUFFIXES,
    is_supported,
)

# shared/clients.py -> repo root
ROOT = Path(__file__).resolve().parents[1]
CLIENTS_ROOT = ROOT / "clients"
TEMPLATE = CLIENTS_ROOT / "_template"

# Folder names we never expose as a client or a category.
_HIDDEN = {"_template"}


def slugify(name: str) -> str:
    """Lowercase, collapse non-alphanumeric runs to single hyphens."""
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    if not slug:
        raise ValueError(f"Cannot derive a folder name from {name!r}.")
    return slug


def list_clients() -> list[str]:
    """All client folder names (slugs), sorted, excluding the template."""
    if not CLIENTS_ROOT.exists():
        return []
    return sorted(
        p.name
        for p in CLIENTS_ROOT.iterdir()
        if p.is_dir() and p.name not in _HIDDEN and not p.name.startswith(".")
    )


def client_dir(client: str) -> Path:
    return CLIENTS_ROOT / client


def create_client(name: str) -> Path:
    """Create clients/<slug>/ from the template. Raises if it already exists."""
    if not TEMPLATE.exists():
        raise FileNotFoundError(f"Template not found: {TEMPLATE}.")
    dest = client_dir(slugify(name))
    if dest.exists():
        raise FileExistsError(f"Client already exists: {dest.name}")
    shutil.copytree(TEMPLATE, dest)
    return dest


def list_categories(client: str) -> list[str]:
    """Input category folders for a client (excludes outputs/), in display order.

    Reuses the same ordering logic the parser uses so the UI and the model agree.
    """
    from shared.doc_parsing import _ordered_categories  # local import: internal helper

    cdir = client_dir(client)
    if not cdir.exists():
        return []
    return _ordered_categories(cdir)


def list_files(client: str, category: str) -> list[Path]:
    """Supported document files inside one category folder."""
    folder = client_dir(client) / category
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir() if is_supported(p))


def list_outputs(client: str) -> list[Path]:
    """Generated artifacts, newest first."""
    folder = client_dir(client) / OUTPUTS_DIRNAME
    if not folder.exists():
        return []
    files = [p for p in folder.iterdir() if p.is_file() and p.name != ".gitkeep"]
    return sorted(files, reverse=True)


def add_category(client: str, name: str) -> Path:
    """Create a new category folder for a client. Returns its path."""
    slug = slugify(name)
    if slug == OUTPUTS_DIRNAME:
        raise ValueError("'outputs' is reserved for generated artifacts.")
    folder = client_dir(client) / slug
    folder.mkdir(parents=True, exist_ok=True)
    (folder / ".gitkeep").touch(exist_ok=True)
    return folder


def save_upload(client: str, category: str, filename: str, data: bytes) -> Path:
    """Save uploaded bytes into a category folder. Returns the written path.

    Rejects unsupported file types and path traversal in the filename.
    """
    safe_name = Path(filename).name  # strip any directory components
    if Path(safe_name).suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(
            f"Unsupported file type for '{safe_name}'. "
            f"Allowed: {', '.join(sorted(SUPPORTED_SUFFIXES))}."
        )
    folder = client_dir(client) / category
    if not folder.exists():
        raise FileNotFoundError(f"Category folder does not exist: {category}")
    dest = folder / safe_name
    dest.write_bytes(data)
    return dest
