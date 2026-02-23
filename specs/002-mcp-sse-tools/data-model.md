# Data Model: MCP Server Hosting Tools in SSE Mode

**Feature**: 002-mcp-sse-tools  
**Phase**: 1 – Design

Entities are logical; the MCP protocol and SDK define the on-wire format. No separate persistence layer.

---

## 1. Tool

A callable capability exposed by the server, with a name, description, and input schema.

| Attribute    | Description |
|-------------|-------------|
| name        | Unique identifier used by clients to invoke the tool (e.g. `extract_procurement_fields`, `check_policy`). |
| description | Human- and model-readable summary (from docstring or explicit metadata). |
| input_schema | JSON Schema for arguments (names, types, required/optional). Derived from the Python function signature and docstring when registering. |

**Source**: Functions in `hil_mcp/tools.py` (copied from `hil/tools.py`). The server registers each as an MCP tool; no separate “Tool” storage—registration is in-memory at startup.

**Validation**: Tool names must be unique. Arguments are validated by the server against the schema before execution (FR-006); invalid or missing required arguments yield a structured error response.

---

## 2. Tool invocation

A single client request to run one tool and the corresponding server response.

| Concept     | Description |
|------------|-------------|
| request    | Tool name (string) + arguments (key-value map). Sent by the client over the SSE session (e.g. POST body or MCP message). |
| response   | Either the tool result (serializable value returned by the function) or a structured error (e.g. tool not found, validation failure, execution exception). |

**State**: Stateless. Each invocation is independent; no server-side conversation or session state beyond the MCP session itself. Results are not persisted.

**Validation**: Server MUST validate tool name exists and arguments match the tool’s input_schema before calling the implementation; otherwise return a clear error (FR-006, acceptance scenarios 2–3).

---

## 3. SSE connection (session)

A long-lived client connection used for MCP communication: listing tools and invoking tools.

| Attribute   | Description |
|------------|-------------|
| session_id | Identifier for the client session (handled by the MCP SDK/transport). |
| lifecycle  | Established when the client connects (e.g. GET to SSE endpoint); closed when the client disconnects or the server shuts down. |

**Concurrency**: Multiple clients can have separate sessions (FR-005). Each request is tied to the correct session so responses are not mixed (SC-003). The server does not store application state per session beyond what the transport requires.

---

## 4. Relationship to existing procurement model

- **Procurement Request / Agent Findings / Human Decision** (see 001-selector-group-chat data-model): Unchanged. Tools in `hil_mcp/tools.py` operate on the same logical data (e.g. `extract_procurement_fields` returns a structure that corresponds to Procurement Request fields; `check_policy`/`check_budget`/etc. produce findings). The only change is that those tools are invoked via MCP (tool invocation) instead of in-process.
- **Conversation context**: Still held in the SelectorGroupChat run (client side). The MCP client in `selector_group_chat_with_hil_mcp.py` obtains tools from the MCP server; the chat run itself is unchanged from 001 except for the source of the tool list.
