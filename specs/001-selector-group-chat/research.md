# Research: Selector Group Chat for Procurement (HIL)

**Feature**: 001-selector-group-chat  
**Phase**: 0 – Outline & Research

## 1. AutoGen SelectorGroupChat

**Decision**: Use AutoGen AgentChat `SelectorGroupChat` with model-based next-speaker selection, as documented in the [Selector Group Chat user guide](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/selector-group-chat.html).

**Rationale**:
- SelectorGroupChat fits the procurement workflow: one agent speaks at a time, chosen by an LLM from conversation context and agent names/descriptions.
- The project already uses `autogen-agentchat` and has a working `SelectorGroupChat` example in `selector_group_chat.py` (Planning, WebSearch, DataAnalyst).
- Key APIs: `SelectorGroupChat(participants, model_client, termination_condition, selector_prompt, allow_repeated_speaker=True)`, optional `selector_func` or `candidate_func` for custom selection logic.

**Alternatives considered**:
- RoundRobinGroupChat: Rejected; procurement flow is context-dependent (Intake first, then Policy/Finance/Vendor as needed, then Reviewer, then Human when needed).
- Custom group chat via Core API: Rejected for first iteration; SelectorGroupChat is sufficient and matches the spec.

## 2. Agent and Tool Wiring

**Decision**: Build six participants from the existing `AGENT_CONFIG` and prompts in `hil/prompts.py`, and wire tools from `hil/tools.py` (not `demo.tools`). Each participant is an `AssistantAgent` with `name`, `description` (for selector), `system_message` (prompt), and `tools` list. Human-in-the-loop uses `UserProxyAgent`.

**Rationale**:
- Spec requires the six roles (Intake, Policy, Finance, Vendor Risk, Reviewer, Human Proxy) with tool assignments as already defined; `AGENT_CONFIG` is the single source of truth for prompt + tools per agent.
- `hil/prompts.py` currently imports from `demo.tools`; for this feature we use `hil.tools` so the selector group chat implementation depends only on the HIL module. Prompts stay in `hil/prompts.py`; tool implementations live in `hil/tools.py`.
- Agent `description` is critical: the selector uses it to choose the next speaker, so we use `AGENT_DESCRIPTIONS` from prompts (e.g. "Extracts and structures procurement request... Use first for new requests.").

**Alternatives considered**:
- Keeping demo.tools: Rejected; spec and user ask for tools from hil/tools.py.
- One generic agent with tool routing: Rejected; spec requires distinct agent roles and per-agent tool restrictions.

## 3. Human-in-the-Loop (Human Proxy)

**Decision**: Add a `UserProxyAgent` to the SelectorGroupChat so the human can respond when the workflow requests input (missing fields, escalation, or final decision). Use the same chat session so context is preserved.

**Rationale**:
- Spec FR-002, FR-007, FR-009 require human input in the same chat for missing data, final approve/reject/modify, and continuation after input.
- AutoGen docs describe adding `UserProxyAgent` to the team and using a custom `selector_func` or selector prompt to route to the user when needed (e.g. after Intake says HUMAN_INPUT_NEEDED or Reviewer says ESCALATE_TO_HUMAN).
- Optional: custom `selector_func` that returns `UserProxyAgent.name` when the last message indicates human input is required (e.g. "HUMAN_INPUT_NEEDED" or "human_action_required": true); otherwise use default model-based selection.

**Alternatives considered**:
- Separate human UI outside the chat: Rejected; spec requires human response in the same chat.
- Human as a special "agent" implemented with AssistantAgent: Rejected; UserProxyAgent is the supported pattern for real human input.

## 4. Selector Prompt and Termination

**Decision**: Use a custom `selector_prompt` that includes participant roles and conversation history (using `{roles}`, `{history}`, `{participants}`). Instruct the selector to prefer Intake for new requests, then Policy/Finance/Vendor as appropriate, then Reviewer to synthesize, then Human when the conversation indicates human input is needed. Use termination conditions: e.g. `MaxMessageTermination(max_messages=...)` to cap turns, and optionally `TextMentionTermination("TERMINATE")` or a decision-based stop when the Human Proxy or Reviewer signals completion.

**Rationale**:
- SelectorGroupChat supports `selector_prompt` with placeholders; agent descriptions are already in `AGENT_DESCRIPTIONS`, so we can format roles for the prompt.
- Procurement flow is ordered conceptually (intake → validation agents → reviewer → human); the selector prompt can encode this without overloading the model (per docs: avoid too many conditions for small models).
- Termination: spec SC-001 suggests "under 20 agent/human turns"; MaxMessageTermination(20) or similar plus explicit TERMINATE from Reviewer/Human keeps runs bounded.

**Alternatives considered**:
- Fully custom `selector_func` with state machine: Possible follow-up; for MVP, a clear selector_prompt plus default model-based selection is simpler and matches the docs example.

## 5. Tool Hosting (Constitution – MCP)

**Decision**: Implement this feature using the existing in-process tools from `hil/tools.py` (Python callables passed to `AssistantAgent(tools=[...])`). Document a constitution deviation: MCP is required by the project constitution, but the current agent/tool definitions are in-process; migrating these tools to MCP is deferred to a follow-up so this feature can ship without blocking on MCP infrastructure.

**Rationale**:
- Constitution states agent tools MUST be hosted via MCP; the HIL prompts and tools are currently defined as in-process callables.
- Migrating to MCP in this feature would require MCP server(s) for procurement tools, client wiring in AutoGen, and possible changes to agent definitions; that is a larger scope.
- Tracking the deviation in the plan’s Complexity Tracking allows the team to plan MCP migration later while still delivering the selector group chat.

**Alternatives considered**:
- Implementing MCP in this feature: Rejected for scope; captured as follow-up.
- Amending the constitution to allow in-process tools for this project: Rejected; deviation with justification is the chosen path.
