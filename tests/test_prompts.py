"""
Tests for demo/prompts.py — prompt content and AGENT_CONFIG structure.
Run from repo root: pytest multiagent_system_demo/tests/test_prompts.py -v
"""

import pytest
from demo.prompts import (
    INTAKE_AGENT_PROMPT,
    POLICY_AGENT_PROMPT,
    FINANCE_AGENT_PROMPT,
    VENDOR_RISK_AGENT_PROMPT,
    REVIEWER_AGENT_PROMPT,
    HUMAN_PROXY_AGENT_PROMPT,
    AGENT_CONFIG,
)
from demo.tools import (
    extract_procurement_fields,
    validate_required_fields,
    check_policy,
    approval_matrix,
    check_budget,
    forecast_spend,
    lookup_vendor,
    vendor_risk_score,
)


# ---------------------------------------------------------------------
# Intake Agent Prompt
# ---------------------------------------------------------------------

class TestIntakeAgentPrompt:
    def test_contains_required_field_names(self):
        for field in ("item_name", "quantity", "estimated_budget", "currency", "department"):
            assert field in INTAKE_AGENT_PROMPT

    def test_contains_status_values(self):
        assert "READY_FOR_REVIEW" in INTAKE_AGENT_PROMPT
        assert "INCOMPLETE" in INTAKE_AGENT_PROMPT

    def test_contains_human_input_marker(self):
        assert "HUMAN_INPUT_NEEDED" in INTAKE_AGENT_PROMPT

    def test_mentions_tools(self):
        assert "tool" in INTAKE_AGENT_PROMPT.lower()

    def test_mentions_missing_fields(self):
        assert "missing" in INTAKE_AGENT_PROMPT.lower()

    def test_output_format_has_extracted_fields(self):
        assert "extracted_fields" in INTAKE_AGENT_PROMPT
        assert "missing_fields" in INTAKE_AGENT_PROMPT
        assert "notes" in INTAKE_AGENT_PROMPT


# ---------------------------------------------------------------------
# Policy Agent Prompt
# ---------------------------------------------------------------------

class TestPolicyAgentPrompt:
    def test_contains_policy_classifications(self):
        for level in ("HARD_BLOCK", "SOFT_BLOCK", "NO_ISSUE"):
            assert level in POLICY_AGENT_PROMPT

    def test_contains_recommendation_options(self):
        for rec in ("approve", "escalate", "reject"):
            assert rec in POLICY_AGENT_PROMPT.lower()

    def test_mentions_policy_tools(self):
        assert "policy" in POLICY_AGENT_PROMPT.lower()
        assert "tool" in POLICY_AGENT_PROMPT.lower()

    def test_output_format_has_required_keys(self):
        assert "policy_status" in POLICY_AGENT_PROMPT
        assert "approval_required" in POLICY_AGENT_PROMPT
        assert "recommendation" in POLICY_AGENT_PROMPT


# ---------------------------------------------------------------------
# Finance Agent Prompt
# ---------------------------------------------------------------------

class TestFinanceAgentPrompt:
    def test_contains_budget_status_values(self):
        for status in ("OK", "WARNING", "INSUFFICIENT"):
            assert status in FINANCE_AGENT_PROMPT

    def test_contains_risk_levels(self):
        for level in ("LOW", "MEDIUM", "HIGH"):
            assert level in FINANCE_AGENT_PROMPT

    def test_mentions_finance_tools(self):
        assert "finance" in FINANCE_AGENT_PROMPT.lower()
        assert "budget" in FINANCE_AGENT_PROMPT.lower()

    def test_output_format_has_required_keys(self):
        assert "budget_status" in FINANCE_AGENT_PROMPT
        assert "available_budget" in FINANCE_AGENT_PROMPT
        assert "requested_amount" in FINANCE_AGENT_PROMPT
        assert "risk_level" in FINANCE_AGENT_PROMPT


# ---------------------------------------------------------------------
# Vendor Risk Agent Prompt
# ---------------------------------------------------------------------

class TestVendorRiskAgentPrompt:
    def test_contains_vendor_status_values(self):
        for status in ("APPROVED", "NOT_APPROVED", "UNKNOWN"):
            assert status in VENDOR_RISK_AGENT_PROMPT

    def test_contains_risk_rating(self):
        assert "risk_rating" in VENDOR_RISK_AGENT_PROMPT

    def test_mentions_vendor_tools(self):
        assert "vendor" in VENDOR_RISK_AGENT_PROMPT.lower()
        assert "tool" in VENDOR_RISK_AGENT_PROMPT.lower()

    def test_output_has_issues_list(self):
        assert "issues" in VENDOR_RISK_AGENT_PROMPT


# ---------------------------------------------------------------------
# Reviewer Agent Prompt
# ---------------------------------------------------------------------

class TestReviewerAgentPrompt:
    def test_contains_decision_options(self):
        for decision in ("AUTO_APPROVE", "ESCALATE_TO_HUMAN", "REJECT", "NEED_MORE_INFO"):
            assert decision in REVIEWER_AGENT_PROMPT

    def test_mentions_no_tools(self):
        assert "Never use tools" in REVIEWER_AGENT_PROMPT or "never use tool" in REVIEWER_AGENT_PROMPT.lower()

    def test_output_has_summary_and_decision(self):
        assert "summary" in REVIEWER_AGENT_PROMPT
        assert "decision" in REVIEWER_AGENT_PROMPT
        assert "human_action_required" in REVIEWER_AGENT_PROMPT
        assert "questions_for_human" in REVIEWER_AGENT_PROMPT


# ---------------------------------------------------------------------
# Human Proxy Agent Prompt
# ---------------------------------------------------------------------

class TestHumanProxyAgentPrompt:
    def test_contains_final_decision_options(self):
        for opt in ("APPROVED", "REJECTED", "MODIFIED"):
            assert opt in HUMAN_PROXY_AGENT_PROMPT

    def test_has_conditions_and_notes(self):
        assert "conditions" in HUMAN_PROXY_AGENT_PROMPT
        assert "notes" in HUMAN_PROXY_AGENT_PROMPT


# ---------------------------------------------------------------------
# AGENT_CONFIG
# ---------------------------------------------------------------------

class TestAgentConfig:
    EXPECTED_AGENTS = [
        "intake_agent",
        "policy_agent",
        "finance_agent",
        "vendor_risk_agent",
        "reviewer_agent",
        "human_proxy_agent",
    ]

    def test_has_all_expected_agents(self):
        for name in self.EXPECTED_AGENTS:
            assert name in AGENT_CONFIG

    def test_each_agent_has_prompt_and_tools(self):
        for name, config in AGENT_CONFIG.items():
            assert "prompt" in config, f"{name} missing 'prompt'"
            assert "tools" in config, f"{name} missing 'tools'"
            assert isinstance(config["prompt"], str), f"{name} prompt must be str"
            assert isinstance(config["tools"], list), f"{name} tools must be list"

    def test_prompts_non_empty(self):
        for name, config in AGENT_CONFIG.items():
            assert len(config["prompt"].strip()) > 100, f"{name} prompt too short"

    def test_intake_agent_tools(self):
        tools = AGENT_CONFIG["intake_agent"]["tools"]
        assert extract_procurement_fields in tools
        assert validate_required_fields in tools
        assert len(tools) == 2

    def test_policy_agent_tools(self):
        tools = AGENT_CONFIG["policy_agent"]["tools"]
        assert check_policy in tools
        assert approval_matrix in tools
        assert len(tools) == 2

    def test_finance_agent_tools(self):
        tools = AGENT_CONFIG["finance_agent"]["tools"]
        assert check_budget in tools
        assert forecast_spend in tools
        assert len(tools) == 2

    def test_vendor_risk_agent_tools(self):
        tools = AGENT_CONFIG["vendor_risk_agent"]["tools"]
        assert lookup_vendor in tools
        assert vendor_risk_score in tools
        assert len(tools) == 2

    def test_reviewer_and_human_have_no_tools(self):
        assert AGENT_CONFIG["reviewer_agent"]["tools"] == []
        assert AGENT_CONFIG["human_proxy_agent"]["tools"] == []
