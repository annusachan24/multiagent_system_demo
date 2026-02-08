"""
Selector group chat for the procurement workflow with human-in-the-loop.

Uses agents and tools from demo/prompts.py and demo/tools.py.
Run from repo root: python demo/selector_human_in_loop.py
"""

import asyncio
import os
import sys

# Ensure demo and project root are on path for prompts, tools, and constants
_demo_dir = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_demo_dir)
if _root not in sys.path:
    sys.path.insert(0, _root)
if _demo_dir not in sys.path:
    sys.path.insert(0, _demo_dir)

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
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

from contants import openai_api_key
from prompts import AGENT_CONFIG

# -----------------------------------------------------------------------------
# Model client
# -----------------------------------------------------------------------------
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=openai_api_key,
)

# -----------------------------------------------------------------------------
# Build agents from AGENT_CONFIG (intake, policy, finance, vendor_risk, reviewer)
# -----------------------------------------------------------------------------
AGENT_DESCRIPTIONS = {
    "intake_agent": "Extracts and structures procurement request from user input. Use first for new requests.",
    "policy_agent": "Checks policy compliance and approval rules. Use after intake when request is structured.",
    "finance_agent": "Validates budget and spend. Use after intake for financial checks.",
    "vendor_risk_agent": "Assesses vendor eligibility and risk. Use when vendor is known.",
    "reviewer_agent": "Synthesizes all findings and decides next action (approve/escalate/reject). Use after other agents.",
}

assistant_agents = []
for key, config in AGENT_CONFIG.items():
    if key == "human_proxy_agent":
        continue
    name = key.replace("_agent", " ").replace("_", " ").title()
    assistant_agents.append(
        AssistantAgent(
            name=key,
            description=AGENT_DESCRIPTIONS.get(key, config["prompt"][:200]),
            model_client=model_client,
            system_message=config["prompt"],
            tools=config.get("tools") or [],
        )
    )

# Human-in-the-loop: when selector chooses this agent, user is prompted for input
human_agent = UserProxyAgent(
    "human_proxy_agent",
    description="Human user. Select when intake or reviewer need clarification (e.g. missing department, quantity, budget) or when final approval/rejection is needed.",
)

participants = assistant_agents + [human_agent]

# -----------------------------------------------------------------------------
# Termination: stop on explicit end or after max messages
# -----------------------------------------------------------------------------
termination = (
    TextMentionTermination("TERMINATE")
    | TextMentionTermination("FINAL_DECISION")
    | TextMentionTermination("APPROVED")
    | TextMentionTermination("REJECTED")
    | MaxMessageTermination(max_messages=30)
)

# -----------------------------------------------------------------------------
# Selector prompt for procurement workflow
# -----------------------------------------------------------------------------
selector_prompt = """You are selecting the next agent in a procurement workflow.

Agents and when to use them:
{roles}

Current conversation:
{history}

Select exactly one agent from {participants} to perform the next step.

Rules:
- If the intake_agent (or any message) shows status INCOMPLETE, missing_fields, HUMAN_INPUT_NEEDED, or asks for clarification (e.g. department, quantity, budget), you MUST select human_proxy_agent so the human can provide the missing information.
- Otherwise prefer order: intake (structure request) -> policy/finance/vendor_risk (checks) -> reviewer (synthesize).
- Choose human_proxy_agent when the reviewer escalates or when a final human decision is needed.

Reply with only the agent name.
"""

# -----------------------------------------------------------------------------
# Team
# -----------------------------------------------------------------------------
team = SelectorGroupChat(
    participants,
    model_client=model_client,
    termination_condition=termination,
    selector_prompt=selector_prompt,
    allow_repeated_speaker=True,
)


# Friendly labels for agents (no raw event names or errors for the user)
SOURCE_LABELS = {
    "user": "You",
    "intake_agent": "Intake",
    "policy_agent": "Policy",
    "finance_agent": "Finance",
    "vendor_risk_agent": "Vendor risk",
    "reviewer_agent": "Reviewer",
    "human_proxy_agent": "You",
}


def _friendly_source(source: str) -> str:
    return SOURCE_LABELS.get(source, source.replace("_", " ").title())


def _is_internal_or_error(text: str) -> bool:
    """Hide only raw tool/validation noise, not normal agent messages."""
    if not text or not text.strip():
        return True
    lower = text.lower()
    return (
        "validation error for " in lower
        or "field required [type=missing" in lower
        or "input_value={}" in lower
        or "for further information visit https://errors.pydantic" in lower
    )


async def _friendly_console(stream):
    """Consume the stream and print only user-friendly lines (no raw events or errors)."""
    last_processed = None
    streaming = False
    async for message in stream:
        if isinstance(message, TaskResult):
            last_processed = message
            continue
        if isinstance(message, Response):
            last_processed = message
            content = message.chat_message.to_text() if hasattr(message.chat_message, "to_text") else str(message.chat_message)
            if not _is_internal_or_error(content):
                label = _friendly_source(message.chat_message.source)
                print(f"\n{label}: {content}\n")
            continue
        if isinstance(message, UserInputRequestedEvent):
            continue
        if isinstance(message, ToolCallRequestEvent):
            print("Checking your request…")
            continue
        if isinstance(message, ToolCallExecutionEvent):
            continue
        if isinstance(message, ToolCallSummaryMessage):
            continue
        if isinstance(message, ModelClientStreamingChunkEvent):
            print(message.to_text(), end="", flush=True)
            streaming = True
            continue
        if isinstance(message, (TextMessage, MultiModalMessage)):
            if streaming:
                print()
                streaming = False
            content = message.to_text() if hasattr(message, "to_text") else str(message)
            if _is_internal_or_error(content):
                continue
            label = _friendly_source(message.source)
            print(f"\n{label}: {content}\n")
            continue
        # Skip other events (selector, etc.) without printing
    if last_processed is None:
        raise ValueError("No TaskResult or Response was processed.")
    return last_processed


def _followup_prompt(error: Exception) -> str:
    """Turn an error into a user-friendly follow-up question."""
    msg = str(error).lower()
    if "department" in msg or "missing" in msg:
        return "Which department is this request for? (e.g. Engineering, Marketing, HR)"
    if "budget" in msg or "amount" in msg:
        return "What is the estimated budget or amount for this request?"
    if "quantity" in msg:
        return "How many units do you need?"
    if "api" in msg or "key" in msg or "openai" in msg:
        return "There was a connection issue. Please check your setup and try again—or type your request again."
    return "Could you provide a bit more detail so we can continue? (e.g. department, quantity, budget)"

async def main() -> None:
    task = (
        "We need to procure 50 MacBooks for Engineering, budget around 75L INR, "
        "next quarter, prefer Apple Authorized Vendor. Process this request."
    )
    while True:
        print("\n--- Running procurement workflow ---\n")
        try:
            stream = team.run_stream(task=task)
            await _friendly_console(stream)
        except Exception as e:
            print("\n" + _followup_prompt(e) + "\n")
        task = input("\nEnter your response (or 'exit' to quit): ").strip()
        if not task or task.lower() == "exit":
            break


if __name__ == "__main__":
    asyncio.run(main())
