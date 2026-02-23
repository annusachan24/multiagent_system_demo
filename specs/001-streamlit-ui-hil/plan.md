# Implementation Plan: Web UI for Procurement Selector Group Chat (Streamlit)

**Branch**: `001-streamlit-ui-hil` | **Date**: 2025-02-21 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-streamlit-ui-hil/spec.md`

## Summary

Provide a web-based, visually polished UI for the existing procurement selector group chat so users can start a chat with a task string, see agent and user messages in order, and submit human responses when the workflow asks—without using the CLI. The implementation wraps the existing `hil/selector_group_chat_with_hil` run flow (SelectorGroupChat + run_stream) and replaces the Console UI with a Streamlit app that consumes the same stream and supplies human input via a custom UserInputManager.

## Technical Context

**Language/Version**: Python 3.10+ (align with existing project)  
**Primary Dependencies**: Existing autogen-agentchat, autogen-ext[openai]; add Streamlit for the web UI  
**Storage**: N/A (conversation in-memory for the session; Streamlit session state for UI state)  
**Testing**: pytest for any non-UI logic; lint/format per PEP 8 (Ruff/Black); manual or widget tests for Streamlit UI as needed  
**Target Platform**: Web browser (Streamlit server runs locally or on a host)  
**Project Type**: Single project with a new Streamlit app entrypoint alongside existing `hil/`  
**Performance Goals**: UI remains responsive during agent turns; loading/progress indication when the run is active (spec SC-003, edge case)  
**Constraints**: PEP 8; no change to Autogen agent/tool design; human input must be supplied in the same run when the stream pauses for UserProxyAgent  
**Scale/Scope**: One active chat per browser session; one procurement request per chat (per spec)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **PEP 8**: Linting/formatting (e.g. Ruff/Black) configured; all new code passes.
- **Autogen**: Multi-agent design is unchanged; this feature adds a UI layer that invokes the existing SelectorGroupChat and run_stream. No new agents or orchestration.
- **MCP**: No new tools or MCP surface. The existing in-process tools (hil/tools.py) remain as in 001-selector-group-chat; this feature does not add or change tool hosting.

*Post Phase 1*: No changes; UI layer only.

## Project Structure

### Documentation (this feature)

```text
specs/001-streamlit-ui-hil/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── streamlit-ui-entrypoint.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
hil/
├── prompts.py           # Unchanged
├── tools.py             # Unchanged
├── selector_group_chat_with_hil.py   # May expose run_stream + team build for reuse
└── streamlit_ui.py     # NEW: Streamlit app — layout, message display, run loop, UserInputManager

# Optional: if UI grows, consider
# hil/app/
#   streamlit_ui.py
#   streamlit_runner.py  # Consumes run_stream, pushes to UI, uses UserInputManager for human input
```

**Structure Decision**: Single project. New Streamlit app lives under `hil/` (e.g. `hil/streamlit_ui.py`) so it can import the existing team builder and run logic from `hil/selector_group_chat_with_hil`. No new top-level packages. Optional refactor: extract a small “runner” module that consumes the stream and uses a pluggable UserInputManager if that keeps streamlit_ui.py simpler.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (None)    | —          | —                                   |
