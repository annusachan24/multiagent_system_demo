# Tasks: Selector Group Chat for Procurement (HIL)

**Input**: Design documents from `/specs/001-selector-group-chat/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Organization**: One implementation task (user requested "Break plan into a single task"). Delivers both User Story 1 (run procurement selector group chat) and User Story 2 (correct agent and tool wiring) in one increment.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (e.g. US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: Repository root with `hil/`; new code in `hil/selector_group_chat_with_hil.py`; existing `hil/prompts.py`, `hil/tools.py`.

---

## Phase 1: Implementation (Single Task)

**Purpose**: Implement the full procurement selector group chat so a user can run it with a natural-language request and get agent collaboration with human-in-the-loop.

**Goal**: One runnable entrypoint that builds six agents + UserProxyAgent, SelectorGroupChat, and runs the chat per plan and contract.

**Independent Test**: Run the script with a task string (e.g. "We need 50 MacBooks for Engineering, budget 75L INR, next quarter, Apple Authorized Vendor."); observe agents taking turns; receive a final recommendation or a request for human input; when human input is requested, respond in the same chat and see the flow continue.

- [x] T001 [US1] Implement procurement selector group chat in `hil/selector_group_chat_with_hil.py`: (1) Ensure `hil/prompts.py` imports tools from `hil.tools` (not `demo.tools`) so the HIL module is self-contained. (2) Build six `AssistantAgent` instances from `AGENT_CONFIG` and `AGENT_DESCRIPTIONS` in `hil/prompts.py`, each with `name`, `description`, `system_message` (prompt), and `tools` from `hil/tools.py` per agent. (3) Add a `UserProxyAgent` for human-in-the-loop. (4) Create `SelectorGroupChat` with a shared model client (e.g. `OpenAIChatCompletionClient`), custom `selector_prompt` using `{roles}`, `{history}`, `{participants}` and instructions for Intake first, then Policy/Finance/Vendor, then Reviewer, then Human when input needed, `MaxMessageTermination(max_messages=20)` (and optionally `TextMentionTermination("TERMINATE")`), and `allow_repeated_speaker=True`. (5) Implement the run entrypoint: accept a task string, call `Console(team.run_stream(task=task))` (or equivalent async run). Follow `specs/001-selector-group-chat/contracts/selector-group-chat-entrypoint.md` and `specs/001-selector-group-chat/research.md`. Code MUST follow PEP 8.

**Checkpoint**: At this point, the selector group chat is runnable; User Story 1 and User Story 2 are both satisfied (six agents with correct tools, human in the loop).

---

## Dependencies & Execution Order

- **Phase 1**: Single task T001; no dependencies. Completing T001 delivers the MVP (both user stories).

## Implementation Strategy

### MVP (Single Task)

1. Complete T001.
2. Run with an example procurement request from `quickstart.md` and confirm agents and tools behave per spec (SC-003, SC-004).

### Notes

- No separate test tasks were requested in the spec; validation is via manual run per quickstart.
- T001 is the only task; it is not marked [P] because it is the sole implementation unit.
