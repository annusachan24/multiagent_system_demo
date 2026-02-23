"""
Google ADK implementation of:
Planner → Executor → Reviewer (no tools)

- Deterministic DAG / state-machine
- Explicit state persistence
- Strong termination guarantees
"""

from typing import Dict, List
from dataclasses import dataclass, field

from google.adk.agents import LlmAgent
from google.adk.workflows import Workflow, step
from google.adk.conditions import Condition
from google.adk.runners import run_workflow

from google.generativeai import GenerativeModel

from constants import google_api_key

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
MODEL_NAME = "gemini-1.5-flash"
MAX_MESSAGES = 9
MAX_TOTAL_TOKENS = 8_000
APPROVAL_KEYWORD = "APPROVED"

# -----------------------------------------------------------------------------
# Model
# -----------------------------------------------------------------------------
model = GenerativeModel(
    model_name=MODEL_NAME,
    api_key=google_api_key,
)

# -----------------------------------------------------------------------------
# State
# -----------------------------------------------------------------------------
@dataclass
class AgentState:
    messages: List[Dict[str, str]] = field(default_factory=list)
    message_count: int = 0
    token_count: int = 0
    approved: bool = False

def estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)

# -----------------------------------------------------------------------------
# Agents
# -----------------------------------------------------------------------------
planner = LlmAgent(
    name="planner",
    model=model,
    system_prompt=(
        "You are a planner. Given a task, break it down into clear, actionable steps. "
        "You must output a plan that includes a line starting with 'Steps:' followed by "
        "numbered steps. Do not execute—only plan. Be concise (at most 5 steps)."
    ),
)

executor = LlmAgent(
    name="executor",
    model=model,
    system_prompt=(
        "You are an executor. You receive a plan from the planner. "
        "Describe how you would execute each step concretely, referencing the planner's step numbers. "
        "Do not use tools—only describe the actions. If no plan is present yet, ask for one."
    ),
)

reviewer = LlmAgent(
    name="reviewer",
    model=model,
    system_prompt=(
        "You are a reviewer. Review the planner's plan and the executor's execution. "
        "If both are satisfactory (clear, feasible, complete), "
        "end your message with exactly the word: APPROVED. "
        "Otherwise give brief feedback and do NOT say APPROVED."
    ),
)

# -----------------------------------------------------------------------------
# Workflow Steps
# -----------------------------------------------------------------------------
@step
def planner_step(state: AgentState) -> AgentState:
    response = planner.run(state.messages)

    state.messages.append({"role": "planner", "content": response})
    state.message_count += 1
    state.token_count += estimate_tokens(response)

    return state

@step
def executor_step(state: AgentState) -> AgentState:
    response = executor.run(state.messages)

    state.messages.append({"role": "executor", "content": response})
    state.message_count += 1
    state.token_count += estimate_tokens(response)

    return state

@step
def reviewer_step(state: AgentState) -> AgentState:
    response = reviewer.run(state.messages)

    state.messages.append({"role": "reviewer", "content": response})
    state.message_count += 1
    state.token_count += estimate_tokens(response)

    if APPROVAL_KEYWORD in response:
        state.approved = True

    return state

# -----------------------------------------------------------------------------
# Exit Conditions
# -----------------------------------------------------------------------------
class ShouldTerminate(Condition):
    def evaluate(self, state: AgentState) -> bool:
        return (
            state.approved
            or state.message_count >= MAX_MESSAGES
            or state.token_count >= MAX_TOTAL_TOKENS
        )

# -----------------------------------------------------------------------------
# Workflow Definition
# -----------------------------------------------------------------------------
workflow = Workflow(
    name="planner_executor_reviewer",
    initial_state=AgentState,
)

workflow.add_step(planner_step)
workflow.add_step(executor_step)
workflow.add_step(reviewer_step)

workflow.add_transition(planner_step, executor_step)
workflow.add_transition(executor_step, reviewer_step)
workflow.add_transition(
    reviewer_step,
    planner_step,
    condition=~ShouldTerminate(),  # loop if NOT terminating
)

workflow.set_exit_condition(ShouldTerminate())

# -----------------------------------------------------------------------------
# Runner
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    task = input("Enter a task (or press Enter for default): ").strip()
    if not task:
        task = "Organize a small team lunch next week: pick date, venue, and send a calendar invite."

    initial_state = AgentState(
        messages=[{"role": "user", "content": task}],
        token_count=estimate_tokens(task),
    )

    final_state = run_workflow(workflow, initial_state)

    print("\n--- Conversation ---\n")
    for msg in final_state.messages:
        print(f"{msg['role'].upper()}: {msg['content']}\n")
