# Quickstart: Selector Group Chat for Procurement (HIL)

**Feature**: 001-selector-group-chat

## Prerequisites

- Python 3.10+.
- Dependencies installed: `pip install -r requirements.txt` (includes `autogen-agentchat`, `autogen-ext[openai]`).
- Environment: Set OpenAI API key (e.g. in `.env` or `OPENAI_API_KEY`).

## Run the Chat

1. **Entrypoint**: The implementation will provide a runnable module or script (e.g. `hil/selector_group_chat_with_hil.py` or similar) that:
   - Builds six AssistantAgents from `hil.prompts` (Intake, Policy, Finance, Vendor Risk, Reviewer) with tools from `hil.tools`.
   - Adds a UserProxyAgent for human-in-the-loop.
   - Constructs a `SelectorGroupChat` with a custom selector prompt and termination condition.
   - Runs the team with a task string (the procurement request).

2. **Example task** (natural language):
   ```text
   We need 50 MacBooks for Engineering, budget 75L INR, next quarter. Prefer Apple Authorized Vendor.
   ```

3. **Expected flow**:
   - Selector chooses Intake first; Intake extracts fields (and may request missing fields from the human).
   - After request is READY_FOR_REVIEW, Policy, Finance, and Vendor Risk may be selected to run their tools.
   - Reviewer is selected to synthesize and recommend (approve / escalate / reject / need more info).
   - When human input is required, UserProxyAgent is selected; you type your response in the console.
   - Run ends when a final decision is reached or max messages / TERMINATE.

4. **Validation**: Run with the example task and confirm all six agent roles participate as intended and tool calls match the defined tool set (see spec SC-003, SC-004).

## Project Layout (this feature)

- Agent definitions and prompts: `hil/prompts.py`.
- Tool implementations: `hil/tools.py`.
- Selector group chat wiring and run script: `hil/selector_group_chat_with_hil.py` (to be implemented).
