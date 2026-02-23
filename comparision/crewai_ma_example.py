"""
CrewAI implementation of:
Planner → Executor → Reviewer (no tools)

Functional parity with:
- AutoGen round-robin
- LangGraph state machine
- Google ADK workflow
"""

from crewai import Agent, Task, Crew, Process
from langchain_openai import ChatOpenAI

from constants import openai_api_key

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
MODEL_NAME = "gpt-4.1-nano"
MAX_ITERATIONS = 3              # ~3 full rounds
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
# Agents
# -----------------------------------------------------------------------------
planner = Agent(
    role="Planner",
    goal="Create a clear, concise execution plan",
    backstory=(
        "You are a careful planner who breaks tasks into clear, actionable steps. "
        "You never execute the task yourself."
    ),
    llm=llm,
    allow_delegation=False,
)

executor = Agent(
    role="Executor",
    goal="Explain how to execute the plan step by step",
    backstory=(
        "You are an executor who follows the planner's steps exactly. "
        "You describe concrete execution actions without using tools."
    ),
    llm=llm,
    allow_delegation=False,
)

reviewer = Agent(
    role="Reviewer",
    goal="Validate the plan and execution",
    backstory=(
        "You are a strict reviewer. If the plan and execution are clear, feasible, "
        "and complete, you end your response with exactly the word APPROVED."
    ),
    llm=llm,
    allow_delegation=False,
)

# -----------------------------------------------------------------------------
# Task templates
# -----------------------------------------------------------------------------
def planner_task(user_task: str) -> Task:
    return Task(
        description=(
            f"Task: {user_task}\n\n"
            "Create a plan with a line starting with 'Steps:' followed by numbered steps. "
            "Do NOT execute the steps. At most 5 steps."
        ),
        expected_output="A concise plan with numbered steps.",
        agent=planner,
    )

def executor_task() -> Task:
    return Task(
        description=(
            "Using the planner's steps, describe how each step would be executed. "
            "Reference the step numbers explicitly. Do not use tools."
        ),
        expected_output="Concrete execution description mapped to planner steps.",
        agent=executor,
        context=["planner"],
    )

def reviewer_task() -> Task:
    return Task(
        description=(
            "Review the planner's plan and the executor's execution. "
            "If both are satisfactory, end with exactly: APPROVED. "
            "Otherwise, give brief feedback without saying APPROVED."
        ),
        expected_output="Approval or concise feedback.",
        agent=reviewer,
        context=["planner", "executor"],
    )

# -----------------------------------------------------------------------------
# Runner (explicit control loop)
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    task = input("Enter a task (or press Enter for default): ").strip()
    if not task:
        task = "Organize a small team lunch next week: pick date, venue, and send a calendar invite."

    approved = False
    iteration = 0

    while not approved and iteration < MAX_ITERATIONS:
        iteration += 1
        print(f"\n=== Iteration {iteration} ===\n")

        crew = Crew(
            agents=[planner, executor, reviewer],
            tasks=[
                planner_task(task),
                executor_task(),
                reviewer_task(),
            ],
            process=Process.sequential,
            verbose=True,
        )

        result = crew.kickoff()

        if APPROVAL_KEYWORD in result:
            approved = True
            print("\n✅ Reviewer approved the result.\n")
        else:
            print("\n🔁 Reviewer requested improvements. Running another round...\n")

    if not approved:
        print("⚠️ Max iterations reached without approval.")
