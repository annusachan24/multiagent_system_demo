"""
LangGraph version of:
Planner → Executor → Reviewer (no tools)

Functional equivalence to the AutoGen example:
- Deterministic round-robin agent flow
- Shared state
- Multiple termination conditions:
  - Reviewer approval
  - Max messages
  - Token budget (approx)
"""

from typing import TypedDict, List, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage

from constants import openai_api_key

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
MODEL_NAME = "gpt-4.1-nano"
MAX_MESSAGES = 9          # Same as AutoGen example
MAX_TOTAL_TOKENS = 8_000  # Soft safety cap
APPROVAL_KEYWORD = "APPROVED"

# -----------------------------------------------------------------------------
# LLM
# -----------------------------------------------------------------------------
llm = ChatOpenAI(
    model=MODEL_NAME,
    api_key=openai_api_key,
    temperature=0,
)

# -----------------------------------------------------------------------------
# State definition
# -----------------------------------------------------------------------------
class AgentState(TypedDict):
    messages: List[AIMessage]
    turn: Literal["planner", "executor", "reviewer"]
    message_count: int
    token_count: int
    approved: bool

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def estimate_tokens(text: str) -> int:
    """Rough token estimator (good enough for safety cap)."""
    return max(1, len(text) // 4)

def call_agent(system_prompt: str, messages: List[AIMessage]) -> AIMessage:
    response = llm(
        [SystemMessage(content=system_prompt)] + messages
    )
    return AIMessage(content=response.content)

# -----------------------------------------------------------------------------
# Agent nodes
# -----------------------------------------------------------------------------
def planner_node(state: AgentState) -> AgentState:
    msg = call_agent(
        system_prompt=(
            "You are a planner. Given a task, break it down into clear, actionable steps. "
            "You must output a plan that includes a line starting with 'Steps:' followed by "
            "numbered steps. Do not execute—only plan. Be concise (at most 5 steps)."
        ),
        messages=state["messages"],
    )

    return {
        **state,
        "messages": state["messages"] + [msg],
        "turn": "executor",
        "message_count": state["message_count"] + 1,
        "token_count": state["token_count"] + estimate_tokens(msg.content),
    }

def executor_node(state: AgentState) -> AgentState:
    msg = call_agent(
        system_prompt=(
            "You are an executor. You receive a plan from the planner. "
            "Describe how you would execute each step concretely, referencing the planner's step numbers. "
            "Do not use tools—only describe the actions. If no plan is present yet, ask for one."
        ),
        messages=state["messages"],
    )

    return {
        **state,
        "messages": state["messages"] + [msg],
        "turn": "reviewer",
        "message_count": state["message_count"] + 1,
        "token_count": state["token_count"] + estimate_tokens(msg.content),
    }

def reviewer_node(state: AgentState) -> AgentState:
    msg = call_agent(
        system_prompt=(
            "You are a reviewer. Review the planner's plan and the executor's execution. "
            "If both are satisfactory (clear, feasible, complete), end your message with exactly the word: APPROVED. "
            "If something is missing or could be improved, give brief feedback and do NOT say APPROVED."
        ),
        messages=state["messages"],
    )

    approved = APPROVAL_KEYWORD in msg.content

    return {
        **state,
        "messages": state["messages"] + [msg],
        "turn": "planner",
        "approved": approved,
        "message_count": state["message_count"] + 1,
        "token_count": state["token_count"] + estimate_tokens(msg.content),
    }

# -----------------------------------------------------------------------------
# Routing / termination logic
# -----------------------------------------------------------------------------
def router(state: AgentState):
    # 1. Reviewer approval
    if state.get("approved"):
        return END

    # 2. Max messages
    if state["message_count"] >= MAX_MESSAGES:
        return END

    # 3. Token cap
    if state["token_count"] >= MAX_TOTAL_TOKENS:
        return END

    # Round-robin
    return state["turn"]

# -----------------------------------------------------------------------------
# Graph
# -----------------------------------------------------------------------------
graph = StateGraph(AgentState)

graph.add_node("planner", planner_node)
graph.add_node("executor", executor_node)
graph.add_node("reviewer", reviewer_node)

graph.set_entry_point("planner")

graph.add_conditional_edges(
    "planner", router,
    {
        "executor": "executor",
        END: END,
    },
)

graph.add_conditional_edges(
    "executor", router,
    {
        "reviewer": "reviewer",
        END: END,
    },
)

graph.add_conditional_edges(
    "reviewer", router,
    {
        "planner": "planner",
        END: END,
    },
)

app = graph.compile()

# -----------------------------------------------------------------------------
# Runner
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    task = input("Enter a task (or press Enter for default): ").strip()
    if not task:
        task = "Organize a small team lunch next week: pick date, venue, and send a calendar invite."

    state: AgentState = {
        "messages": [HumanMessage(content=task)],
        "turn": "planner",
        "message_count": 0,
        "token_count": estimate_tokens(task),
        "approved": False,
    }

    final_state = app.invoke(state)

    print("\n--- Conversation ---\n")
    for msg in final_state["messages"]:
        role = msg.__class__.__name__.replace("Message", "")
        print(f"{role}: {msg.content}\n")
