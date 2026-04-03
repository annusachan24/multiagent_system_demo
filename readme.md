# Multi-agent system demo

Python demos built with [Microsoft AutoGen](https://github.com/microsoft/autogen) (`autogen-agentchat`): procurement-focused **selector group chats**, **human-in-the-loop (HIL)** flows, optional **Streamlit** UI, and an **MCP** server (SSE) that exposes the same tool surface to agents.

## Requirements

- **Python 3.10+**
- An **OpenAI API key** with access to the models used in the scripts (e.g. `gpt-4o`)

## Setup

1. **Clone** the repository and enter the project root.

2. **Create and activate a virtual environment** (recommended):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the API key**. The code loads environment variables via `python-dotenv` from a `.env` file in the repo root (see `contants.py`).

   Create `.env`:

   ```bash
   OPENAI_API_KEY=sk-...
   ```

   Alternatively, export `OPENAI_API_KEY` in your shell before running any script.

## How to run the main flows

### 1. Streamlit UI (procurement HIL, in-process tools)

Runs the selector group chat in the background and collects human replies in the browser.

```bash
streamlit run hil/streamlit_ui.py
```

Open the URL Streamlit prints (default **http://localhost:8501**). Submit a procurement-style request; when agents ask for human input, use the chat input.

### 2. Console procurement HIL (in-process tools)

Same team and prompts as the UI, but **stdin/stdout** for human answers.

```bash
python -m hil.selector_group_chat_with_hil
```

Optional task text:

```bash
python -m hil.selector_group_chat_with_hil "We need 50 MacBooks for Engineering..."
```

### 3. MCP server + console chat (tools over SSE)

**Terminal A — start the MCP server** (default `http://127.0.0.1:8000`):

```bash
python -m hil_mcp.server
```

Optional: `--port 8010`, `--host 0.0.0.0`.

**Terminal B — run the selector chat** (connects to `http://127.0.0.1:8000/sse` by default):

```bash
python -m hil_mcp.selector_group_chat_with_hil_mcp
```

With a one-line task:

```bash
python -m hil_mcp.selector_group_chat_with_hil_mcp "Your procurement request here."
```

If the server uses another host/port, set:

```bash
export HIL_MCP_SERVER_URL=http://127.0.0.1:8010/sse
```

### 4. Notebook (AutoGen basics)

`state_disk.ipynb` is a small **Jupyter** example (round-robin team, `await Console(stream)`). From the repo root, start Jupyter or VS Code’s notebook UI with the same Python environment where dependencies are installed.

## Other scripts in the repo

| Path | Purpose |
|------|--------|
| `selector_group_chat.py` | Standalone selector group chat example (mock tools, different domain than procurement HIL). |
| `single_agent.py`, `single_llm.py`, `single_agent_multiple_tools.py`, `travel_planning_agent.py` | Smaller single-agent or tool demos. |
| `comparision/` | Examples comparing other multi-agent frameworks (separate from the main `hil` / `hil_mcp` flows). |

## Project layout (high level)

- **`hil/`** — Procurement HIL team (`selector_group_chat_with_hil.py`), prompts, in-process tools, Streamlit app (`streamlit_ui.py`).
- **`hil_mcp/`** — MCP SSE server (`server.py`), tool implementations (`tools.py`), selector chat wired to MCP (`selector_group_chat_with_hil_mcp.py`).
- **`contants.py`** — Loads `OPENAI_API_KEY` (and `.env`).
- **`requirements.txt`** / **`pyproject.toml`** — Dependencies and packaging metadata.
- **`specs/`** — Design notes and quickstarts for individual features.

## Troubleshooting

- **`OPENAI_API_KEY` missing** — Add it to `.env` or your environment; otherwise model clients will fail when building the team.
- **MCP chat cannot connect** — Start `python -m hil_mcp.server` first; align `HIL_MCP_SERVER_URL` with the real SSE URL (including `/sse` if that is what your server exposes).
- **`mcp` import errors** — Re-run `pip install -r requirements.txt` so `mcp` and `autogen-ext[openai,mcp]` are installed.
