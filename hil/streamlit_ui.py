"""
Streamlit UI for the procurement selector group chat (HIL).

Architecture:
  - Background thread runs the Autogen SelectorGroupChat via run_stream().
  - UserProxyAgent receives a custom input_func that blocks on a thread-safe queue,
    so all human replies flow through the UI rather than stdin.
  - @st.fragment(run_every=1) auto-refreshes the message panel every second, giving
    seamless streaming without a manual Refresh button.
  - When the agent workflow needs human input, waiting_ref[0] is set to True; the
    fragment detects the change and triggers a full app rerun so st.chat_input appears.

Run from repo root:
    streamlit run hil/streamlit_ui.py
"""

import asyncio
import queue
import sys
import threading
from pathlib import Path
from typing import Callable

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import streamlit as st

from hil.selector_group_chat_with_hil import build_team

# ---------------------------------------------------------------------------
# Status constants
# ---------------------------------------------------------------------------
_IDLE = "idle"
_RUNNING = "running"
_DONE = "done"
_ERROR = "error"

# ---------------------------------------------------------------------------
# Agent display config
# ---------------------------------------------------------------------------
_AGENT_AVATARS: dict[str, str] = {
    "IntakeAgent": "📥",
    "PolicyAgent": "📜",
    "FinanceAgent": "💰",
    "VendorRiskAgent": "🔍",
    "ReviewerAgent": "✅",
    "HumanProxyAgent": "🤝",
    "You": "👤",
}
_DEFAULT_AVATAR = "🤖"


def _avatar(speaker: str) -> str:
    return _AGENT_AVATARS.get(speaker, _DEFAULT_AVATAR)


# ---------------------------------------------------------------------------
# Session state helpers (mutable list refs survive across Streamlit reruns)
# ---------------------------------------------------------------------------
def _init_state() -> None:
    defaults: dict = {
        "_msgs": [],          # list of {"speaker": str, "content": str}
        "_status": [_IDLE],   # mutable: thread and UI both read/write [0]
        "_error": [None],     # mutable: thread sets error message
        "_waiting": [False],  # mutable: True while input_func blocks on queue
        "_prev_waiting": [False],  # tracks last observed value of _waiting[0]
        "_q": queue.Queue(),  # human-input channel: UI puts, thread gets
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


def _reset_chat() -> None:
    """Clear all chat state so a new conversation can be started."""
    msgs: list = st.session_state["_msgs"]
    msgs.clear()
    st.session_state["_status"][0] = _IDLE
    st.session_state["_error"][0] = None
    st.session_state["_waiting"][0] = False
    st.session_state["_prev_waiting"][0] = False
    q: queue.Queue = st.session_state["_q"]
    while not q.empty():
        try:
            q.get_nowait()
        except queue.Empty:
            break


# ---------------------------------------------------------------------------
# Stream → display conversion
# ---------------------------------------------------------------------------
def _to_display(item) -> tuple[str, str] | None:
    """Return (speaker, content) for displayable stream items, else None."""
    if item.__class__.__name__ == "TaskResult":
        return None
    source: str = getattr(item, "source", None) or ""
    to_text: Callable | None = getattr(item, "to_text", None)
    if callable(to_text):
        try:
            content = to_text() or ""
        except Exception:
            content = str(getattr(item, "content", ""))
    else:
        content = str(getattr(item, "content", ""))
    return (source or "System", content) if content else None


# ---------------------------------------------------------------------------
# Background chat thread
# ---------------------------------------------------------------------------
def _chat_thread(
    task: str,
    msgs: list,
    status_ref: list,
    error_ref: list,
    waiting_ref: list,
    q: queue.Queue,
) -> None:
    """Run the selector group chat; human input is supplied via *q* not stdin."""

    def get_input(prompt: str) -> str:  # noqa: ARG001 (prompt shown via stream)
        waiting_ref[0] = True
        try:
            return q.get()
        finally:
            waiting_ref[0] = False

    try:
        team = build_team(input_func=get_input)

        async def _consume() -> None:
            async for item in team.run_stream(task=task):
                pair = _to_display(item)
                if pair and pair[1]:
                    msgs.append({"speaker": pair[0], "content": pair[1]})

        asyncio.run(_consume())
        status_ref[0] = _DONE
    except Exception:
        status_ref[0] = _ERROR
        error_ref[0] = (
            "The chat could not complete. "
            "Please check your configuration (e.g. OPENAI_API_KEY) and try again."
        )


# ---------------------------------------------------------------------------
# Auto-refreshing message panel (Streamlit fragment)
# ---------------------------------------------------------------------------
@st.fragment(run_every=1)
def _messages_panel() -> None:
    """Render messages and status; auto-reruns every second for seamless streaming."""
    msgs: list = st.session_state["_msgs"]
    status: str = st.session_state["_status"][0]
    waiting: bool = st.session_state["_waiting"][0]
    prev_waiting_ref: list = st.session_state["_prev_waiting"]

    # Render all messages so far
    for msg in list(msgs):
        sp = msg["speaker"]
        with st.chat_message(sp, avatar=_avatar(sp)):
            st.markdown(msg["content"])

    # Status indicator
    if status == _RUNNING and not waiting:
        st.markdown(":gray[⏳ Agents are working…]")
    elif status == _RUNNING and waiting:
        st.info("💬 Your response is needed — type in the input box below.")
    elif status == _DONE:
        st.success("✅ Chat complete.")
    elif status == _ERROR:
        err = st.session_state["_error"][0]
        if err:
            st.error(err)

    # When waiting state changes, trigger a full app rerun so the main script
    # can show or hide st.chat_input accordingly.
    if waiting != prev_waiting_ref[0]:
        prev_waiting_ref[0] = waiting
        st.rerun(scope="app")


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main() -> None:
    st.set_page_config(
        page_title="Procurement Chat",
        page_icon="📋",
        layout="centered",
    )
    _init_state()

    # Header
    st.title("📋 Procurement Chat")
    st.caption("Multi-agent procurement workflow — powered by AutoGen.")
    st.divider()

    status_ref: list = st.session_state["_status"]
    error_ref: list = st.session_state["_error"]
    waiting_ref: list = st.session_state["_waiting"]
    msgs: list = st.session_state["_msgs"]
    q: queue.Queue = st.session_state["_q"]
    status: str = status_ref[0]

    # ── Idle: show task entry form ─────────────────────────────────────────
    if status == _IDLE:
        task = st.text_area(
            "Describe your procurement request",
            placeholder=(
                "e.g. We need 50 MacBooks for Engineering, "
                "budget 75L INR, next quarter. Prefer Apple Authorized Vendor."
            ),
            height=110,
        )
        if st.button("🚀 Start Chat", type="primary", disabled=not (task or "").strip()):
            task = task.strip()
            msgs.clear()
            msgs.append({"speaker": "You", "content": task})
            status_ref[0] = _RUNNING
            error_ref[0] = None
            waiting_ref[0] = False
            st.session_state["_prev_waiting"][0] = False
            while not q.empty():
                try:
                    q.get_nowait()
                except queue.Empty:
                    break
            threading.Thread(
                target=_chat_thread,
                args=(task, msgs, status_ref, error_ref, waiting_ref, q),
                daemon=True,
            ).start()
            st.rerun()
        return  # nothing else to show while idle

    # ── Active chat: auto-refreshing message panel ─────────────────────────
    _messages_panel()

    # ── Human input (shown only while the workflow waits for a reply) ──────
    if status == _RUNNING and waiting_ref[0]:
        if reply := st.chat_input("Your response"):
            q.put(reply)
            msgs.append({"speaker": "You", "content": reply})
            # waiting_ref[0] will be reset to False by the thread's finally block;
            # the fragment picks up the change on its next 1-second tick.

    # ── Done / error: offer a fresh start ─────────────────────────────────
    if status in (_DONE, _ERROR):
        if st.button("🔄 Start a new chat", type="primary"):
            _reset_chat()
            st.rerun()


if __name__ == "__main__":
    main()
