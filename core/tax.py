"""
Global Tax Index Logic – cross-border service & remittance tax calculation.
Stateless deterministic computation from tax_rates.json dataset.
"""
import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "tax_rates.json"

SERVICE_TYPES = {"care", "remittance", "general"}

def _load_rates() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def calculate_tax(
    from_country: str,
    to_country:   str,
    amount:       float,
    service_type: str = "care"
) -> dict:
    """
    Calculate T_global: effective cross-border tax rate for a payment corridor.
    Applies treaty discounts where applicable.
    """
    rates = _load_rates()

    from_country  = from_country.upper()
    to_country    = to_country.upper()
    service_type  = service_type.lower()

    countries = rates["countries"]

    if from_country not in countries:
        raise ValueError(f"Unsupported origin country: {from_country}")
    if to_country not in countries:
        raise ValueError(f"Unsupported destination country: {to_country}")
    if service_type not in SERVICE_TYPES:
        raise ValueError(f"service_type must be one of: {SERVICE_TYPES}")

    src = countries[from_country]
    dst = countries[to_country]

    has_treaty = to_country in src.get("tax_treaty_zones", [])

    # Base withholding
    base_withholding = dst["withholding_base"]
    treaty_discount  = 0.50 if has_treaty else 0.0
    effective_withholding = base_withholding * (1 - treaty_discount)

    # Service-type specific rates
    if service_type == "care":
        service_rate     = dst["service_tax"]
        care_deduction   = dst["silver_care_deduction"]
        net_service_rate = max(0, service_rate - (service_rate * care_deduction))
    elif service_type == "remittance":
        net_service_rate = dst["remittance_tax"]
        care_deduction   = 0
    else:
        net_service_rate = dst["service_tax"]
        care_deduction   = 0

    # T_global = withholding + service tax (combined effective)
    t_global = effective_withholding + net_service_rate

    # Monetary amounts
    tax_amount        = amount * t_global
    net_amount        = amount - tax_amount
    vat_amount        = amount * dst["vat"] if service_type in {"care","general"} else 0

    return {
        "from_country":       from_country,
        "to_country":         to_country,
        "from_name":          src["name"],
        "to_name":            dst["name"],
        "service_type":       service_type,
        "amount_usd":         amount,
        "tax_breakdown": {
            "base_withholding_pct":    round(base_withholding * 100, 2),
            "treaty_discount_applied": has_treaty,
            "effective_withholding_pct": round(effective_withholding * 100, 2),
            "service_tax_pct":         round(net_service_rate * 100, 2),
            "silver_care_deduction_pct": round(care_deduction * 100, 2) if service_type == "care" else 0,
            "vat_pct":                 round(dst["vat"] * 100, 2)
        },
        "t_global":           round(t_global, 4),
        "t_global_pct":       round(t_global * 100, 2),
        "tax_amount_usd":     round(tax_amount, 2),
        "vat_amount_usd":     round(vat_amount, 2),
        "net_amount_usd":     round(net_amount, 2),
        "compliance_notes":   f"{'Tax treaty discount applied (50% WHT reduction).' if has_treaty else 'No tax treaty – standard withholding rates apply.'} Silver Care deduction: {round(care_deduction*100)}%." if service_type == "care" else ("Treaty discount applied." if has_treaty else "Standard rate corridor.")
    }
