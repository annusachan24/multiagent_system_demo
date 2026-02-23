"""
OpenAI Swarm-style implementation of:
Planner → Executor → Reviewer (no tools)

Swarm principles:
- Lightweight agents
- Explicit handoffs
- Shared context
- User-controlled orchestration
"""

from dataclasses import dataclass, field
from typing import List, Dict

from openai import OpenAI

from constants import openai_api_key

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
MODEL = "gpt-4.1-nano"
MAX_ROUNDS = 3
MAX_MESSAGES = 9
MAX_TOTAL_TOKENS = 8_000
APPROVAL_KEYWORD = "APPROVED"

# -----------------------------------------------------------------------------
# Client
# -----------------------------------------------------------------------------
client = OpenAI(api_key=openai_api_key)

# -----------------------------------------------------------------------------
# Shared Swarm Context
# -----------------------------------------------------------------------------
@dataclass
class SwarmContext:
    messages: List[Dict[str, str]] = field(default_factory=list)
    message_count: int = 0
    token_count: int = 0
    approved: bool = False

def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)

# -----------------------------------------------------------------------------
# Base Agent
# -----------------------------------------------------------------------------
class SwarmAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt

    def run(self, context: SwarmContext) -> str:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": self.system_prompt},
                *context.messages,
            ],
        )

        text = response.choices[0].message.content

        context.messages.append(
            {"role": self.name, "content": text}
        )
        context.message_count += 1
        context.token_count += estimate_tokens(text)

        return text

# -----------------------------------------------------------------------------
# Agents
# -----------------------------------------------------------------------------
planner = SwarmAgent(
    name="planner",
    system_prompt=(
        "You are a planner. Given a task, break it down into clear, actionable steps. "
        "You must output a plan that includes a line starting with 'Steps:' followed by "
        "numbered steps. Do not execute—only plan. Be concise (at most 5 steps)."
    ),
)

executor = SwarmAgent(
    name="executor",
    system_prompt=(
        "You are an executor. You receive a plan from the planner. "
        "Describe how you would execute each step concretely, referencing the planner's step numbers. "
        "Do not use tools—only describe the actions. If no plan is present yet, ask for one."
    ),
)

reviewer = SwarmAgent(
    name="reviewer",
    system_prompt=(
        "You are a reviewer. Review the planner's plan and the executor's execution. "
        "If both are satisfactory (clear, feasible, complete), "
        "end your message with exactly the word: APPROVED. "
        "Otherwise give brief feedback and do NOT say APPROVED."
    ),
)

# -----------------------------------------------------------------------------
# Termination Check
# -----------------------------------------------------------------------------
def should_terminate(ctx: SwarmContext) -> bool:
    return (
        ctx.approved
        or ctx.message_count >= MAX_MESSAGES
        or ctx.token_count >= MAX_TOTAL_TOKENS
    )

# -----------------------------------------------------------------------------
# Runner (Swarm Orchestration)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    task = input("Enter a task (or press Enter for default): ").strip()
    if not task:
        task = "Organize a small team lunch next week: pick date, venue, and send a calendar invite."

    context = SwarmContext(
        messages=[{"role": "user", "content": task}],
        token_count=estimate_tokens(task),
    )

    round_num = 0

    while not should_terminate(context) and round_num < MAX_ROUNDS:
        round_num += 1
        print(f"\n=== Round {round_num} ===\n")

        planner.run(context)
        if should_terminate(context):
            break

        executor.run(context)
        if should_terminate(context):
            break

        review_text = reviewer.run(context)

        if APPROVAL_KEYWORD in review_text:
            context.approved = True
            print("\n✅ Reviewer approved the result.\n")
            break

        print("\n🔁 Reviewer requested changes. Continuing swarm...\n")

    print("\n--- Conversation ---\n")
    for msg in context.messages:
        print(f"{msg['role'].upper()}: {msg['content']}\n")

    if not context.approved:
        print("⚠️ Terminated without approval.")
