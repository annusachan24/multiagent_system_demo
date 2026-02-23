
"""
Multi-agent example: Planner → Executor → Reviewer (no tools).
Agents take turns in round-robin order. Termination is controlled by
multiple conditions: reviewer approval, max messages, or token cap.
"""

import asyncio

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import (
    FunctionalTermination,
    MaxMessageTermination,
    TextMentionTermination,
    TokenUsageTermination,
)
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

from contants import openai_api_key

MAX_MESSAGES = 9  # Up to 3 full rounds (planner → executor → reviewer per round)
APPROVAL_KEYWORD = "APPROVED"
MAX_TOTAL_TOKENS = 8_000  # Safety cap to avoid runaway cost

# Shared model client (no tools)
model_client = OpenAIChatCompletionClient(
    model="gpt-4.1-nano",
    api_key=openai_api_key,
)


# -----------------------------------------------------------------------------
# Agents
# -----------------------------------------------------------------------------
planner = AssistantAgent(
    name="planner",
    description="Breaks down tasks into clear, numbered steps. Outputs plans only; does not execute.",
    model_client=model_client,
    system_message=(
        "You are a planner. Given a task, break it down into clear, actionable steps. "
        "You must output a plan that includes a line starting with 'Steps:' followed by "
        "numbered steps. Do not execute—only plan. Be concise (at most 5 steps)."
    ),
)


executor = AssistantAgent(
    name="executor",
    description="Takes the planner's steps and describes how to execute each one. No tools—describes actions only.",
    model_client=model_client,
    system_message=(
        "You are an executor. You receive a plan from the planner. "
        "Describe how you would execute each step concretely, referencing the planner's step numbers. "
        "Do not use tools—only describe the actions. If no plan is present yet, ask for one."
    ),
)


reviewer = AssistantAgent(
    name="reviewer",
    description="Reviews the plan and execution; says APPROVED when satisfied or gives feedback for another round.",
    model_client=model_client,
    system_message=(
        "You are a reviewer, be very ciritcal about the plan and the execution. Review the planner's plan and the executor's execution. "
        "If both are satisfactory (clear, feasible, complete), end your message with exactly the word: APPROVED. "
        "If something is missing or could be improved, give brief feedback and do NOT say APPROVED—"
        "the team will do another round. Be concise."
    ),
)

# -----------------------------------------------------------------------------
# Termination conditions (stop when any of these is met)
# -----------------------------------------------------------------------------
# 1. Reviewer explicitly approves
approval_termination = TextMentionTermination(APPROVAL_KEYWORD, sources=["reviewer"])

# 2. Hard cap on number of messages (avoids infinite loops)
max_messages_termination = MaxMessageTermination(max_messages=MAX_MESSAGES)

# 3. Token budget (safety net for cost)
token_termination = TokenUsageTermination(max_total_token=MAX_TOTAL_TOKENS)

# 4. Custom condition: stop if any new message is from reviewer and contains APPROVED
#    (redundant with 1 but demonstrates FunctionalTermination)
def reviewer_said_approved(messages):
    for msg in messages:
        if getattr(msg, "source", None) != "reviewer":
            continue
        to_text = getattr(msg, "to_text", None)
        text = (to_text() if callable(to_text) else getattr(msg, "content", "")) or ""
        if APPROVAL_KEYWORD in text:
            return True
    return False

functional_termination = FunctionalTermination(reviewer_said_approved)

# Combined: stop when ANY condition is satisfied
termination = (
    approval_termination
    | max_messages_termination
    | token_termination
    | functional_termination
)


# -----------------------------------------------------------------------------
# Team
# -----------------------------------------------------------------------------
team = RoundRobinGroupChat(
    [planner, executor, reviewer],
    termination_condition=termination,
    max_turns=10,
)

async def main():
    task = input("Enter a task for the team (or press Enter for default): ").strip()
    if not task:
        task = "Organize a small team lunch next week: pick date, venue, and send a calendar invite."
    await Console(team.run_stream(task=task), output_stats=True)


if __name__ == "__main__":
    asyncio.run(main())