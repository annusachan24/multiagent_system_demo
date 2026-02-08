"""
Unit tests for demo/tools.py — all procurement workflow tools.
Run from repo root: pytest multiagent_system_demo/tests/test_tools.py -v
"""

import pytest
from demo.tools import (
    extract_procurement_fields,
    validate_required_fields,
    check_policy,
    approval_matrix,
    check_budget,
    forecast_spend,
    lookup_vendor,
    vendor_risk_score,
    generate_request_id,
)


# ---------------------------------------------------------------------
# Intake Agent Tools
# ---------------------------------------------------------------------

class TestExtractProcurementFields:
    """Tests for extract_procurement_fields(text)."""

    def test_empty_string_returns_hint(self):
        result = extract_procurement_fields("")
        assert "_hint" in result
        assert "procure" in result["_hint"].lower()

    def test_none_returns_hint(self):
        result = extract_procurement_fields(None)
        assert "_hint" in result

    def test_non_string_returns_hint(self):
        result = extract_procurement_fields(123)
        assert "_hint" in result

    def test_full_request_extracts_all_fields(self):
        text = "We need 50 MacBooks for engineering, budget 75L, next quarter, Apple authorized vendor."
        result = extract_procurement_fields(text)
        assert result.get("item_name") == "MacBook"
        assert result.get("quantity") == 50
        assert result.get("estimated_budget") == 7500000
        assert result.get("currency") == "INR"
        assert result.get("department") == "Engineering"
        assert result.get("timeline") == "Next Quarter"
        assert result.get("vendor_preference") == "Apple Authorized Vendor"

    def test_macbook_triggers_item_name(self):
        result = extract_procurement_fields("Need MacBook for team")
        assert result.get("item_name") == "MacBook"

    def test_75_or_75l_triggers_budget(self):
        assert extract_procurement_fields("budget 75L")["estimated_budget"] == 7500000
        assert extract_procurement_fields("around 75 lakh")["estimated_budget"] == 7500000

    def test_50_triggers_quantity(self):
        result = extract_procurement_fields("50 laptops")
        assert result.get("quantity") == 50

    def test_engineering_tech_developers_map_to_engineering(self):
        for word in ("engineering", "tech", "developers"):
            result = extract_procurement_fields(f"request from {word} team")
            assert result.get("department") == "Engineering"

    def test_marketing_hr_maps(self):
        assert extract_procurement_fields("marketing campaign")["department"] == "Marketing"
        assert extract_procurement_fields("HR needs")["department"] == "HR"

    def test_vague_input_returns_partial_or_none(self):
        result = extract_procurement_fields("we need some stuff")
        assert "item_name" in result
        assert result.get("item_name") is None or result.get("quantity") is None


class TestValidateRequiredFields:
    """Tests for validate_required_fields(fields)."""

    REQUIRED = ["item_name", "quantity", "estimated_budget", "currency", "department"]

    def test_none_returns_all_required(self):
        assert validate_required_fields(None) == self.REQUIRED

    def test_empty_dict_returns_all_required(self):
        assert validate_required_fields({}) == self.REQUIRED

    def test_dict_with_hint_returns_all_required(self):
        assert validate_required_fields({"_hint": "describe request"}) == self.REQUIRED

    def test_all_present_returns_empty(self):
        full = {
            "item_name": "MacBook",
            "quantity": 50,
            "estimated_budget": 7500000,
            "currency": "INR",
            "department": "Engineering",
        }
        assert validate_required_fields(full) == []

    def test_partial_returns_missing_only(self):
        partial = {"item_name": "MacBook", "quantity": 50}
        missing = validate_required_fields(partial)
        assert "item_name" not in missing
        assert "quantity" not in missing
        assert "estimated_budget" in missing
        assert "currency" in missing
        assert "department" in missing


# ---------------------------------------------------------------------
# Policy Agent Tools
# ---------------------------------------------------------------------

class TestCheckPolicy:
    """Tests for check_policy(estimated_budget, category)."""

    def test_below_50l_no_issue(self):
        result = check_policy(4_000_000)
        assert result["policy_status"] == "NO_ISSUE"
        assert "Within standard" in result["message"]

    def test_50l_or_above_soft_block(self):
        result = check_policy(5_000_000)
        assert result["policy_status"] == "SOFT_BLOCK"
        assert "50L" in result["message"] or "Approval" in result["message"]

    def test_above_50l_soft_block(self):
        result = check_policy(10_000_000)
        assert result["policy_status"] == "SOFT_BLOCK"

    def test_none_budget_returns_no_issue_message(self):
        result = check_policy(None)
        assert result["policy_status"] == "NO_ISSUE"
        assert "estimated budget" in result["message"].lower()

    def test_invalid_budget_type_returns_no_issue_message(self):
        result = check_policy("not a number")
        assert "policy_status" in result
        assert "message" in result


class TestApprovalMatrix:
    """Tests for approval_matrix(amount)."""

    def test_under_10l_manager(self):
        assert approval_matrix(500_000) == "Manager Approval"

    def test_10l_to_50l_director(self):
        assert approval_matrix(1_000_000) == "Director Approval"
        assert approval_matrix(4_000_000) == "Director Approval"

    def test_50l_plus_vp(self):
        assert approval_matrix(5_000_000) == "VP Approval"
        assert approval_matrix(10_000_000) == "VP Approval"

    def test_none_returns_message(self):
        out = approval_matrix(None)
        assert "amount" in out.lower() or "approval" in out

    def test_invalid_returns_message(self):
        out = approval_matrix("abc")
        assert isinstance(out, str)
        assert len(out) > 0


# ---------------------------------------------------------------------
# Finance Agent Tools
# ---------------------------------------------------------------------

class TestCheckBudget:
    """Tests for check_budget(department, amount)."""

    def test_engineering_has_budget(self):
        result = check_budget("Engineering", 5_000_000)
        assert result["available_budget"] == 8_000_000
        assert result["sufficient"] is True

    def test_engineering_insufficient_if_over_8l(self):
        result = check_budget("Engineering", 10_000_000)
        assert result["available_budget"] == 8_000_000
        assert result["sufficient"] is False

    def test_marketing_hr_limits(self):
        assert check_budget("Marketing", 2_000_000)["available_budget"] == 3_000_000
        assert check_budget("HR", 1_000_000)["available_budget"] == 2_000_000

    def test_unknown_department_zero_available(self):
        result = check_budget("UnknownDept", 100)
        assert result["available_budget"] == 0
        assert result["sufficient"] is False

    def test_empty_department_returns_message(self):
        result = check_budget("", 1000)
        assert "message" in result
        assert "department" in result["message"].lower()

    def test_none_department_returns_message(self):
        result = check_budget(None, 1000)
        assert "message" in result

    def test_invalid_amount_returns_message(self):
        result = check_budget("Engineering", None)
        assert "message" in result
        assert result.get("sufficient") is False


class TestForecastSpend:
    """Tests for forecast_spend(amount)."""

    def test_low_risk(self):
        assert forecast_spend(2_000_000) == "LOW"

    def test_medium_risk(self):
        assert forecast_spend(4_000_000) == "MEDIUM"

    def test_high_risk(self):
        assert forecast_spend(8_000_000) == "HIGH"

    def test_none_returns_message(self):
        out = forecast_spend(None)
        assert "amount" in out.lower() or "risk" in out.lower()

    def test_invalid_returns_message(self):
        out = forecast_spend("x")
        assert isinstance(out, str)


# ---------------------------------------------------------------------
# Vendor Risk Agent Tools
# ---------------------------------------------------------------------

class TestLookupVendor:
    """Tests for lookup_vendor(vendor_name)."""

    def test_apple_authorized_approved(self):
        result = lookup_vendor("Apple Authorized Vendor")
        assert result["status"] == "APPROVED"
        assert result["vendor_name"] == "Apple Authorized Vendor"

    def test_dell_preferred_approved(self):
        result = lookup_vendor("Dell Preferred Partner")
        assert result["status"] == "APPROVED"

    def test_unknown_vendor_returns_unknown(self):
        result = lookup_vendor("Random Vendor LLC")
        assert result["status"] == "UNKNOWN"

    def test_empty_string_returns_message(self):
        result = lookup_vendor("")
        assert result["status"] == "UNKNOWN"
        assert "message" in result

    def test_whitespace_stripped(self):
        result = lookup_vendor("  Apple Authorized Vendor  ")
        assert result["status"] == "APPROVED"


class TestVendorRiskScore:
    """Tests for vendor_risk_score(vendor_name)."""

    def test_approved_vendors_low_risk(self):
        assert vendor_risk_score("Apple Authorized Vendor")["risk_rating"] == "LOW"
        assert vendor_risk_score("Dell Preferred Partner")["risk_rating"] == "LOW"

    def test_unknown_vendor_medium_risk(self):
        result = vendor_risk_score("Unknown Corp")
        assert result["risk_rating"] == "MEDIUM"

    def test_contract_in_place_for_known(self):
        result = vendor_risk_score("Apple Authorized Vendor")
        assert result["contract_in_place"] is True
        assert result["vendor_name"] == "Apple Authorized Vendor"

    def test_empty_returns_message(self):
        result = vendor_risk_score("")
        assert "message" in result or "risk_rating" in result
        assert result.get("risk_rating") in ("LOW", "MEDIUM", "HIGH", None) or "message" in result


# ---------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------

class TestGenerateRequestId:
    """Tests for generate_request_id()."""

    def test_returns_string(self):
        assert isinstance(generate_request_id(), str)

    def test_format_pr_prefix(self):
        rid = generate_request_id()
        assert rid.startswith("PR-")

    def test_contains_digits(self):
        rid = generate_request_id()
        num_part = rid.replace("PR-", "")
        assert num_part.isdigit()
        assert 10000 <= int(num_part) <= 99999
