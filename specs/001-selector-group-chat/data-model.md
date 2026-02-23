# Data Model: Selector Group Chat for Procurement

**Feature**: 001-selector-group-chat  
**Phase**: 1 – Design

Entities below are logical; no storage or API schema is implied unless stated in contracts.

## 1. Procurement Request

Represents the user’s request as it moves through the workflow.

| Attribute          | Description |
|-------------------|-------------|
| item_name         | Item to procure (optional until filled). |
| quantity          | Numeric quantity (optional until filled). |
| estimated_budget  | Amount (numeric). |
| currency          | Currency code (e.g. INR). |
| department        | Department (e.g. Engineering, Marketing, HR). |
| timeline          | When needed (e.g. "Next Quarter"). |
| vendor_preference | Preferred vendor name (optional). |
| status            | INCOMPLETE \| READY_FOR_REVIEW. |
| missing_fields    | List of required field names when status is INCOMPLETE. |

**Validation**: Required fields for progression: item_name, quantity, estimated_budget, currency, department (per spec and existing tool behavior). When status is INCOMPLETE, the workflow requests human input for missing_fields before other agents run.

**State**: No formal state machine; status and missing_fields drive selector/human behavior (e.g. Intake sets INCOMPLETE and HUMAN_INPUT_NEEDED; after human responds, Intake can set READY_FOR_REVIEW).

## 2. Agent Findings

Structured outputs from Policy, Finance, and Vendor Risk agents (and Reviewer summary).

| Concept          | Attributes / Values |
|------------------|---------------------|
| Policy           | policy_status (NO_ISSUE \| SOFT_BLOCK \| HARD_BLOCK), issues, approval_required, recommendation (approve \| escalate \| reject), notes. |
| Finance          | budget_status (OK \| WARNING \| INSUFFICIENT), available_budget, requested_amount, risk_level (LOW \| MEDIUM \| HIGH), notes. |
| Vendor Risk      | vendor_name, vendor_status (APPROVED \| NOT_APPROVED \| UNKNOWN), risk_rating, issues, notes. |
| Reviewer summary | summary (policy, finance, vendor), decision (AUTO_APPROVE \| ESCALATE_TO_HUMAN \| REJECT \| NEED_MORE_INFO), reasoning, human_action_required, questions_for_human. |

**Relationships**: Findings are produced in chat messages; Reviewer synthesizes Policy, Finance, and Vendor findings into a single summary and decision.

## 3. Human Decision

Final outcome when the human responds via the Human Proxy.

| Attribute     | Description |
|--------------|-------------|
| final_decision | APPROVED \| REJECTED \| MODIFIED. |
| conditions    | Optional list of conditions (e.g. caps, approvals). |
| notes         | Optional justification or comments. |

**Usage**: When the workflow escalates or requests final decision, the human responds through the UserProxyAgent; that response is treated as final for the flow (no further agent validation required for approval/rejection).

## 4. Conversation Context (Runtime)

- **Participants**: Six agents (Intake, Policy, Finance, Vendor Risk, Reviewer, Human Proxy) plus UserProxyAgent for the human.
- **Messages**: Conversation history (user task, agent messages, tool calls/results, human replies) kept in the SelectorGroupChat team for the duration of the run; used by the selector to choose the next speaker and by agents to maintain context.
- **No persistence**: One procurement request per chat session; no requirement to persist conversation or request to a database in this feature.
