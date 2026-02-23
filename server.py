"""
MCP server over SSE exposing procurement tools from hil_mcp.tools.

Run: python -m hil_mcp.server [--port 8000]
Or: uvicorn hil_mcp.server:app --host 0.0.0.0 --port 8000

Server URL for clients: http://127.0.0.1:8000 (or --port value).
"""

import argparse
import inspect
import sys
from typing import Any, Callable

# Fail fast if mcp is not installed
try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    sys.stderr.write(
        "ERROR: MCP SDK not installed. Run: pip install mcp\n"
        f"Detail: {e}\n"
    )
    sys.exit(1)

# Load tool module and collect callables (T006: fail fast with clear message)
def _load_tools():
    """Import hil_mcp.tools and return list of (name, callable) for tool registration."""
    try:
        import hil_mcp.tools as tools_module
    except ImportError as e:
        sys.stderr.write(
            "ERROR: Could not load tool module hil_mcp.tools. "
            "Ensure hil_mcp/tools.py exists and is importable.\n"
            f"Detail: {e}\n"
        )
        sys.exit(1)

    # Public functions only (no private, no imports like Dict/random)
    tool_fns = []
    for name in dir(tools_module):
        if name.startswith("_"):
            continue
        obj = getattr(tools_module, name)
        if callable(obj) and inspect.isfunction(obj):
            tool_fns.append((name, obj))

    if not tool_fns:
        sys.stderr.write(
            "ERROR: No callable tools found in hil_mcp.tools. "
            "Register at least one function in hil_mcp/tools.py.\n"
        )
        sys.exit(1)

    return tool_fns


def _create_mcp_app(host: str = "127.0.0.1", port: int = 8000) -> Any:
    """Build FastMCP app with all hil_mcp.tools registered. Exits on failure (T006)."""
    tool_list = _load_tools()
    mcp = FastMCP(
        "Procurement tools (MCP)",
        json_response=True,
        host=host,
        port=port,
    )
    for _name, fn in tool_list:
        mcp.tool()(fn)  # Register existing function as MCP tool
    return mcp


# Default app for "uvicorn hil_mcp.server:app" (tools loaded at import; exits on failure)
mcp_app = _create_mcp_app()
# Expose Starlette ASGI app for SSE (T007)
app = mcp_app.sse_app(mount_path="/") if hasattr(mcp_app, "sse_app") else None


def _run_standalone(host: str = "127.0.0.1", port: int = 8000) -> None:
    """Run server with SSE; print readiness message (T010)."""
    url = f"http://{host}:{port}"
    print(f"MCP server listening at {url}", flush=True)
    print("Connect MCP clients to this URL for tool list and invocation.", flush=True)
    # Create app with requested host/port so run_sse_async uses them
    server = _create_mcp_app(host=host, port=port)
    server.run(transport="sse", mount_path="/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP server (SSE) for procurement tools")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind")
    args = parser.parse_args()
    _run_standalone(host=args.host, port=args.port)
