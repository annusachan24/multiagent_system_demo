# Research: Streamlit UI for Procurement Selector Group Chat

**Feature**: 001-streamlit-ui-hil  
**Phase**: 0

## 1. Autogen run_stream and Console integration

**Decision**: Use the same `team.run_stream(task=task)` API that the CLI uses; replace `Console` with a custom stream consumer that renders to Streamlit and supplies human input via Autogen’s `UserInputManager`.

**Rationale**: The spec requires reusing the existing selector group chat logic. Autogen’s `Console(stream, user_input_manager=...)` accepts an optional `UserInputManager(callback)` where the callback has signature `(messages: list[str], cancellation_token?) -> str | Awaitable[str]`. So we can plug in a callback that, instead of reading from stdin, returns the value provided by the Streamlit UI (e.g. from a queue or session state).

**Alternatives considered**:
- Reimplementing chat logic outside Autogen: rejected; spec and constitution require keeping Autogen as the source of truth.
- Exposing the chat as an HTTP API and building a separate front-end: rejected for initial scope; spec asks for a single web UI (Streamlit) wrapping the existing entrypoint.

**Implementation note**: The stream yields `BaseAgentEvent | BaseChatMessage` and finally `TaskResult`. The custom consumer must iterate the stream, map events/messages to a simple (speaker, content) form for display, and when the framework calls the UserInputManager callback, provide the string the user entered in the UI (see “Human input and threading” below).

---

## 2. Human input and threading (Streamlit + UserInputManager)

**Decision**: Run the async stream in a dedicated thread and use a thread-safe queue to pass user input from the Streamlit main thread into the `UserInputManager` callback. Use shared state (e.g. `st.session_state`) for the message list the stream consumer appends to, and a “waiting for human input” flag so the UI shows an input box when needed.

**Rationale**: Streamlit’s execution model is single-threaded and reruns the script on each interaction. The Autogen stream runs asynchronously and blocks on the `UserInputManager` callback when it’s the human’s turn. So the stream must run in a thread; the callback blocks on `queue.get()`; the Streamlit script enqueues the user’s reply when they submit the form and then triggers a rerun so the thread can continue and append more messages.

**Alternatives considered**:
- Running the stream in the main thread and showing an input box “after” the stream: not possible, because the stream blocks when it needs human input.
- Using only async (no thread): Streamlit does not natively support long-running async work that blocks on user input in the same run; the thread + queue approach is the standard pattern for “background task + UI input.”

**Implementation notes**:
- Ensure the stream-consumer thread only writes to session state (or a thread-safe structure that the main thread reads) so Streamlit’s constraints are respected; use `add_script_run_ctx` if the thread needs to touch `st.session_state` from the docs, or a lock-protected list that the main thread copies into session state on each rerun.
- On “Submit” for human reply: put the reply into the queue, set `waiting_for_input = False`, and call `st.rerun()` so the next run can show any new messages the thread adds after the human responds.
- Optional: poll or use a “Refresh” control to update the message list while the thread is running and not waiting for input, so the user sees messages as they appear without having to submit to refresh.

---

## 3. Streamlit version and “fancy” UI

**Decision**: Use Streamlit’s built-in layout and styling (e.g. `st.chat_message`, `st.chat_input`, columns, expanders) plus a consistent theme (e.g. `config.toml` or `st.set_page_config`) to meet the “visually polished, modern” requirement. No separate front-end framework.

**Rationale**: Spec asks for a single web UI and “fancy” meaning modern and polished. Streamlit’s native components and theming are sufficient and keep the stack minimal.

**Alternatives considered**:
- Custom CSS/HTML in Streamlit: acceptable for small tweaks; avoid large custom front-ends for scope.
- Separate React/Vue app: out of scope; spec expects a Streamlit UI.

---

## 4. Error handling and loading state

**Decision**: Wrap the run in try/except; on configuration or backend failure show a clear, non-technical message in the UI (spec FR-006, SC-004). Show a loading/progress indicator (e.g. spinner or “Running…”) while the stream is active and not waiting for human input.

**Rationale**: Spec edge case (“long-running or slow responses”) and success criterion SC-004 require user-visible feedback and friendly error messages.

**Alternatives considered**:
- Exposing raw tracebacks: rejected per spec.
