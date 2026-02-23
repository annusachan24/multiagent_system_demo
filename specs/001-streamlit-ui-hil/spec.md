# Feature Specification: Web UI for Procurement Selector Group Chat

**Feature Branch**: `001-streamlit-ui-hil`  
**Created**: 2025-02-21  
**Status**: Draft  
**Input**: User description: "create a streamlit ui for hil/selector_group_chat_with_hil.py, make it fancy"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Procurement Chat from a Web Interface (Priority: P1)

As a procurement operator, I want to use a web-based interface to start and participate in the procurement selector group chat so that I can submit requests and respond to agents without using the command line.

**Why this priority**: Core value is moving from CLI to a browser-based experience.

**Independent Test**: Open the web UI, enter a procurement request (e.g. "buy 50 MacBooks for Engineering"), start the chat, and see agent messages and a way to provide human input when prompted.

**Acceptance Scenarios**:

1. **Given** the web UI is open, **When** the user enters a natural-language procurement request and starts the chat, **Then** the conversation runs and agent messages appear in the interface in order.
2. **Given** the workflow is waiting for human input, **When** the user types a response in the UI and submits, **Then** the response is sent into the chat and the flow continues (or the run ends as designed).
3. **Given** the user is viewing the conversation, **Then** messages are clearly attributable (e.g. which agent or the user spoke) and readable in natural language.

### User Story 2 - Visually Polished, Modern Experience (Priority: P2)

As a user, I want the interface to look modern and polished so that using the procurement chat feels professional and pleasant rather than utilitarian.

**Why this priority**: "Fancy" was an explicit ask; supports adoption and perceived quality.

**Independent Test**: Open the UI and confirm it has a cohesive, modern look (layout, typography, spacing, optional light/dark or theme), and that the chat area and input are easy to use.

**Acceptance Scenarios**:

1. **Given** the UI is loaded, **Then** the layout is clear, with a dedicated area for the conversation and a clear place to type and send the user's message.
2. **Given** the user is in the chat, **Then** visual design is consistent (e.g. colors, fonts, spacing) and avoids a bare, unstyled appearance.
3. **Given** the conversation is long, **Then** the user can scroll or navigate the message history without losing context.

### Edge Cases

- **Long-running or slow responses**: The UI shows that the system is working (e.g. loading or progress indication) so the user does not assume the app has frozen.
- **Errors (e.g. missing config, API failure)**: The user sees an understandable message in the UI rather than a raw error or blank screen.
- **Session or refresh**: Behavior on browser refresh or back is defined (e.g. session lost is acceptable for MVP, with a clear message if the conversation cannot be resumed).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a web-based interface that allows the user to start the procurement selector group chat with a task string (the initial procurement request).
- **FR-002**: The interface MUST display the conversation (agent and user messages) in order, with clear indication of who spoke (user vs. which agent).
- **FR-003**: When the chat workflow requires human input, the user MUST be able to type and submit a response in the same interface and have it used as the human's reply in the chat.
- **FR-004**: The interface MUST present messages in a readable, natural-language way (no raw technical dumps as the primary view when the backend sends natural text).
- **FR-005**: The interface MUST have a visually polished, modern design (cohesive layout, typography, and styling) so it does not appear as a bare, unstyled page.
- **FR-006**: The system MUST handle errors (e.g. missing configuration, backend failure) by showing the user an understandable message in the UI.

### Key Entities *(include if feature involves data)*

- **Conversation / message stream**: Ordered sequence of messages (user task, agent replies, user replies) produced by the existing selector group chat; the UI displays and appends to this.
- **User input**: The initial procurement request and any follow-up responses the user types when the workflow asks for human input.

## Assumptions

- The existing procurement selector group chat (e.g. the runnable behind hil/selector_group_chat_with_hil) remains the source of truth for conversation logic; the UI is a front-end that starts the chat, displays messages, and supplies user input.
- "Fancy" is interpreted as a modern, polished look (layout, typography, spacing, optional theme) rather than a specific visual style unless the product owner specifies otherwise.
- One active chat session per browser session is sufficient for the initial scope; multi-tab or multi-session behavior can be defined later.
- Configuration (e.g. API keys) is available to the backend as today; the UI does not need to manage secrets in the first version.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can open the web interface, submit a procurement request, and complete at least one full exchange (see agent messages and provide at least one human response when asked) without using the command line.
- **SC-002**: When the workflow requests human input, the user can respond within the same interface and see the conversation continue (or end as designed) based on that response.
- **SC-003**: The interface presents a consistent, modern visual design so that stakeholders rate it as professional and easy to use in a quick walkthrough.
- **SC-004**: If the backend or configuration fails, the user sees a clear, non-technical message in the UI rather than a raw stack trace or blank screen.
