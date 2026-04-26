"""
Standard Settlement Index (SSI) – Omni-Settlement combinator.
Applies the core formula: S_rate = (V_base × I_care) × (1 + T_global) × B_eff

This is the 'killer endpoint' – merges Bridge, Tax, and Care-Gap into one call.
"""
from core.bridge import get_bridge_rate
from core.tax    import calculate_tax
from core.care   import get_care_valuation

def calculate_ssi(
    origin_cbdc:  str,
    dest_country: str,
    amount:       float,
    target_crypto: str = "XRP",
    service_type: str = "care"
) -> dict:
    """
    Compute the final Standard Settlement Rate (S_rate) using the SSI formula.
    Combines V_base, I_care, T_global, and B_eff.
    """
    # Map high-level service_type to care-gap specific sub-types if needed
    mapped_care_type = service_type
    if service_type == "care":
        mapped_care_type = "visit"  # Default fallback
    elif service_type not in ["visit", "residential", "remote"]:
        # If it's not a care type at all (remittance/general), 
        # use visit as indexing baseline for I_care component
        mapped_care_type = "visit"

    # --- Component 1: Bridge Rate (V_base, B_eff) ---
    bridge  = get_bridge_rate(origin_cbdc, target_crypto, amount)
    v_base  = bridge["v_base"]
    b_eff   = bridge["bridge_efficiency"]

    # --- Component 2: Care-Gap Index (I_care) ---
    care    = get_care_valuation(dest_country, mapped_care_type)
    i_care  = care["i_care"]

    # --- Component 3: Global Tax Index (T_global) ---
    # Detect origin country from CBDC (simplified mapping)
    cbdc_to_country = {
        "USD": "US", "EUR": "DE", "KRW": "KR", "JPY": "JP",
        "CNY": "CN", "SGD": "SG", "AED": "AE", "GBP": "GB",
        "AUD": "AU", "CAD": "CA"
    }
    from_country = cbdc_to_country.get(origin_cbdc.upper(), "US")
    tax         = calculate_tax(from_country, dest_country, amount, service_type)
    t_global    = tax["t_global"]

    # --- SSI Formula ---
    # S_rate = (V_base × I_care) × (1 + T_global) × B_eff
    s_rate = (v_base * i_care) * (1 + t_global) * b_eff

    # Compute final settlement amounts
    gross_amount   = amount
    tax_deducted   = amount * t_global
    net_after_tax  = gross_amount - tax_deducted

    # Crypto amount received by recipient
    crypto_amount  = net_after_tax * v_base * b_eff

    # Cost efficiency vs SWIFT
    swift_total_cost = amount * (42.50 / 1000)   # SWIFT baseline fee
    bridge_fee       = bridge["fee_comparison"]["bridge_fee_usd"]
    total_savings    = swift_total_cost - bridge_fee

    return {
        "meta": {
            "formula": "S_rate = (V_base × I_care) × (1 + T_global) × B_eff",
            "origin_cbdc":    origin_cbdc.upper(),
            "dest_country":   dest_country.upper(),
            "target_crypto":  target_crypto.upper(),
            "service_type":   service_type,
            "amount_usd":     amount
        },
        "components": {
            "v_base":   round(v_base, 8),
            "i_care":   round(i_care, 4),
            "t_global": round(t_global, 4),
            "b_eff":    round(b_eff, 4)
        },
        "s_rate": round(s_rate, 8),
        "settlement_summary": {
            "gross_amount_usd":      round(gross_amount, 2),
            "tax_deducted_usd":      round(tax_deducted, 2),
            "net_after_tax_usd":     round(net_after_tax, 2),
            "crypto_received":       round(crypto_amount, 6),
            "crypto_ticker":         target_crypto.upper(),
            "care_monthly_coverage_months": round(net_after_tax / care["cost_projection"]["monthly_cost_usd"], 1) if care["cost_projection"]["monthly_cost_usd"] > 0 else 0
        },
        "cost_efficiency": {
            "swift_fee_usd":         round(swift_total_cost, 2),
            "bridge_fee_usd":        round(bridge_fee, 2),
            "total_savings_usd":     round(total_savings, 2),
            "savings_pct":           round((total_savings / swift_total_cost) * 100, 1) if swift_total_cost > 0 else 0,
            "settlement_speed":      bridge["settlement_speed"]["speed_multiplier"]
        },
        "esg": {
            "carbon_reduction_pct":  bridge["esg_carbon"]["carbon_reduction_pct"],
            "crypto_co2_g":          bridge["esg_carbon"]["crypto_co2_g_per_1000"],
            "swift_co2_g":           bridge["esg_carbon"]["swift_co2_g_per_1000"],
            "carbon_saved_g":        round((bridge["esg_carbon"]["swift_co2_g_per_1000"] - bridge["esg_carbon"]["crypto_co2_g_per_1000"]) * (amount / 1000), 1)
        },
        "compliance": {
            "tax_treaty_applied":    tax["tax_breakdown"]["treaty_discount_applied"],
            "regulatory_status":     bridge["regulatory_status"],
            "compliance_note":       tax["compliance_notes"]
        },
        "care_arbitrage":            care.get("care_arbitrage_insights")
    }
