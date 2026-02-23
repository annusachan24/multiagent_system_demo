# Contract: Exposed Tool List (MCP Server)

**Feature**: 002-mcp-sse-tools  
**Type**: Logical contract (tool names and purposes).

## Purpose

Define the set of tools the MCP server exposes. These match the functions in `hil_mcp/tools.py` (copied from `hil/tools.py`) so that the selector group chat and prompts remain valid when tools are consumed via MCP.

## Tools (by agent role)

- **Intake**: `extract_procurement_fields`, `validate_required_fields`, `create_purchase_request`
- **Policy**: `check_policy`, `approval_matrix`
- **Finance**: `check_budget`, `forecast_spend`
- **Vendor risk**: `lookup_vendor`, `vendor_risk_score`
- **Utility**: `generate_request_id` (if exposed; may be internal to `create_purchase_request`)

Exact names and parameter schemas are defined by the server from the Python function signatures and docstrings when registering tools. Clients discover them via the MCP “list tools” operation; no separate API document is required beyond this list for spec/plan alignment.

## Validation

- Server MUST expose only tools that exist in `hil_mcp.tools` and are registered at startup.
- Any request for a tool name not in this set MUST return an error (tool not found) per spec acceptance scenario 3.
