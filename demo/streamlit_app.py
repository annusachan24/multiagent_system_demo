"""
Streamlit UI for the procurement workflow (selector group chat).

Conversation happens in the browser; no terminal. Run from repo root:
  streamlit run demo/streamlit_app.py
"""

import asyncio
import os
import sys
from concurrent.futures import ThreadPoolExecutor

_demo_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_demo_dir)
if _root not in sys.path:
    sys.path.insert(0, _root)
if _demo_dir not in sys.path:
    sys.path.insert(0, _demo_dir)

import streamlit as st
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import Response, TaskResult
from autogen_agentchat.conditions import MaxMessageTermination, TextMentionTermination
from autogen_agentchat.messages import (
    ModelClientStreamingChunkEvent,
    MultiModalMessage,
    TextMessage,
    ToolCallExecutionEvent,
    ToolCallRequestEvent,
    ToolCallSummaryMessage,
    UserInputRequestedEvent,
)
from autogen_agentchat.teams import SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient

from constants import openai_api_key
from prompts import AGENT_CONFIG

# -----------------------------------------------------------------------------
# Page config
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Procurement workflow",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------------------------------------------------------
# Build team (assistant agents only – user replies via chat, not as an agent)
# -----------------------------------------------------------------------------
@st.cache_resource
def get_team():
    model_client = OpenAIChatCompletionClient(model="gpt-4o", api_key=openai_api_key)
    AGENT_DESCRIPTIONS = {
        "intake_agent": "Extracts and structures procurement request. Use first for new requests.",
        "policy_agent": "Checks policy compliance. Use after intake when request is structured.",
        "finance_agent": "Validates budget. Use after intake for financial checks.",
        "vendor_risk_agent": "Assesses vendor risk. Use when vendor is known.",
        "reviewer_agent": "Synthesizes findings and decides next action. Use after other agents.",
    }
    assistant_agents = []
    for key, config in AGENT_CONFIG.items():
        if key == "human_proxy_agent":
            continue
        assistant_agents.append(
            AssistantAgent(
                name=key,
                description=AGENT_DESCRIPTIONS.get(key, config["prompt"][:200]),
                model_client=model_client,
                system_message=config["prompt"],
                tools=config.get("tools") or [],
            )
        )
    termination = (
        TextMentionTermination("TERMINATE")
        | TextMentionTermination("FINAL_DECISION")
        | TextMentionTermination("APPROVED")
        | TextMentionTermination("REJECTED")
        | MaxMessageTermination(max_messages=30)
    )
    selector_prompt = """You are selecting the next agent in a procurement workflow.

Agents and when to use them:
{roles}

Current conversation:
{history}

Select exactly one agent from {participants} to perform the next step.
Prefer order: intake (structure request) -> policy/finance/vendor_risk (checks) -> reviewer (synthesize).
When clarification is needed from the user (e.g. missing department, quantity, budget), the reviewer or intake should state it clearly so the user can reply in the next message.

Reply with only the agent name.
"""
    return SelectorGroupChat(
        assistant_agents,
        model_client=model_client,
        termination_condition=termination,
        selector_prompt=selector_prompt,
        allow_repeated_speaker=True,
    )


SOURCE_LABELS = {
    "user": "You",
    "intake_agent": "Intake",
    "policy_agent": "Policy",
    "finance_agent": "Finance",
    "vendor_risk_agent": "Vendor risk",
    "reviewer_agent": "Reviewer",
}


def _friendly_source(source: str) -> str:
    return SOURCE_LABELS.get(source, source.replace("_", " ").title())


def _is_internal_or_error(text: str) -> bool:
    if not text or not text.strip():
        return True
    lower = text.lower()
    return (
        "validation error for " in lower
        or "field required [type=missing" in lower
        or "input_value={}" in lower
        or "for further information visit https://errors.pydantic" in lower
    )


async def collect_messages(stream):
    """Consume stream and return list of {role, source, content} for display."""
    out = []
    last_processed = None
    streaming_content = []
    async for message in stream:
        if isinstance(message, TaskResult):
            last_processed = message
            continue
        if isinstance(message, Response):
            last_processed = message
            content = (
                message.chat_message.to_text()
                if hasattr(message.chat_message, "to_text")
                else str(message.chat_message)
            )
            if not _is_internal_or_error(content):
                out.append(
                    {
                        "role": "assistant",
                        "source": _friendly_source(message.chat_message.source),
                        "content": content,
                    }
                )
            continue
        if isinstance(message, UserInputRequestedEvent):
            continue
        if isinstance(message, ToolCallRequestEvent):
            out.append({"role": "assistant", "source": "System", "content": "Checking your request…"})
            continue
        if isinstance(message, (ToolCallExecutionEvent, ToolCallSummaryMessage)):
            continue
        if isinstance(message, ModelClientStreamingChunkEvent):
            streaming_content.append(message.to_text())
            continue
        if isinstance(message, (TextMessage, MultiModalMessage)):
            if streaming_content:
                streaming_content.clear()
            content = message.to_text() if hasattr(message, "to_text") else str(message)
            if _is_internal_or_error(content):
                continue
            out.append(
                {
                    "role": "assistant",
                    "source": _friendly_source(message.source),
                    "content": content,
                }
            )
            continue
    if last_processed is None:
        raise ValueError("No TaskResult or Response was processed.")
    return out


def _run_team_async(task: str):
    """Run team in a dedicated event loop (call from a thread to avoid Streamlit's loop)."""
    team = get_team()
    stream = team.run_stream(task=task)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(collect_messages(stream))
    finally:
        loop.close()


def run_team_sync(task: str):
    """Run team in a thread so Streamlit's event loop is not blocked or conflicted."""
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(_run_team_async, task)
        return future.result(timeout=120)


# -----------------------------------------------------------------------------
# Session state
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending_user_input" not in st.session_state:
    st.session_state.pending_user_input = None
if "run_team_task" not in st.session_state:
    st.session_state.run_team_task = None  # When set, we need to run the team and append results

# --- 1) Consume pending chat input: add user message and schedule team run ---
if st.session_state.pending_user_input is not None:
    user_text = st.session_state.pending_user_input.strip()
    st.session_state.pending_user_input = None
    if user_text:
        st.session_state.messages.append({"role": "user", "content": user_text})
        # Build full conversation for context; will run in step 2
        task_parts = []
        for m in st.session_state.messages:
            if m["role"] == "user":
                task_parts.append(f"User: {m['content']}")
            else:
                task_parts.append(f"{m.get('source', 'Assistant')}: {m['content']}")
        st.session_state.run_team_task = "\n\n".join(task_parts)
    st.rerun()

# --- 2) If a team run was scheduled, run it in a thread and show spinner ---
if st.session_state.run_team_task is not None:
    task = st.session_state.run_team_task
    st.session_state.run_team_task = None
    status = st.status("Processing your request…", state="running")
    with status:
        try:
            new_msgs = run_team_sync(task)
            for m in new_msgs:
                st.session_state.messages.append(m)
            status.update(label="Done", state="complete")
        except Exception as e:
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "source": "System",
                    "content": f"Something went wrong. Please try again or rephrase. ({str(e)[:200]})",
                }
            )
            status.update(label="Error", state="error")
    st.rerun()

# -----------------------------------------------------------------------------
# UI
# -----------------------------------------------------------------------------
st.title("Procurement workflow")
st.caption("Describe your request in the chat. The team will ask for any missing details (e.g. department, budget).")

# Show conversation (or welcome when empty)
if not st.session_state.messages:
    with st.chat_message("assistant", avatar="📋"):
        st.markdown(
            "**Welcome.** Send a procurement request to start (e.g. *50 MacBooks for Engineering, 75L INR, next quarter*). "
            "If something is missing, we'll ask and you can reply here."
        )
else:
    for msg in st.session_state.messages:
        role = "user" if msg["role"] == "user" else "assistant"
        with st.chat_message(role, avatar="🧑" if role == "user" else "📋"):
            if msg["role"] == "assistant" and msg.get("source") and msg["source"] != "You":
                st.markdown(f"**{msg['source']}**\n\n{msg['content']}")
            else:
                st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input("Your message (e.g. request or missing detail)…"):
    st.session_state.pending_user_input = prompt
    st.rerun()
