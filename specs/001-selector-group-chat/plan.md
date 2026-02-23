# Implementation Plan: Selector Group Chat for Procurement (HIL)

**Branch**: `001-selector-group-chat` | **Date**: 2025-02-21 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-selector-group-chat/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Implement a selector group chat where six specialized agents (Intake, Policy, Finance, Vendor Risk, Reviewer, Human Proxy) collaborate on a single procurement request, using the existing agent prompts and tool set from the HIL module. The chat uses AutoGen’s [SelectorGroupChat](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/selector-group-chat.html) with model-based next-speaker selection; the human participates via UserProxyAgent when the workflow requests input or final decision. Tools are wired from `hil/tools.py`; agent definitions and prompts come from `hil/prompts.py`.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: autogen-agentchat (0.7.5), autogen-ext[openai]; existing code uses `OpenAIChatCompletionClient`, `AssistantAgent`, `SelectorGroupChat`, `UserProxyAgent`  
**Storage**: N/A (conversation context in-memory for the run)  
**Testing**: pytest (or project standard); lint/format per PEP 8 (e.g. Ruff/Black)  
**Target Platform**: Local/CLI (Console UI for streamed chat)  
**Project Type**: Single project (repository root with `hil/`, scripts at root or under `hil/`)  
**Performance Goals**: Typical request resolved or escalated within a reasonable number of turns (e.g. &lt; 20)  
**Constraints**: PEP 8; tools currently in-process (see Constitution deviation below)  
**Scale/Scope**: One procurement request per chat session; six agents + human

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **PEP 8**: Linting/formatting (e.g. Ruff/Black) configured; all new code passes.
- **Autogen**: Multi-agent design uses Autogen SelectorGroupChat; agent roles and orchestration documented in this plan and in `research.md`.
- **MCP**: Agent tools are currently in-process (hil/tools.py). **Deviation**: See Complexity Tracking. MCP adoption is deferred to a follow-up; this feature uses existing in-process tool definitions to deliver the selector group chat.

## Project Structure

### Documentation (this feature)

```text
specs/001-selector-group-chat/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── selector-group-chat-entrypoint.md
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
hil/
├── prompts.py           # Existing: agent prompts + AGENT_CONFIG (update to use hil.tools)
├── tools.py             # Existing: procurement tools (extract, validate, policy, finance, vendor)
└── selector_group_chat_with_hil.py   # NEW: build agents from prompts/tools, SelectorGroupChat + UserProxyAgent, run entrypoint

selector_group_chat.py   # Existing: reference example (Planning, WebSearch, DataAnalyst)
```

**Structure Decision**: Single project. The feature adds one new file under `hil/` (`selector_group_chat_with_hil.py`) and may update `hil/prompts.py` to import tools from `hil.tools` instead of `demo.tools` so the HIL selector chat is self-contained. No new top-level packages.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| In-process tools (hil/tools.py) instead of MCP | Existing agent and tool definitions are in-process; spec requires using “these tools” (hil/tools.py) and existing prompts. Delivering the selector group chat first unblocks value. | Migrating all HIL tools to MCP in this feature would require MCP server(s), client wiring, and possible agent changes; that is a larger, separate scope. MCP adoption is planned as a follow-up. |
