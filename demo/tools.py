"""
Tool implementations for AutoGen-based
multi-agent procurement workflow.

All tools are:
- Deterministic
- Side-effect free
- Easy to replace with real services
"""

from typing import Dict, List
import random


# ---------------------------------------------------------------------
# Intake Agent Tools
# ---------------------------------------------------------------------

def extract_procurement_fields(text: str) -> Dict:
    """
    Extract structured procurement fields from free text.
    NOTE: This is a mocked deterministic extractor.
    Returns friendly follow-up hints instead of raising.
    """
    if not text or not isinstance(text, str):
        return {"_hint": "Please describe what you want to procure (item, quantity, budget, department)."}

    text_lower = text.lower()

    # Map common department words to department name
    dept = None
    if "engineering" in text_lower or "tech" in text_lower or "developers" in text_lower:
        dept = "Engineering"
    elif "marketing" in text_lower:
        dept = "Marketing"
    elif "hr" in text_lower or "human" in text_lower:
        dept = "HR"

    fields = {
        "item_name": "MacBook" if "macbook" in text_lower else None,
        "quantity": 50 if "50" in text_lower else None,
        "estimated_budget": 7500000 if "75" in text_lower or "75l" in text_lower else None,
        "currency": "INR",
        "department": dept or ("Engineering" if "hire" in text_lower else None),
        "timeline": "Next Quarter" if "quarter" in text_lower else None,
        "vendor_preference": "Apple Authorized Vendor" if "apple" in text_lower else None,
    }

    return fields


def validate_required_fields(fields: Dict | None = None) -> List[str]:
    """
    Identify missing required fields.
    Department is required for budget checks.
    Call with the result of extract_procurement_fields; if omitted or empty, returns all as missing.
    """
    if fields is None or not fields or fields.get("_hint"):
        return ["item_name", "quantity", "estimated_budget", "currency", "department"]
    required = ["item_name", "quantity", "estimated_budget", "currency", "department"]
    missing = [f for f in required if not fields.get(f)]
    return missing


# ---------------------------------------------------------------------
# Policy Agent Tools
# ---------------------------------------------------------------------

def check_policy(estimated_budget: int, category: str = "IT_EQUIPMENT") -> Dict:
    """
    Validate procurement against policy rules.
    """
    try:
        amount = int(estimated_budget) if estimated_budget is not None else 0
    except (TypeError, ValueError):
        return {
            "policy_status": "NO_ISSUE",
            "message": "Please provide the estimated budget so we can check policy."
        }
    if amount >= 5000000:
        return {
            "policy_status": "SOFT_BLOCK",
            "message": "Approval required for purchases above 50L"
        }
    return {
        "policy_status": "NO_ISSUE",
        "message": "Within standard procurement limits"
    }


def approval_matrix(amount: int) -> str:
    """
    Determine approval authority.
    """
    try:
        amt = int(amount) if amount is not None else 0
    except (TypeError, ValueError):
        return "Please provide the amount to determine approval authority."
    if amt < 1000000:
        return "Manager Approval"
    elif amt < 5000000:
        return "Director Approval"
    else:
        return "VP Approval"


# ---------------------------------------------------------------------
# Finance Agent Tools
# ---------------------------------------------------------------------

def check_budget(department: str, amount: int) -> Dict:
    """
    Check departmental budget availability.
    """
    if not department or not str(department).strip():
        return {
            "available_budget": 0,
            "sufficient": False,
            "message": "Which department is this request for? (e.g. Engineering, Marketing, HR)"
        }
    try:
        amt = int(amount) if amount is not None else 0
    except (TypeError, ValueError):
        return {
            "available_budget": 0,
            "sufficient": False,
            "message": "What is the estimated amount for this request?"
        }
    mock_budget = {
        "Engineering": 8000000,
        "Marketing": 3000000,
        "HR": 2000000
    }
    available = mock_budget.get(str(department).strip(), 0)
    return {
        "available_budget": available,
        "sufficient": available >= amt
    }


def forecast_spend(amount: int) -> str:
    """
    Identify spend risk pattern.
    """
    try:
        amt = int(amount) if amount is not None else 0
    except (TypeError, ValueError):
        return "Please provide the amount to assess spend risk."
    if amt > 7000000:
        return "HIGH"
    elif amt > 3000000:
        return "MEDIUM"
    return "LOW"


# ---------------------------------------------------------------------
# Vendor Risk Agent Tools
# ---------------------------------------------------------------------

def lookup_vendor(vendor_name: str) -> Dict:
    """
    Lookup vendor status in vendor registry.
    """
    if not vendor_name or not str(vendor_name).strip():
        return {
            "vendor_name": "",
            "status": "UNKNOWN",
            "message": "Which vendor do you prefer? (e.g. Apple Authorized Vendor)"
        }
    name = str(vendor_name).strip()
    approved_vendors = {
        "Apple Authorized Vendor": True,
        "Dell Preferred Partner": True
    }
    if name in approved_vendors:
        return {"vendor_name": name, "status": "APPROVED"}
    return {"vendor_name": name, "status": "UNKNOWN"}


def vendor_risk_score(vendor_name: str) -> Dict:
    """
    Return vendor risk rating.
    """
    if not vendor_name or not str(vendor_name).strip():
        return {
            "vendor_name": "",
            "risk_rating": "MEDIUM",
            "contract_in_place": False,
            "message": "Which vendor is this for?"
        }
    name = str(vendor_name).strip()
    risk_map = {
        "Apple Authorized Vendor": "LOW",
        "Dell Preferred Partner": "LOW"
    }
    return {
        "vendor_name": name,
        "risk_rating": risk_map.get(name, "MEDIUM"),
        "contract_in_place": name in risk_map
    }


# ---------------------------------------------------------------------
# Utility / Shared Tools (Optional)
# ---------------------------------------------------------------------

def generate_request_id() -> str:
    """
    Generate a mock procurement request ID.
    """

    return f"PR-{random.randint(10000, 99999)}"
