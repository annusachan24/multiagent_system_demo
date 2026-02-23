# Tasks: Web UI for Procurement Selector Group Chat (Streamlit)

**Input**: Design documents from `/specs/001-streamlit-ui-hil/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not requested in spec; no test tasks included.

**Organization**: Tasks are grouped by user story for independent implementation and validation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2)
- Include exact file paths in descriptions

## Path Conventions

- Single project: `hil/` at repository root; new app `hil/streamlit_ui.py` per plan.md

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add Streamlit and ensure environment supports the new UI entrypoint.

- [x] T001 Add Streamlit to requirements.txt and ensure Python 3.10+ and existing autogen-agentchat, autogen-ext[openai] remain
- [x] T002 [P] Ensure PEP 8 / Ruff (or project linter) config includes hil/ so new hil/streamlit_ui.py will be linted

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Expose the selector group chat so the Streamlit app can run it with a custom UserInputManager and stream consumer (no Console output).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T003 In hil/selector_group_chat_with_hil.py export build_team (e.g. `build_team = _build_team` or `def build_team(): return _build_team()`) so hil/streamlit_ui.py can get the team and call team.run_stream(task=task) with a custom stream consumer and UserInputManager; keep existing run(task) and main() for CLI unchanged

**Checkpoint**: Foundation ready — Streamlit can import team and run_stream.

---

## Phase 3: User Story 1 — Run Procurement Chat from Web (Priority: P1) — MVP

**Goal**: User can open the web UI, enter a procurement request, start the chat, see agent messages in order, and submit human input when the workflow asks (FR-001–FR-004, FR-006).

**Independent Test**: Open the UI, enter "buy 50 MacBooks for Engineering", start the chat, see agent messages with clear speaker labels; when prompted for human input, type a response and submit; conversation continues or ends as designed.

### Implementation for User Story 1

- [x] T004 [US1] Create hil/streamlit_ui.py with app skeleton: st.set_page_config, session state for task, messages (list of {speaker, content}), status (idle|running|waiting_for_input|done|error), error_message, and a thread-safe queue for user input; layout with area for messages and a place for initial task input and Start action
- [x] T005 [US1] In hil/streamlit_ui.py implement stream consumer: in a dedicated thread run asyncio.run(team.run_stream(task=task)) with UserInputManager(callback) where callback blocks on queue.get() and returns the string; consume the stream (async for item in stream), map BaseAgentEvent/BaseChatMessage to (speaker, content), append to session state messages; on TaskResult set status=done
- [x] T006 [US1] In hil/streamlit_ui.py when status is waiting_for_input show st.chat_input (or text input + submit); on submit put user reply in the queue, call st.rerun() so the chat thread can continue; set status=waiting_for_input when the stream consumer detects human turn (per research: callback blocks on queue.get())
- [x] T007 [US1] In hil/streamlit_ui.py wire Start to launch the chat thread with the initial task from session state; set status=running when thread starts; show a loading indicator (e.g. st.spinner) when status is running
- [x] T008 [US1] In hil/streamlit_ui.py add error handling: wrap chat run in try/except, on configuration or backend failure set status=error and error_message to a clear, non-technical message (FR-006, SC-004); display error_message in the UI when status is error

**Checkpoint**: User Story 1 is functional — full exchange and human input work from the browser.

---

## Phase 4: User Story 2 — Visually Polished, Modern Experience (Priority: P2)

**Goal**: Interface has a cohesive, modern look: clear layout, typography, theme, scrollable chat, and loading state (FR-005, edge case).

**Independent Test**: Open the UI; confirm dedicated chat area, clear input placement, consistent styling, and scrollable message history; when the run is active, a loading/progress indicator is visible.

### Implementation for User Story 2

- [ ] T009 [US2] In hil/streamlit_ui.py apply consistent theme and layout: use st.chat_message for each message with speaker as role/label, dedicated chat container and clear input placement; add .streamlit/config.toml or st.set_page_config for a modern base theme (e.g. base light/dark) per research
- [ ] T010 [US2] In hil/streamlit_ui.py use st.chat_message and st.chat_input for message display and user input; ensure message history is scrollable (e.g. container with messages and scroll) so long conversations remain usable (FR-005, spec acceptance scenario 3)
- [ ] T011 [US2] In hil/streamlit_ui.py show a loading/progress indicator (e.g. st.spinner("Running…") or status text) when status is running so the user does not assume the app has frozen (spec edge case)

**Checkpoint**: User Stories 1 and 2 are complete — working chat with a polished UI.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Validation and code quality.

- [ ] T012 Run quickstart.md validation: from repo root run `streamlit run hil/streamlit_ui.py`, complete one full exchange (task + at least one human response), and confirm a config/backend error shows a clear, non-technical message in the UI
- [ ] T013 [P] Code cleanup and PEP 8 pass for hil/streamlit_ui.py (and any new files under hil/ for this feature)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately.
- **Phase 2 (Foundational)**: Depends on Phase 1 — blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2 — MVP.
- **Phase 4 (US2)**: Depends on Phase 3 (builds on same hil/streamlit_ui.py).
- **Phase 5 (Polish)**: Depends on Phase 4.

### User Story Dependencies

- **US1 (P1)**: After Foundational; no dependency on US2.
- **US2 (P2)**: After US1; enhances the same app (layout, theme, loading).

### Parallel Opportunities

- T001 and T002 can run in parallel (Setup).
- T012 and T013 can run in parallel (Polish).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (Streamlit in requirements, lint config).
2. Complete Phase 2: Export build_team in hil/selector_group_chat_with_hil.py.
3. Complete Phase 3: Implement hil/streamlit_ui.py (stream consumer, UserInputManager queue, Start, human input, errors).
4. **STOP and VALIDATE**: Run quickstart flow — one full exchange and one human response.
5. Demo MVP.

### Incremental Delivery

1. Setup + Foundational → ready for UI work.
2. Add US1 → test independently → MVP.
3. Add US2 → polish layout/theme/loading → full spec.
4. Polish → quickstart validation and PEP 8.

---

## Notes

- [P] tasks use different files or have no ordering dependency.
- [US1]/[US2] map to spec user stories for traceability.
- No test tasks; spec does not require them.
- Commit after each task or logical group.
- Validate at each checkpoint before moving on.
