# Contract: Streamlit UI Entrypoint for Procurement Selector Group Chat

**Feature**: 001-streamlit-ui-hil  
**Type**: Web app entrypoint (no HTTP API; Streamlit’s own server).

## Purpose

Define how the Streamlit UI is started and how it interacts with the existing selector group chat (invocation, message display, human input).

## Entrypoint

- **Name**: Streamlit app for procurement selector group chat.
- **Invocation**: From repo root, `streamlit run hil/streamlit_ui.py` (or equivalent path chosen in implementation). Optional: `--server.port`, `--theme.*` per Streamlit docs.
- **Input (user)**:
  - Initial task: one natural-language procurement request, entered in the UI (e.g. text area or chat input).
  - Follow-up input: when the workflow is waiting for human input, the user types a response in the UI and submits.
- **Output (user-visible)**:
  - Ordered list of messages with clear speaker attribution (User / IntakeAgent / PolicyAgent / FinanceAgent / VendorRiskAgent / ReviewerAgent / HumanProxyAgent).
  - Messages shown in natural language (no raw technical dumps as the primary view).
  - When the run is active and not waiting for input: loading/progress indication.
  - When the run is waiting for human input: an input control and submit action.
  - On error: a clear, non-technical message (no raw stack trace).

## Preconditions

- Same as selector group chat: model client (e.g. OpenAI) configured with valid API key; participants and tools from `hil.prompts` and `hil.tools`.
- Streamlit and project dependencies installed; run from an environment that can import `hil.selector_group_chat_with_hil` (or the module that exposes the team and run_stream).

## Integration with chat

- The UI builds or imports the same SelectorGroupChat (and run_stream) as `hil/selector_group_chat_with_hil.py`.
- It does not call a separate HTTP service; it runs the chat in-process (e.g. in a thread) and consumes the stream to update the UI.
- Human input is supplied via a `UserInputManager` callback that returns the string the user submitted in the UI (e.g. from a thread-safe queue).

## Termination

- The chat run ends per existing logic (MaxMessageTermination, TextMentionTermination, HandoffTermination, etc.).
- The UI reflects “done” and may show a final message or allow starting a new chat (per spec: one active chat per session for initial scope).
