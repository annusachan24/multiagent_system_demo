# Implementation Plan: MCP Server Hosting Tools in SSE Mode

**Branch**: `002-mcp-sse-tools` | **Date**: 2025-02-21 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/002-mcp-sse-tools/spec.md`

**User planning context**: Build an MCP server in SSE mode; copy tools from `hil/tools.py`; keep Python files in `hil_mcp/`; `hil_mcp/selector_group_chat_with_hil_mcp.py` must use tools from this MCP server.

## Summary

Implement an MCP server that exposes procurement tools over SSE, loading tool implementations from a module in `hil_mcp/` (copied from `hil/tools.py`). A second component, `hil_mcp/selector_group_chat_with_hil_mcp.py`, will act as an MCP client: it will connect to this server via SSE and supply the discovered tools to the existing SelectorGroupChat agents instead of in-process callables. This aligns with the constitution: tools are hosted via MCP and consumed by Autogen through the MCP client.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: MCP Python SDK (`mcp`), Autogen (autogen-agentchat, autogen-ext with MCP and OpenAI), ASGI server (e.g. Uvicorn/Hypercorn for SSE).  
**Storage**: N/A (stateless tool execution).  
**Testing**: pytest (unit for tool behavior; integration for server list/invoke and client flow).  
**Target Platform**: Local/dev and standard HTTP (SSE) for server; same process or remote for client.  
**Project Type**: Single (monorepo with `hil_mcp/` as the feature package).  
**Performance Goals**: Tool discovery within 5s, correct tool results; support ≥2 concurrent SSE clients.  
**Constraints**: PEP 8; tools only via MCP; no ad-hoc in-process tool binding in the selector chat.  
**Scale/Scope**: One MCP server process, multiple agents in one SelectorGroupChat using one MCP client session to that server.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **PEP 8**: Linting/formatting (e.g. Ruff/Black) configured; all new code in `hil_mcp/` passes.
- **Autogen**: Selector group chat remains implemented with Autogen (SelectorGroupChat, AssistantAgent, UserProxyAgent); agent roles and prompts remain as in `hil`; only the tool source changes from in-process list to MCP-sourced tools.
- **MCP**: Agent tools are hosted via the new MCP server (SSE) and consumed by `selector_group_chat_with_hil_mcp.py` via `autogen_ext.tools.mcp` (e.g. `SseServerParams` + `mcp_server_tools`); no ad-hoc in-process tool bypass.

**Post–Phase 1 re-check**: All three principles still satisfied. research.md, data-model.md, contracts, and quickstart.md do not introduce violations.

## Project Structure

### Documentation (this feature)

```text
specs/002-mcp-sse-tools/
├── plan.md              # This file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1 (MCP server entrypoint, tool list)
└── tasks.md             # Phase 2 (/speckit.tasks)
```

### Source Code (repository root)

All new and modified Python files for this feature live under `hil_mcp/`:

```text
hil_mcp/
├── tools.py                    # Tool implementations (copied from hil/tools.py)
├── server.py                   # MCP server: SSE transport, loads tools from tools.py, exposes list + call
├── selector_group_chat_with_hil_mcp.py   # SelectorGroupChat entrypoint; uses MCP client (SSE) for tools
└── (optional) __main__.py      # e.g. python -m hil_mcp runs server or client per arg
```

- **tools.py**: Copy of `hil/tools.py` (same function names and signatures) so the server has no dependency on `hil` and the tool set is self-contained in `hil_mcp/`.
- **server.py**: Starts MCP over SSE (using MCP Python SDK SSE server transport); registers tools from `hil_mcp.tools`; supports list tools and call tool; fails fast if tool module cannot be loaded.
- **selector_group_chat_with_hil_mcp.py**: Builds the same participant set as the existing HIL selector chat (from `hil.prompts`), but instead of `config["tools"]` from AGENT_CONFIG, obtains tools from the MCP server via `autogen_ext.tools.mcp` (SseServerParams + mcp_server_tools). Assumes the MCP server is already running (e.g. started separately or via a documented quickstart).

**Structure Decision**: Single package `hil_mcp/` under repo root. No new top-level apps; tests can live in `tests/` with namespaced modules (e.g. `tests/integration/test_hil_mcp_server.py`, `tests/unit/hil_mcp/test_tools.py`) or under `hil_mcp/tests/` if the project prefers feature-local tests.

## Complexity Tracking

No constitution violations. Tools are hosted on MCP; Autogen uses MCP client; PEP 8 applies. Table left empty.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    | —          | —                                   |
