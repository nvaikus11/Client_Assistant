"""Engagement Intelligence — local Streamlit control panel.

Select a client, drop files into the right material folder, then generate a brief /
recap / talk track / slides, etc. Everything runs locally; the only network call is
to the Anthropic API at generation time.

Run from the repo root:

    streamlit run ui/app.py
"""

from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ui/app.py -> repo root; put it on sys.path so `shared` and the tool import.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import clients as cfs  # noqa: E402
from shared.doc_parsing import SUPPORTED_SUFFIXES, category_label  # noqa: E402

# The tool folder name is hyphenated (not a valid module name), so load by path.
# Register in sys.modules before exec so the module can resolve itself (e.g. for
# @dataclass under `from __future__ import annotations`).
_AGENT_PATH = ROOT / "tools" / "engagement-intelligence-agent" / "src" / "agent.py"
_spec = importlib.util.spec_from_file_location("eia_agent", _AGENT_PATH)
agent = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = agent
_spec.loader.exec_module(agent)

_UPLOAD_TYPES = sorted(s.lstrip(".") for s in SUPPORTED_SUFFIXES)

st.set_page_config(page_title="Engagement Intelligence", page_icon="🧭", layout="wide")
load_dotenv()


def _select_client() -> str | None:
    """Top-of-page client selector + new-client creator."""
    clients = cfs.list_clients()
    col_pick, col_new = st.columns([3, 2])

    with col_pick:
        if clients:
            client = st.selectbox("Client", options=clients, key="client")
        else:
            client = None
            st.info("No clients yet — create one on the right to get started.")

    with col_new:
        with st.expander("➕ New client"):
            name = st.text_input("Client name", key="new_client_name",
                                 placeholder="e.g. Acme Corp")
            if st.button("Create client", use_container_width=True):
                try:
                    dest = cfs.create_client(name)
                    st.session_state["client"] = dest.name
                    st.success(f"Created clients/{dest.name}/")
                    st.rerun()
                except Exception as exc:  # FileExists / empty name / etc.
                    st.error(str(exc))

    return client


def _materials(client: str) -> None:
    """Per-category file lists + drag-drop uploaders, plus add-folder."""
    st.subheader(f"📁 Materials — {client}")
    st.caption("Drop files into the matching folder. Everything here is bundled as "
               "context when you generate.")

    for category in cfs.list_categories(client):
        files = cfs.list_files(client, category)
        with st.expander(f"{category_label(category)}  ·  {len(files)} file(s)"):
            if files:
                for f in files:
                    st.write(f"• {f.name}")
            else:
                st.caption("No files yet.")

            uploads = st.file_uploader(
                f"Add to {category_label(category)}",
                type=_UPLOAD_TYPES,
                accept_multiple_files=True,
                key=f"up_{client}_{category}",
                label_visibility="collapsed",
            )
            if uploads:
                added, skipped = [], []
                for up in uploads:
                    dest = cfs.client_dir(client) / category / Path(up.name).name
                    if dest.exists():
                        skipped.append(up.name)
                        continue
                    try:
                        cfs.save_upload(client, category, up.name, up.getvalue())
                        added.append(up.name)
                    except Exception as exc:
                        st.error(f"{up.name}: {exc}")
                if skipped:
                    st.caption("Already present: " + ", ".join(skipped))
                if added:
                    st.success("Added: " + ", ".join(added))
                    st.rerun()  # refresh counts/listing

    with st.expander("➕ Add a category folder"):
        new_folder = st.text_input("Folder name", key=f"newcat_{client}",
                                   placeholder="e.g. technical-specs")
        if st.button("Add folder", key=f"addcat_{client}"):
            try:
                cfs.add_category(client, new_folder)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _generate(client: str) -> None:
    """The 'what do you need?' panel + output display."""
    st.subheader("✨ Generate")

    label = st.selectbox("What do you need?", options=list(agent.MODES.keys()),
                         key="mode_label")
    col_o, col_a = st.columns(2)
    objective = col_o.text_input("Meeting objective",
                                 placeholder="e.g. Align on phase-2 scope")
    audience = col_a.text_input("Audience (who's in the room)",
                                placeholder="e.g. VP of Data + 2 directors")
    topic = st.text_input("Topic / named artifact (optional)",
                          placeholder="Only needed for some modes (e.g. ARTIFACT, DEEP DIVE)")

    if st.button("Generate", type="primary", use_container_width=True):
        try:
            with st.spinner("Generating with Claude…"):
                result = agent.generate_artifact(
                    client=client,
                    mode=agent.MODES[label],
                    objective=objective or None,
                    audience=audience or None,
                    topic=topic or None,
                )
            st.success(
                f"Saved {result.out_path.name}  ·  "
                f"{result.input_tokens} in / {result.output_tokens} out tokens  ·  "
                f"{result.model}"
            )
            st.download_button("⬇ Download .md", result.text,
                               file_name=result.out_path.name, mime="text/markdown")
            st.markdown(result.text)
        except Exception as exc:  # missing docs / missing key / API error
            st.error(str(exc))


def _previous_outputs(client: str) -> None:
    outs = cfs.list_outputs(client)
    if not outs:
        return
    st.subheader("🗂 Previous outputs")
    pick = st.selectbox("View a past output", options=[p.name for p in outs],
                        key="past_output")
    st.markdown((cfs.client_dir(client) / "outputs" / pick).read_text(encoding="utf-8"))


def main() -> None:
    st.title("🧭 Engagement Intelligence")

    if not os.environ.get("ANTHROPIC_API_KEY"):
        st.warning("ANTHROPIC_API_KEY is not set in .env — you can manage files, but "
                   "generation will fail until you add it.")

    client = _select_client()
    if not client:
        return

    st.divider()
    left, right = st.columns([1, 1])
    with left:
        _materials(client)
    with right:
        _generate(client)

    st.divider()
    _previous_outputs(client)


main()
