"""
Procurement selector group chat using HIL agents and MCP tools.

Builds six participants (five AssistantAgents + UserProxyAgent) from hil.prompts;
tools are obtained from the MCP server (SSE) via autogen_ext.tools.mcp.
Run from repo root with MCP server already running:
  python -m hil_mcp.selector_group_chat_with_hil_mcp [task]
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Sequence

# Ensure repo root is on path for contants when run as script from any cwd
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import (
    HandoffTermination,
    MaxMessageTermination,
    TextMentionTermination,
)
from autogen_agentchat.teams import SelectorGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.tools.mcp import SseServerParams, mcp_server_tools

from contants import openai_api_key
from hil.prompts import AGENT_CONFIG, AGENT_DESCRIPTIONS

# MCP server SSE endpoint (server uses /sse by default; override with HIL_MCP_SERVER_URL)
DEFAULT_MCP_SERVER_URL = "http://127.0.0.1:8000/sse"
MCP_SERVER_URL = os.environ.get("HIL_MCP_SERVER_URL", DEFAULT_MCP_SERVER_URL)

# Model client shared by selector and assistant agents
model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key=openai_api_key,
)

# Human-readable names for the selector (must match agent .name)
AGENT_NAMES = {
    "intake_agent": "IntakeAgent",
    "policy_agent": "PolicyAgent",
    "finance_agent": "FinanceAgent",
    "vendor_risk_agent": "VendorRiskAgent",
    "reviewer_agent": "ReviewerAgent",
    "human_proxy_agent": "HumanProxyAgent",
}

# Tool names per agent (from AGENT_CONFIG; used to filter MCP tools)
AGENT_TOOL_NAMES = {
    "intake_agent": ["extract_procurement_fields", "validate_required_fields", "create_purchase_request"],
    "policy_agent": ["check_policy", "approval_matrix"],
    "finance_agent": ["check_budget", "forecast_spend"],
    "vendor_risk_agent": ["lookup_vendor", "vendor_risk_score"],
    "reviewer_agent": [],
    "human_proxy_agent": [],
}


def _build_assistant_agents(tools_by_name: dict):
    """Build five AssistantAgents from AGENT_CONFIG with MCP tool adapters (exclude human_proxy)."""
    agents = []
    for key in (
        "intake_agent",
        "policy_agent",
        "finance_agent",
        "vendor_risk_agent",
        "reviewer_agent",
    ):
        config = AGENT_CONFIG[key]
        name = AGENT_NAMES[key]
        description = AGENT_DESCRIPTIONS.get(key, "")
        want = AGENT_TOOL_NAMES.get(key, [])
        agent_tools = [tools_by_name[n] for n in want if n in tools_by_name]
        agents.append(
            AssistantAgent(
                name=name,
                description=description,
                model_client=model_client,
                system_message=config["prompt"],
                tools=agent_tools,
            )
        )
    return agents


def _build_user_proxy_agent():
    """Build UserProxyAgent for human-in-the-loop."""
    description = AGENT_DESCRIPTIONS.get("human_proxy_agent", "")
    return UserProxyAgent(
        name=AGENT_NAMES["human_proxy_agent"],
        description=description,
    )


HUMAN_PROXY_NAME = AGENT_NAMES["human_proxy_agent"]


def _last_message_text(messages: Sequence) -> str:
    """Extract text from the last message for selector logic."""
    if not messages:
        return ""
    last = messages[-1]
    to_text = getattr(last, "to_text", None)
    if callable(to_text):
        try:
            return to_text() or ""
        except Exception:
            pass
    return getattr(last, "content", "") or ""


def _selector_func(messages: Sequence) -> str | None:
    """
    When an agent requests human input, force the next speaker to HumanProxyAgent
    so the run stops and waits for the user. Otherwise use default model selection.
    """
    if not messages:
        return None
    last = messages[-1]
    source = getattr(last, "source", "")
    # After the human has spoken, use default selection
    if source == HUMAN_PROXY_NAME:
        return None
    text = _last_message_text(messages)
    text_upper = text.upper()
    # Agent is asking for human input: must route to human so run stops for input
    if "HUMAN_INPUT_NEEDED" in text_upper:
        return HUMAN_PROXY_NAME
    if "HUMAN_ACTION_REQUIRED" in text_upper or "ESCALATE_TO_HUMAN" in text_upper:
        return HUMAN_PROXY_NAME
    if "INCOMPLETE" in text_upper and "MISSING_FIELDS" in text_upper:
        return HUMAN_PROXY_NAME
    # Intake's tool result shows missing required fields: give Intake one more
    # turn to ask the user in natural language (not the raw dict), then we
    # route to Human when HUMAN_INPUT_NEEDED appears
    if source == AGENT_NAMES["intake_agent"] and (
        "ESTIMATED_BUDGET': NONE" in text_upper
        or "QUANTITY': NONE" in text_upper
        or "'DEPARTMENT': NONE" in text_upper
    ):
        return AGENT_NAMES["intake_agent"]
    return None


def _build_team(tools_by_name: dict):
    """Build SelectorGroupChat with all participants and termination."""
    participants = _build_assistant_agents(tools_by_name) + [_build_user_proxy_agent()]

    text_mention = TextMentionTermination("exit")
    text_mention_terminate = TextMentionTermination("terminate")
    text_mention_TERMINATE = TextMentionTermination("TERMINATE")
    max_messages = MaxMessageTermination(max_messages=20)
    # Stop when control is handed to UserProxyAgent so the run returns instead of blocking
    handoff_to_human = HandoffTermination(target=HUMAN_PROXY_NAME)
    termination = text_mention | text_mention_terminate | text_mention_TERMINATE | max_messages | handoff_to_human

    selector_prompt = """Select an agent to perform the next step.

{roles}

Current conversation context:
{history}

Read the conversation above. Select one agent from {participants} to perform the next task.
- For a new request, choose IntakeAgent first to extract and structure the request.
- After intake is READY_FOR_REVIEW, choose PolicyAgent, FinanceAgent, or VendorRiskAgent as needed.
- After validations, choose ReviewerAgent to synthesize and decide.
- When the conversation indicates human input is needed (HUMAN_INPUT_NEEDED, ESCALATE_TO_HUMAN, or final decision), choose HumanProxyAgent.
- After the human has confirmed an AUTO_APPROVE (e.g. said "ok", "approved", "yes"), choose IntakeAgent to create the purchase request (PR) and close the flow.
Only select one agent.
"""

    return SelectorGroupChat(
        participants,
        model_client=model_client,
        termination_condition=termination,
        selector_prompt=selector_prompt,
        selector_func=_selector_func,
        allow_repeated_speaker=True,
    )


async def run(task: str):
    """Run the procurement selector group chat with the given task string."""
    server_params = SseServerParams(url=MCP_SERVER_URL)
    mcp_tools = await mcp_server_tools(server_params)
    tools_by_name = {t.name: t for t in mcp_tools}
    team = _build_team(tools_by_name)
    await Console(team.run_stream(task=task))


def main():
    """Entrypoint: run with example task or first CLI argument."""
    default_task = (
        "We need 50 MacBooks for Engineering, budget 75L INR, next quarter. "
        "Prefer Apple Authorized Vendor."
    )
    task = default_task
    if len(sys.argv) > 1:
        task = " ".join(sys.argv[1:])
    asyncio.run(run(task))


if __name__ == "__main__":
    main()
