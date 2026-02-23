# Feature Specification: Selector Group Chat for Procurement (HIL Agents and Tools)

**Feature Branch**: `001-selector-group-chat`  
**Created**: 2025-02-21  
**Status**: Draft  
**Input**: User description: "I need to create a selector group chat with following agents (from hil prompts) and with these tools (from hil tools)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run Procurement Selector Group Chat (Priority: P1)

As a procurement operator, I want to run a selector group chat where specialized agents (Intake, Policy, Finance, Vendor Risk, Reviewer, and Human Proxy) collaborate on a single procurement request so that the request is structured, validated against policy and budget, assessed for vendor risk, and either auto-resolved or escalated to me with clear next steps.

**Why this priority**: This is the core capability; without it there is no feature.

**Independent Test**: Start a chat with a natural-language procurement request; observe agents taking turns (selector choosing who speaks next); receive either a final recommendation or a clear request for human input (missing fields, approval, or decision).

**Acceptance Scenarios**:

1. **Given** the selector group chat is started with a new procurement request, **When** the conversation runs, **Then** the Intake agent (or equivalent first-step agent) is used to extract and structure the request, and missing required fields result in a clear request for human input.
2. **Given** a structured request, **When** the selector chooses subsequent agents, **Then** Policy, Finance, and Vendor Risk agents can perform their checks using the defined tools (policy checks, budget checks, vendor lookup/risk), and the Reviewer synthesizes findings and recommends approve / escalate / reject or need more info.
3. **Given** the Reviewer (or workflow) determines human input is required, **When** the Human Proxy agent is selected, **Then** the human can approve, reject, modify the request, or ask clarification questions, and that decision is treated as final for the flow.
4. **Given** any agent that has tools assigned, **When** that agent is selected, **Then** the agent can invoke only its assigned tools (e.g. Intake: extraction and validation; Policy: policy and approval matrix; Finance: budget and spend forecast; Vendor Risk: vendor lookup and risk score).

### User Story 2 - Correct Agent and Tool Wiring (Priority: P2)

As a maintainer, I want the selector group chat to use the existing agent definitions (roles, prompts, and tool assignments) and the existing tool set so that behavior is consistent with the defined procurement workflow and no ad-hoc agents or tools are introduced for this chat.

**Why this priority**: Ensures the feature integrates the specified agents and tools rather than redefining them.

**Independent Test**: Run the chat and verify that each agent role (Intake, Policy, Finance, Vendor Risk, Reviewer, Human Proxy) appears with the correct responsibilities and that tool calls align with the defined tool set (extraction, validation, policy, budget, vendor lookup/risk).

**Acceptance Scenarios**:

1. **Given** the defined agent set, **When** the selector group chat runs, **Then** only these six agent roles participate, each with the intended scope (e.g. Reviewer and Human Proxy do not use tools; others use only their assigned tools).
2. **Given** the defined tool set, **When** an agent invokes a tool, **Then** the tool behavior matches the existing tool definitions (e.g. extraction/validation for Intake, policy/approval for Policy, budget/forecast for Finance, vendor lookup/risk for Vendor Risk).

### Edge Cases

- **Missing or invalid request data**: When required fields are missing, the flow clearly requests human input (e.g. via Intake marking INCOMPLETE and specifying missing fields); the next step allows the human to supply data before continuing.
- **Policy or budget blocks**: When Policy or Finance tools return a block or warning, the Reviewer’s recommendation (e.g. escalate or reject) is visible and the Human Proxy can make the final decision.
- **Unknown or high-risk vendor**: When vendor tools return NOT_APPROVED or high risk, the flow surfaces this to the Reviewer and human rather than auto-approving.
- **Selector or tool failure**: If the selector cannot choose an agent or a tool call fails, the system surfaces an understandable error or fallback so the operator can retry or correct input.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a selector group chat where one agent is chosen at a time to respond, using the six defined agent roles: Intake, Policy, Finance, Vendor Risk, Reviewer, and Human Proxy.
- **FR-002**: The Intake agent MUST be able to extract and structure procurement request fields and validate required fields using the defined extraction and validation tools; when data is incomplete, it MUST request human input and not hand off to other validators until the human responds.
- **FR-003**: The Policy agent MUST perform policy and approval-matrix checks using the defined policy tools; it MUST NOT modify the request or perform budget/vendor checks.
- **FR-004**: The Finance agent MUST perform budget availability and spend-forecast checks using the defined finance tools; it MUST NOT approve or reject requests.
- **FR-005**: The Vendor Risk agent MUST perform vendor lookup and risk scoring using the defined vendor tools; it MUST NOT evaluate pricing or policy.
- **FR-006**: The Reviewer agent MUST synthesize outputs from other agents and decide next action (e.g. auto-approve, escalate to human, reject, need more info); it MUST NOT use tools.
- **FR-007**: The Human Proxy agent MUST allow the human to approve, reject, modify the request, or ask clarification questions; that decision MUST be treated as final for the flow; it MUST NOT use tools.
- **FR-008**: Tool calls MUST be restricted per agent: only the tools assigned to each agent in the existing definitions may be invoked by that agent.
- **FR-009**: When the workflow requires human input (missing fields, escalation, or final decision), the human MUST be able to respond in the same chat and the flow MUST continue based on that response.

### Key Entities *(include if feature involves data)*

- **Procurement request**: Item, quantity, estimated budget, currency, department, timeline, vendor preference; status (e.g. INCOMPLETE, READY_FOR_REVIEW) and missing-field list when incomplete.
- **Agent findings**: Policy status and issues; budget status and risk level; vendor status and risk rating; Reviewer summary and decision (approve / escalate / reject / need more info).
- **Human decision**: Final approval, rejection, or modification with optional conditions and notes.

## Assumptions

- Agent role definitions (names, responsibilities, and tool assignments) and tool implementations already exist in the project; this feature wires them into a selector group chat and does not redefine behavior.
- The selector mechanism chooses the next speaker from the six agents (and human when in the loop) based on conversation context and agent descriptions.
- One procurement request is processed per chat session; multi-request batching is out of scope unless explicitly added later.
- Human-in-the-loop is supported within the same chat (e.g. Human Proxy agent or equivalent) so the human can respond when the workflow asks for input or final decision.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user can submit a natural-language procurement request and receive either a final recommendation (approve / escalate / reject) or a clear request for human input (missing fields or decision) within a reasonable number of turns (e.g. under 20 agent/human turns for a typical request).
- **SC-002**: When human input is required, the user can provide it in the same chat and the flow continues without losing context (e.g. missing fields are filled and validation continues).
- **SC-003**: Each agent uses only its assigned tools; no agent invokes tools that are not in its definition (verifiable by inspecting tool call usage per agent).
- **SC-004**: The six agent roles (Intake, Policy, Finance, Vendor Risk, Reviewer, Human Proxy) are all reachable and used appropriately in at least one end-to-end run (e.g. from raw request to final recommendation or human decision).
