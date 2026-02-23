# Contract: MCP SSE Server Entrypoint

**Feature**: 002-mcp-sse-tools  
**Type**: Server process / SSE endpoint.

## Purpose

Define how the MCP server is started, how clients connect, and what they can do (list tools, call tools).

## Server entrypoint

- **Name**: MCP server over SSE (procurement tools).
- **Start**: Run the server process (e.g. `python -m hil_mcp.server` or a documented equivalent). Server loads `hil_mcp.tools`, registers all tools with the MCP runtime, and listens for SSE connections on a configured host/port (e.g. `http://localhost:8xxx`).
- **Failure**: If the tool module cannot be imported or no tools can be registered, the process exits with a clear, actionable error message and does not accept connections (FR-007, SC-004).

## Client connection

- **Transport**: SSE (Server-Sent Events) per MCP spec. Clients use the standard MCP SSE client flow: establish SSE stream (e.g. GET), send messages (e.g. POST) with session linkage.
- **Base URL**: Documented in quickstart (e.g. `http://127.0.0.1:8000` or similar). The exact port and path are implementation-defined and must be consistent with what `selector_group_chat_with_hil_mcp.py` uses in `SseServerParams`.

## Operations

1. **List tools**  
   Client requests the list of available tools.  
   **Response**: List of tools, each with name, description, and input schema (parameters).  
   **Success criterion**: Client can discover the full list within 5 seconds of connecting (SC-001).

2. **Call tool**  
   Client sends a request with tool name and arguments.  
   **Response**: Tool result (serialized) or structured error (tool not found, invalid/missing arguments, execution error).  
   **Success criterion**: Valid requests receive correct results; invalid requests receive clear errors (SC-002, FR-006).

## Preconditions

- Python environment with MCP SDK and ASGI server available.
- `hil_mcp/tools.py` present and importable; all intended tool functions are exportable.

## Concurrency

- Multiple clients may connect. Each gets a distinct session; requests and responses are associated with the correct client (FR-005, SC-003).
