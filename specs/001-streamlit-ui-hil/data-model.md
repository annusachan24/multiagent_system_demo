# Data Model: Web UI for Procurement Selector Group Chat

**Feature**: 001-streamlit-ui-hil  
**Phase**: 1 – Design

Entities below are for the UI and its integration with the existing chat; no new persistence or API schema beyond the existing selector group chat.

## 1. UI message (display)

Represents one visible line in the chat UI.

| Attribute   | Description |
|------------|-------------|
| speaker    | Human-readable name: "User", "IntakeAgent", "PolicyAgent", "FinanceAgent", "VendorRiskAgent", "ReviewerAgent", or "HumanProxyAgent". |
| content    | Plain-text body to show (natural language; no raw JSON/dumps as primary view per FR-004). |
| timestamp  | Optional; display order is sufficient for MVP. |

**Source**: Derived from the Autogen stream (BaseAgentEvent / BaseChatMessage); the stream consumer maps `source` and message content to `speaker` and `content`.

## 2. UI session state (Streamlit)

State held in the browser session for one run of the app.

| Attribute            | Description |
|-----------------------|-------------|
| task                  | Initial procurement request string (user-provided). |
| messages              | List of UI messages (speaker + content) to render. |
| status                | `idle` \| `running` \| `waiting_for_input` \| `done` \| `error`. |
| error_message         | User-facing error text when status is `error`. |
| user_input_queue      | Thread-safe queue for passing the user’s reply from the UI into the UserInputManager callback (implementation detail). |

**Validation**: When status is `waiting_for_input`, the UI MUST show an input control and submit MUST enqueue the reply and trigger a rerun so the chat can continue.

## 3. Conversation / message stream (existing)

As in the feature spec and 001-selector-group-chat: the ordered sequence of messages (user task, agent replies, user replies) produced by the selector group chat. The UI does not define this; it consumes the stream and displays it (and supplies user input when requested).

## 4. User input (existing)

The initial procurement request and any follow-up responses the user types when the workflow asks for human input. Captured in the UI via the input control and passed into the chat via the UserInputManager callback.
