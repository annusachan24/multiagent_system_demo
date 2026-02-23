# Tasks: MCP Server Hosting Tools in SSE Mode

**Input**: Design documents from `/specs/002-mcp-sse-tools/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Not requested in the feature specification; no test tasks included.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- All new/modified Python files live under `hil_mcp/` at repository root (per plan.md).
- Optional tests under `tests/` (e.g. `tests/integration/test_hil_mcp_server.py`) if added later.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Package structure, dependencies, and lint for `hil_mcp/`.

- [x] T001 Create `hil_mcp/` package with `__init__.py` (empty or minimal) at repo root per plan.md structure.
- [x] T002 Add MCP and ASGI dependencies: add `mcp` and `autogen-ext[mcp]` and an ASGI server (e.g. `uvicorn` or `hypercorn`) to `requirements.txt` or project docs so the server and client can run.
- [x] T003 [P] Ensure PEP 8 / Ruff (or project linter) is configured and that `hil_mcp/` is included; all new code in `hil_mcp/` must pass.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Tool source that the server and contracts depend on. No user story implementation can start without this.

**⚠️ CRITICAL**: Server and all user stories depend on `hil_mcp/tools.py` existing.

- [x] T004 Copy `hil/tools.py` to `hil_mcp/tools.py` preserving all function names, signatures, and docstrings so the server can import and register tools from `hil_mcp.tools` with no dependency on `hil`.

**Checkpoint**: Foundation ready — User Story 1 (server discovery) can start.

---

## Phase 3: User Story 1 - Expose Tools for Discovery (Priority: P1) 🎯 MVP

**Goal**: Operator runs an MCP server over SSE; clients can connect and receive the full list of tools and their parameter schemas.

**Independent Test**: Start the server, connect with an MCP client (or test script), request the list of tools; verify tool names and input schemas match the set in `specs/002-mcp-sse-tools/contracts/tool-list.md` within 5 seconds.

### Implementation for User Story 1

- [x] T005 [US1] Implement `hil_mcp/server.py`: create MCP server using MCP Python SDK with SSE transport (e.g. `SseServerTransport` or FastMCP over SSE); load tool functions from `hil_mcp.tools` and register them with the MCP runtime; expose list-tools and accept client connections per `specs/002-mcp-sse-tools/contracts/mcp-sse-server-entrypoint.md`.
- [x] T006 [US1] In `hil_mcp/server.py`, add startup behavior: if `hil_mcp.tools` cannot be imported or no tools are registered, exit immediately with a clear, actionable error message to stderr and do not start the HTTP/SSE listener (FR-007, SC-004).
- [x] T007 [US1] Add an ASGI entrypoint (e.g. in `hil_mcp/server.py` or a `__main__` block) so the server can be run with `python -m hil_mcp.server` or `uvicorn hil_mcp.server:app` (or equivalent); document host/port (e.g. `http://127.0.0.1:8000`) for clients.

**Checkpoint**: User Story 1 is done when a client can connect over SSE and get the full tool list with schemas within 5 seconds; failed tool load exits with a clear error.

---

## Phase 4: User Story 2 - Invoke Tools via SSE (Priority: P2)

**Goal**: Clients can call a tool by name with arguments and receive the tool result or a structured error (invalid/missing args, tool not found).

**Independent Test**: With the server running, send valid tool name + arguments and assert correct result; send invalid or missing arguments and assert clear error; request unknown tool name and assert tool-not-found error (SC-002, FR-006).

### Implementation for User Story 2

- [x] T008 [US2] In `hil_mcp/server.py`, implement tool invocation: on call-tool request, validate that the tool name exists in the registered set; validate arguments against the tool’s input schema; if valid, execute the tool and return the result; if invalid or tool not found, return a structured error response (no crash) per FR-006 and acceptance scenarios 2–3.
- [x] T009 [US2] Update `hil_mcp/selector_group_chat_with_hil_mcp.py`: replace in-process tools from `AGENT_CONFIG` with tools obtained from the MCP server using `autogen_ext.tools.mcp` — use `SseServerParams` with the server URL (matching the entrypoint contract) and `mcp_server_tools(server_params)` to get tool adapters, then pass the appropriate tools to each `AssistantAgent` per agent role (intake, policy, finance, vendor_risk, reviewer) per research.md and plan.md; keep using `hil.prompts` for AGENT_CONFIG prompts and AGENT_DESCRIPTIONS.

**Checkpoint**: User Story 2 is done when clients receive correct results for valid tool calls and clear errors for invalid/unknown tool requests; selector group chat runs using tools from the MCP server.

---

## Phase 5: User Story 3 - Operate Server Reliably (Priority: P3)

**Goal**: Server reports readiness on start, supports multiple concurrent clients without mixing responses, and shuts down gracefully.

**Independent Test**: Start server and confirm a readiness message/listening state; connect two clients and invoke tools from each, confirm each client gets only its own results; stop the server and confirm existing connections close and no new connections are accepted (SC-003).

### Implementation for User Story 3

- [x] T010 [US3] In `hil_mcp/server.py`, ensure the server logs or prints a clear readiness message when the SSE listener is accepting connections (e.g. host and port) per contract and SC-001 context.
- [x] T011 [US3] Ensure shutdown behavior: on process stop (SIGTERM/SIGINT), close existing SSE sessions gracefully and stop accepting new connections; rely on MCP SDK session handling so multiple clients get distinct sessions and responses are not mixed (FR-005, SC-003).

**Checkpoint**: User Story 3 is done when start/stop and multi-client behavior match the spec and contract.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, quickstart validation, and consistency.

- [x] T012 Run through `specs/002-mcp-sse-tools/quickstart.md`: start the MCP server, then run `hil_mcp/selector_group_chat_with_hil_mcp.py` with the example task; confirm tool discovery, tool use, and flow complete as described; fix any path or dependency issues.
- [x] T013 [P] Update `specs/002-mcp-sse-tools/quickstart.md` or project README with the exact run commands and port/URL for the MCP server and selector chat if they differ from the current quickstart text.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start first.
- **Phase 2 (Foundational)**: Depends on Phase 1 — blocks all user stories.
- **Phase 3 (US1)**: Depends on Phase 2 — server needs `hil_mcp/tools.py`.
- **Phase 4 (US2)**: Depends on Phase 3 — invocation and client build on the running server contract.
- **Phase 5 (US3)**: Depends on Phase 3 (and Phase 4 for full E2E) — lifecycle and concurrency apply to the same server.
- **Phase 6 (Polish)**: Depends on Phases 3–5 — validate full flow and docs.

### User Story Dependencies

- **US1 (P1)**: After Foundational only — discovery and list tools.
- **US2 (P2)**: After US1 — call tool and selector chat client.
- **US3 (P3)**: After US1 — startup/shutdown and multi-client; can overlap with US2.

### Within Each User Story

- US1: T005 (server + list) → T006 (fail fast) → T007 (entrypoint).
- US2: T008 (call + validation) → T009 (selector chat uses MCP tools).
- US3: T010 (readiness) and T011 (shutdown/sessions) can be done in either order.

### Parallel Opportunities

- Phase 1: T003 [P] can run in parallel with T001/T002 after structure and deps are decided.
- Phase 5: T010 and T011 are independent (readiness vs shutdown).
- Phase 6: T013 [P] (docs) can run in parallel with T012 (quickstart run).

---

## Parallel Example: User Story 1

```bash
# Sequential for US1 (server is one module):
# T005 → T006 → T007
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T003).
2. Complete Phase 2: Foundational (T004).
3. Complete Phase 3: User Story 1 (T005–T007).
4. **STOP and VALIDATE**: Connect with an MCP client and list tools within 5 seconds; try starting without `hil_mcp/tools.py` and confirm clear exit with error.
5. Demo: server running, tool list discoverable.

### Incremental Delivery

1. Setup + Foundational → tool source and package ready.
2. Add US1 → Server exposes tools over SSE; validate discovery (MVP).
3. Add US2 → Tool invocation and selector chat using MCP tools; validate calls and errors.
4. Add US3 → Reliable start/stop and multi-client; validate lifecycle.
5. Polish → Quickstart and docs; full flow validated.

### Suggested MVP Scope

- **MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1)**  
  Delivers: MCP server in SSE mode, tools from `hil_mcp/tools.py`, clients can discover the full tool list. Total tasks in MVP: T001–T007 (7 tasks).

---

## Notes

- [P] tasks use different files or concerns and have no ordering dependency within the phase.
- [Story] labels (US1, US2, US3) map to spec.md user stories for traceability.
- Each user story has a checkpoint and independent test criterion.
- No test tasks were added; the spec does not require TDD or explicit test tasks.
- Commit after each task or logical group; stop at any checkpoint to validate that story.
