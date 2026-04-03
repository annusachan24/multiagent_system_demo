# Demo scripts: to-and-fro conversations (HIL selector group chat)

These are **illustrative** scripts for rehearsing a live demo. The real model may phrase things differently, but the **facts you type** and the **order of turns** should match so every tool path is exercised.

**Speaker labels:** **You** = your message in Streamlit or console. **Agents** = assistant turns. **HumanProxy** = the slot where the app waits for you when `HUMAN_INPUT_NEEDED` / handoff fires.

---

## Scenario 1 — Full request, high budget, Apple vendor (→ PR creation)

**Goal:** Intake (extract + validate), Policy (`check_policy` ≥50L, `approval_matrix` VP), Finance (`check_budget` Engineering, `forecast_spend` MEDIUM), Vendor (`lookup_vendor`, `vendor_risk_score` approved), Reviewer → **You confirm** → Intake (`create_purchase_request`).

| Turn | Speaker | What to say (copy or paraphrase) |
|------|---------|----------------------------------|
| 1 | **You** | We need 50 MacBooks for Engineering, budget 75 lakhs INR, next quarter. Prefer Apple Authorized Vendor. |
| 2 | **IntakeAgent** | *(Uses `extract_procurement_fields`, `validate_required_fields`.)* Structures fields; status READY_FOR_REVIEW. |
| 3 | **PolicyAgent** | *(Uses `check_policy`, `approval_matrix`.)* SOFT_BLOCK or special approval above 50L; VP approval level. |
| 4 | **FinanceAgent** | *(Uses `check_budget`, `forecast_spend`.)* Engineering budget vs 75L; spend risk MEDIUM. |
| 5 | **VendorRiskAgent** | *(Uses `lookup_vendor`, `vendor_risk_score`.)* Apple Authorized Vendor = APPROVED, LOW risk. |
| 6 | **ReviewerAgent** | Summarizes; may recommend AUTO_APPROVE with policy note; asks you to confirm. Includes **HUMAN_INPUT_NEEDED** or similar. |
| 7 | **HumanProxy** *(you)* | I confirm approval for this request. Please proceed and create the purchase request. *(Or: “Approved. Create the PR.”)* |
| 8 | **IntakeAgent** | *(Uses `create_purchase_request`.)* Returns PR id; message ends with **TERMINATE**. |

**If the run stops earlier:** If Intake asks for clarification, answer in plain language with the same numbers and vendor name, then let the flow continue until Reviewer asks for you again.

---

## Scenario 2 — Lower budget, HR, Dell (different policy / approval / forecast paths)

**Goal:** Same tool *types*, different branches: `check_policy` NO_ISSUE, `approval_matrix` Manager, `forecast_spend` LOW, `check_budget` HR, vendor tools on **Dell Preferred Partner**.

| Turn | Speaker | What to say |
|------|---------|-------------|
| 1 | **You** | Order 10 monitors for HR, estimated budget 5 lakhs INR total, timeline this quarter. Preferred vendor: Dell Preferred Partner. |
| 2 | **IntakeAgent** | Extracts quantity, department HR, budget 500000 INR, vendor preference, etc. |
| 3 | **PolicyAgent** | Policy within limits; Manager-level approval for this amount. |
| 4 | **FinanceAgent** | HR departmental budget vs 5L; forecast LOW. |
| 5 | **VendorRiskAgent** | Dell Preferred Partner — approved registry, LOW risk. |
| 6 | **ReviewerAgent** | AUTO_APPROVE or short summary; may ask you to confirm. |
| 7 | **HumanProxy** *(you)* | Approved. Please create the purchase request. |
| 8 | **IntakeAgent** | `create_purchase_request` → PR id → **TERMINATE**. |

---

## Scenario 3 — Vague start, then unknown vendor (clarification + vendor UNKNOWN)

**Goal:** Force **`validate_required_fields`** and follow-up extraction; then Policy / Finance / Vendor on a **non-catalog** vendor (**Contoso Supplies**) so `lookup_vendor` / `vendor_risk_score` hit UNKNOWN / MEDIUM paths.

| Turn | Speaker | What to say |
|------|---------|-------------|
| 1 | **You** | We need to buy laptops for new hires soon. |
| 2 | **IntakeAgent** | *(Extract + validate.)* Missing quantity, budget, department, timeline; asks clarifying questions. Message includes **HUMAN_INPUT_NEEDED**. |
| 3 | **HumanProxy** *(you)* | 20 laptops, 40 lakhs INR, Engineering department, next quarter. Use vendor Contoso Supplies — they are new, not on our usual approved list. |
| 4 | **IntakeAgent** | Fills structured request; READY_FOR_REVIEW. |
| 5 | **PolicyAgent** | Runs policy tools on stated budget. |
| 6 | **FinanceAgent** | Runs budget + forecast for Engineering + amount. |
| 7 | **VendorRiskAgent** | Contoso Supplies → UNKNOWN / MEDIUM in mock registry. |
| 8 | **ReviewerAgent** | May flag vendor risk or ask whether to proceed; may include **HUMAN_INPUT_NEEDED**. |
| 9 | **HumanProxy** *(you)* | *(Example.)* Understood on vendor risk. I approve proceeding with Contoso for this pilot. Create the PR if policy and finance are acceptable. |
| 10 | **ReviewerAgent** / **IntakeAgent** | As the model routes, Intake eventually **`create_purchase_request`** after clear approval. |

**Optional shorter second user turn** (if Intake only asked for one thing first): split into two human replies, e.g. first only budget + department, second vendor name — still valid as long as the final structured request mentions **Contoso Supplies**.

---

## Quick reference: what each scenario stresses

| Scenario | Intake tools | Policy | Finance | Vendor | PR |
|----------|--------------|--------|---------|--------|-----|
| 1 | extract, validate, create_purchase_request | high ₹, VP | Eng + 75L, MEDIUM | Apple approved | Yes |
| 2 | same | low ₹, Manager | HR + 5L, LOW | Dell approved | Yes |
| 3 | extract, validate, (+ create at end) | per 40L | Eng + 40L | Contoso UNKNOWN | Yes (if approved) |

For a **short live demo**, run **Scenario 1** end-to-end first; add **Scenario 3** if you need to show clarification + unknown vendor in one sitting.
