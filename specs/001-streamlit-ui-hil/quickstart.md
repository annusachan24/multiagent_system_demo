# Quickstart: Streamlit UI for Procurement Selector Group Chat

**Feature**: 001-streamlit-ui-hil

## Prerequisites

- Python 3.10+.
- Dependencies: `pip install -r requirements.txt` (includes `autogen-agentchat`, `autogen-ext[openai]`, and Streamlit).
- Environment: Set OpenAI API key (e.g. in `.env` or `OPENAI_API_KEY`).

## Run the UI

1. **Start the app** (from repo root):
   ```bash
   streamlit run hil/streamlit_ui.py
   ```
   Or, if the app is placed elsewhere, use that path. Optional: `--server.port 8502`, `--theme.base dark`, etc.

2. **In the browser**:
   - Enter a natural-language procurement request (e.g. “We need 50 MacBooks for Engineering, budget 75L INR, next quarter. Prefer Apple Authorized Vendor.”).
   - Start the chat (e.g. “Start” or “Send”).
   - Watch agent messages appear in order with clear speaker labels.
   - When the workflow asks for human input, type your response in the input box and submit; the conversation continues (or ends as designed).

3. **Validation**:
   - Complete at least one full exchange (see agent messages and provide at least one human response when asked).
   - Confirm the interface looks polished (layout, typography, clear chat area and input).
   - If the backend or config fails, confirm the UI shows a clear, non-technical error message.

## Project layout (this feature)

- Chat logic and team: `hil/selector_group_chat_with_hil.py` (unchanged or lightly refactored to expose run_stream + team for reuse).
- Streamlit app: `hil/streamlit_ui.py` (or path chosen in implementation)—layout, message display, run loop, UserInputManager integration.
