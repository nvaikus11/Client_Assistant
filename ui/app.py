"""Engagement Intelligence — local Streamlit control panel (chat).

Pick a client, drop files into the right material folder (sidebar), then hold a
multi-turn conversation: generate a first draft, answer the model's clarifying
questions, and refine ("expand the risks", "redo as slides"). The full document
context stays loaded across the conversation. Everything runs locally; the only
network call is to the Anthropic API.

Run from the repo root:

    streamlit run ui/app.py
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# ui/app.py -> repo root; put it on sys.path so `shared` and the tool import.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared import clients as cfs  # noqa: E402
from shared.claude_client import ClaudeClient, detect_backend  # noqa: E402
from shared.doc_parsing import (  # noqa: E402
    SUPPORTED_SUFFIXES,
    category_label,
    load_engagement,
)

# The tool folder name is hyphenated (not a valid module name), so load by path.
# Register in sys.modules before exec so the module can resolve itself.
_AGENT_PATH = ROOT / "tools" / "engagement-intelligence-agent" / "src" / "agent.py"
_spec = importlib.util.spec_from_file_location("eia_agent", _AGENT_PATH)
agent = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = agent
_spec.loader.exec_module(agent)

CLIENTS_ROOT = ROOT / "clients"
_UPLOAD_TYPES = sorted(s.lstrip(".") for s in SUPPORTED_SUFFIXES)
CHAT_MAX_TOKENS = 8000

st.set_page_config(page_title="Engagement Intelligence", page_icon="🧭", layout="wide")
load_dotenv(ROOT / ".env")


@st.cache_resource(show_spinner=False)
def get_client() -> ClaudeClient:
    """One shared Anthropic client for the app session (raises if key missing)."""
    return ClaudeClient()


# ---------------------------------------------------------------- sidebar -----

def _sidebar() -> str | None:
    """Client selector + new client + materials. Returns the selected client."""
    with st.sidebar:
        st.header("Client")
        clients = cfs.list_clients()
        client = st.selectbox("Select", options=clients, key="client") if clients else None
        if not clients:
            st.info("No clients yet — create one below.")

        with st.expander("➕ New client"):
            name = st.text_input("Client name", key="new_client_name",
                                 placeholder="e.g. Acme Corp")
            if st.button("Create client", use_container_width=True):
                try:
                    dest = cfs.create_client(name)
                    st.session_state["client"] = dest.name
                    st.success(f"Created clients/{dest.name}/")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

        if client:
            st.divider()
            st.header("Materials")
            st.caption("Drop files into the matching folder. These are the context "
                       "for the conversation.")
            _materials(client)
            st.divider()
            _past_outputs(client)

    return client


def _materials(client: str) -> None:
    for category in cfs.list_categories(client):
        files = cfs.list_files(client, category)
        with st.expander(f"{category_label(category)} · {len(files)}"):
            for f in files:
                st.write(f"• {f.name}")
            if not files:
                st.caption("No files yet.")
            uploads = st.file_uploader(
                f"Add to {category_label(category)}", type=_UPLOAD_TYPES,
                accept_multiple_files=True, key=f"up_{client}_{category}",
                label_visibility="collapsed",
            )
            if uploads:
                added = []
                for up in uploads:
                    dest = cfs.client_dir(client) / category / Path(up.name).name
                    if dest.exists():
                        continue
                    try:
                        cfs.save_upload(client, category, up.name, up.getvalue())
                        added.append(up.name)
                    except Exception as exc:
                        st.error(f"{up.name}: {exc}")
                if added:
                    st.success("Added: " + ", ".join(added))
                    st.rerun()

    with st.expander("➕ Add a folder"):
        new_folder = st.text_input("Folder name", key=f"newcat_{client}",
                                   placeholder="e.g. technical-specs")
        if st.button("Add folder", key=f"addcat_{client}"):
            try:
                cfs.add_category(client, new_folder)
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def _past_outputs(client: str) -> None:
    outs = cfs.list_outputs(client)
    with st.expander(f"🗂 Saved outputs · {len(outs)}"):
        if not outs:
            st.caption("None yet.")
            return
        pick = st.selectbox("File", options=[p.name for p in outs], key=f"out_{client}")
        path = cfs.client_dir(client) / "outputs" / pick
        st.download_button("⬇ Download", path.read_text(encoding="utf-8"),
                           file_name=pick, mime="text/markdown",
                           use_container_width=True)


# ---------------------------------------------------------------- chat --------

def _assistant_turn(state: dict, system: str) -> None:
    """Stream one assistant reply for the current api_messages and record it."""
    with st.chat_message("assistant"):
        try:
            client = get_client()
            stream = client.stream_chat(
                system=system, messages=state["api_messages"],
                model=state["model"], max_tokens=CHAT_MAX_TOKENS,
            )
            if client.backend == "cli":
                # No token stream from the CLI — show a spinner while it runs.
                with st.spinner("Generating via Claude Code… (first reply can take ~30–60s)"):
                    text = st.write_stream(stream)
            else:
                text = st.write_stream(stream)
        except Exception as exc:  # missing backend, API/CLI error, etc.
            st.error(f"Generation failed: {exc}")
            return
        resp = stream.response
        if resp.input_tokens or resp.output_tokens:
            caption = (f"🧠 {resp.model} · {resp.input_tokens:,} in / "
                       f"{resp.output_tokens:,} out tokens")
        else:
            caption = f"🧠 {resp.model}"
        st.caption(caption)

    state["api_messages"].append({"role": "assistant", "content": text})
    state["display"].append({"role": "assistant", "content": text, "caption": caption})


def _start_session_form(client: str) -> dict | None:
    """Render the setup form. On submit, seed and return the new chat state."""
    with st.form("setup"):
        st.markdown("**Start a session**")
        mode_label = st.selectbox("What do you need first?", options=list(agent.MODES))
        col_o, col_a = st.columns(2)
        objective = col_o.text_input("Meeting objective",
                                     placeholder="e.g. Align on phase-2 scope")
        audience = col_a.text_input("Audience",
                                    placeholder="e.g. VP of Data + 2 directors")
        topic = st.text_input("Topic / named artifact (optional)")
        model_label = st.selectbox("Model", options=list(agent.MODEL_CHOICES),
                                   help="Auto picks a model from task complexity; "
                                        "override to force a specific one.")
        started = st.form_submit_button("Start session", type="primary",
                                        use_container_width=True)

    if not started:
        return None

    try:
        engagement = load_engagement(CLIENTS_ROOT, client)
    except Exception as exc:  # no docs yet, etc.
        st.error(str(exc))
        return None

    mode = agent.MODES[mode_label]
    model, reason = agent.resolve_model(agent.MODEL_CHOICES[model_label], mode, engagement)
    seed = agent.build_user_message(engagement, objective=objective or None,
                                    audience=audience or None, mode=mode,
                                    topic=topic or None)
    return {
        "api_messages": [{"role": "user", "content": seed}],
        "display": [],
        "pending": True,
        "model": model,
        "model_reason": reason,
        "mode_label": mode_label,
        "n_docs": len(engagement.all_docs),
        "started_mode": mode,
    }


def _chat(client: str) -> None:
    system = agent.load_prompt()
    chat_key = f"chat::{client}"
    state = st.session_state.get(chat_key)

    if state is None:
        st.caption("Set the meeting context, then chat to refine. The model may ask a "
                   "clarifying question — answer it in the chat box.")
        new_state = _start_session_form(client)
        if new_state is not None:
            st.session_state[chat_key] = new_state
            state = new_state
        else:
            return  # waiting for the user to start

    # Active session header
    head = st.container()
    with head:
        c1, c2 = st.columns([5, 1])
        c1.caption(f"📎 {state['n_docs']} doc(s) · first task: **{state['mode_label']}** "
                   f"· {state['model_reason']}")
        if c2.button("↺ New", use_container_width=True, help="Start a fresh session"):
            del st.session_state[chat_key]
            st.rerun()

    # Transcript
    for msg in state["display"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("caption"):
                st.caption(msg["caption"])

    # First assistant turn after seeding
    if state.get("pending"):
        state["pending"] = False
        _assistant_turn(state, system)

    # Save the latest reply
    last_assistant = next((m for m in reversed(state["display"])
                           if m["role"] == "assistant"), None)
    if last_assistant:
        if st.button("💾 Save latest reply to outputs/"):
            out_dir = cfs.client_dir(client) / "outputs"
            out_dir.mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
            slug = state["started_mode"].lower().replace("/", "-").replace(" ", "-")
            path = out_dir / f"{stamp}-{slug}-chat.md"
            path.write_text(last_assistant["content"], encoding="utf-8")
            st.success(f"Saved {path.name}")

    # Follow-up input
    prompt = st.chat_input("Refine, or answer the model's question…")
    if prompt:
        state["api_messages"].append({"role": "user", "content": prompt})
        state["display"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        _assistant_turn(state, system)


# ---------------------------------------------------------------- main --------

def main() -> None:
    st.title("🧭 Engagement Intelligence")

    backend, reason = detect_backend()
    if backend is None:
        st.warning(f"No Claude backend found — {reason}. Add ANTHROPIC_API_KEY to .env, "
                   "or install Claude Code (`claude`) to run without an API key. You can "
                   "still manage files.")
    else:
        st.caption(f"Backend: {reason}")

    client = _sidebar()
    if not client:
        st.info("Create or select a client in the sidebar to begin.")
        return

    st.subheader(f"💬 {client}")
    _chat(client)


main()
