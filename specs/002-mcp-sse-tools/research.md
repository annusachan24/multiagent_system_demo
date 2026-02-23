# Research: MCP SSE Server and Autogen Client

**Feature**: 002-mcp-sse-tools  
**Purpose**: Resolve technical choices for MCP server (SSE) and client usage in `hil_mcp/`.

---

## 1. MCP Python server with SSE transport

**Decision**: Use the official MCP Python SDK (`mcp`) with its SSE server transport. Run the SSE endpoint behind an ASGI server (e.g. Hypercorn or Uvicorn).

**Rationale**:
- The MCP Python SDK provides `SseServerTransport` (e.g. in `mcp.server.sse`) with standard GET (connect SSE) and POST (client messages) handling, matching the spec’s SSE requirement.
- Same SDK is widely used and documented; aligns with “standard MCP clients can connect.”
- FastMCP or equivalent high-level helpers in the SDK can be used to register tools from Python functions and expose them over SSE with minimal boilerplate.

**Alternatives considered**:
- Custom SSE endpoint without MCP SDK: rejected because it would reimplement the MCP protocol and risk incompatibility with clients.
- Stdio-only MCP server: rejected because the spec requires SSE mode for network accessibility and multiple clients.

---

## 2. Tool source and registration

**Decision**: Copy tool implementations from `hil/tools.py` into `hil_mcp/tools.py`. The MCP server in `hil_mcp/server.py` imports from `hil_mcp.tools` and registers each callable as an MCP tool (name, description, parameters derived from function signature/docstring).

**Rationale**:
- Keeps `hil_mcp` self-contained and avoids depending on `hil` at runtime for the server, so the server can be started and tested independently.
- Tool names and signatures stay aligned with what `hil/prompts.py` and the selector chat expect; only the delivery mechanism (MCP vs in-process) changes.
- Single source of truth for “procurement tool set” in this feature is `hil_mcp/tools.py`.

**Alternatives considered**:
- Server importing from `hil.tools`: would tie the server to `hil` and blur the boundary; rejected.
- Shared package used by both `hil` and `hil_mcp`: possible future refactor; not required for this feature.

---

## 3. Autogen agent tools from MCP (SSE client)

**Decision**: In `selector_group_chat_with_hil_mcp.py`, use `autogen_ext.tools.mcp` with SSE: `SseServerParams` (server URL) and `mcp_server_tools(server_params)` to obtain a list of tool adapters, then pass those to `AssistantAgent(..., tools=...)` instead of the current in-process list from AGENT_CONFIG.

**Rationale**:
- autogen-ext documents MCP support and provides `SseServerParams` and `mcp_server_tools()` for SSE-based MCP servers, matching our server transport.
- Agents continue to receive a list of tools; only the origin of that list changes from `hil.tools` + AGENT_CONFIG to MCP discovery.
- Agent prompts and roles in `hil.prompts` remain unchanged; tool names and behavior stay the same so prompts do not need edits for this feature.

**Alternatives considered**:
- Per-agent MCP connections: rejected; one client connection (and one session) to the single MCP server is sufficient and simpler.
- Keeping in-process tools and not using MCP: rejected by constitution (tools must be hosted via MCP).

---

## 4. Server startup and failure behavior

**Decision**: On startup, the server loads `hil_mcp.tools` and registers all intended tools. If the import fails or no tools can be registered, the server exits with a clear, actionable error message and does not listen for connections.

**Rationale**: Matches FR-007 and SC-004: “start only when the tool source can be loaded successfully” and “operator sees a clear, actionable error message.”

---

## 5. Concurrency and session handling

**Decision**: Rely on the MCP SDK’s SSE transport and session handling so that multiple clients can connect; each client gets its own session. The server does not hold mutable per-caller state beyond what the SDK requires; tool executions are stateless.

**Rationale**: Meets FR-005 and SC-003 (multiple concurrent clients, no mixed responses). No custom concurrency design needed beyond using the SDK correctly.

---

## Summary

| Topic              | Decision                                              |
|--------------------|--------------------------------------------------------|
| MCP server stack   | MCP Python SDK + SSE transport + ASGI server          |
| Tool definitions   | Copy `hil/tools.py` → `hil_mcp/tools.py`; server imports from `hil_mcp.tools` |
| Client integration | autogen_ext.tools.mcp with SseServerParams + mcp_server_tools in selector_group_chat_with_hil_mcp.py |
| Startup failure    | Exit with clear error if tool module fails to load     |
| Concurrency        | SDK session per client; stateless tool execution       |
