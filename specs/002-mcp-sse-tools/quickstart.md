# Quickstart: MCP Server (SSE) and Selector Group Chat with MCP Tools

**Feature**: 002-mcp-sse-tools

## Prerequisites

- Python 3.10+.
- Dependencies: `pip install -r requirements.txt` plus MCP and SSE support (e.g. `mcp`, and `autogen-ext[mcp]` if not already present). OpenAI API key set (e.g. `.env` or `OPENAI_API_KEY`) for the selector chat.

## 1. Start the MCP server

1. From the repo root, start the MCP server in SSE mode:
   ```text
   python -m hil_mcp.server
   ```
   Optional: `--port 8010` or `--host 0.0.0.0`. Default is `http://127.0.0.1:8000`.

2. Confirm it starts successfully: you should see "MCP server listening at http://127.0.0.1:8000". If the tool module fails to load, the process exits with a clear error.

3. Optional: Use an MCP client (e.g. CLI or test script) to list tools and call one (e.g. `extract_procurement_fields` with a sample string) to verify discovery and invocation.

## 2. Run the selector group chat (MCP tools)

1. With the MCP server **already running**, start the selector group chat that uses tools from that server:
   ```text
   python -m hil_mcp.selector_group_chat_with_hil_mcp
   ```
   Or pass a task as arguments:
   ```text
   python -m hil_mcp.selector_group_chat_with_hil_mcp "We need 50 MacBooks for Engineering, budget 75L INR, next quarter. Prefer Apple Authorized Vendor."
   ```
   The client connects to `http://127.0.0.1:8000/sse` by default. To use a different server URL or port, set `HIL_MCP_SERVER_URL` (e.g. `export HIL_MCP_SERVER_URL=http://127.0.0.1:8010/sse`).

2. The chat uses the same agent roles and prompts as the existing HIL flow (`hil.prompts`), but tools are supplied by the MCP server (SSE) instead of in-process. Flow: Intake → Policy/Finance/Vendor Risk → Reviewer → Human Proxy as needed.

3. When the run asks for human input, respond in the console. The run ends when a final decision is reached or termination conditions are met.

## 3. Validation

- **SC-001**: Connect a client to the server and list tools; the full list and schemas should be returned within 5 seconds.
- **SC-002**: Invoke each tool with valid arguments and confirm correct results.
- **SC-003**: Start two client sessions (e.g. two chat runs or two test clients); invoke tools from both; confirm no mixed responses.
- **SC-004**: Rename or break `hil_mcp/tools.py` and start the server; it must exit with a clear error and not listen.

## Project layout (this feature)

- Tool implementations: `hil_mcp/tools.py` (copied from `hil/tools.py`).
- MCP server (SSE): `hil_mcp/server.py`.
- Selector group chat using MCP tools: `hil_mcp/selector_group_chat_with_hil_mcp.py`.
