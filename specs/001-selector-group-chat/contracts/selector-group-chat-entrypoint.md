# Contract: Selector Group Chat Entrypoint

**Feature**: 001-selector-group-chat  
**Type**: Programmatic / CLI entrypoint (no HTTP API in scope).

## Purpose

Define how the procurement selector group chat is invoked and what it consumes/produces.

## Entrypoint

- **Name**: Run procurement selector group chat (single session).
- **Input**: One natural-language procurement request (string), e.g. "We need 50 MacBooks for Engineering, budget 75L INR, next quarter, Apple Authorized Vendor."
- **Output**: Conversation result (AutoGen `TaskResult`): messages (history), stop_reason. The last messages contain either a final recommendation (approve / escalate / reject) or a clear request for human input; when a human responds via UserProxyAgent, the flow continues until a final outcome.
- **Side effects**: LLM and tool calls during the run; no required persistence. Console (or UI) displays the stream of agent/human messages.

## Preconditions

- Model client (e.g. OpenAI) configured with valid API key.
- Participants built from `hil.prompts` (agents) and `hil.tools` (tools); Human Proxy (UserProxyAgent) available for input when the workflow requests it.

## Termination

- Conversation ends when: (1) a termination condition is met (e.g. MaxMessageTermination, or TERMINATE mentioned), or (2) the Human Proxy or Reviewer indicates a final decision and the run is considered complete by the implementation.
