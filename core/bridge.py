"""
Core Bridge Rate Logic – CBDC ↔ Crypto settlement index computation.
Stateless: all values derived from internal dataset + deterministic formulas.
"""
import json
import math
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "bridge_params.json"

def _load_params() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_bridge_rate(base_currency: str, target_crypto: str, amount: float) -> dict:
    """
    Calculate CBDC ↔ Crypto bridge rate and efficiency index.
    Returns V_base (bridge rate) + bridge efficiency metrics.
    """
    params = _load_params()

    base_currency = base_currency.upper()
    target_crypto  = target_crypto.upper()

    if base_currency not in params["cbdc_pairs"]:
        raise ValueError(f"Unsupported CBDC: {base_currency}. Available: {list(params['cbdc_pairs'].keys())}")
    if target_crypto not in params["cryptos"]:
        raise ValueError(f"Unsupported crypto: {target_crypto}. Available: {list(params['cryptos'].keys())}")

    cbdc   = params["cbdc_pairs"][base_currency]
    crypto = params["cryptos"][target_crypto]
    swift  = params["swift_baseline"]

    # V_base: units of crypto per 1 CBDC unit (using simulated price)
    v_base = 1.0 / crypto["simulated_price_usd"]

    # Bridge Efficiency with minor volatility penalty
    volatility   = crypto["volatility_30d"]
    risk_adj     = 1 + (volatility * 0.05)
    b_eff        = crypto["bridge_efficiency"] / risk_adj

    # Cost comparison
    crypto_fee_total = amount * (crypto["avg_fee_per_1000_usd"] / 1000)
    swift_fee_total  = amount * (swift["avg_fee_per_1000_usd"] / 1000)
    savings          = swift_fee_total - crypto_fee_total
    savings_pct      = (savings / swift_fee_total) * 100 if swift_fee_total > 0 else 0

    # Settlement Speed
    speed_multiplier = crypto["swift_speed_multiplier"]

    return {
        "base_currency":      base_currency,
        "target_crypto":      target_crypto,
        "cbdc_name":          cbdc["name"],
        "crypto_name":        crypto["name"],
        "v_base":             round(v_base, 8),
        "bridge_efficiency":  round(b_eff, 4),
        "simulated_price_usd": crypto["simulated_price_usd"],
        "volatility_30d":     volatility,
        "amount_usd":         amount,
        "fee_comparison": {
            "swift_fee_usd":        round(swift_fee_total, 2),
            "bridge_fee_usd":       round(crypto_fee_total, 2),
            "savings_usd":          round(savings, 2),
            "savings_pct":          round(savings_pct, 1),
            "human_readable":       f"Per ${amount:,.0f} transferred: save ${savings:.2f} vs SWIFT"
        },
        "settlement_speed": {
            "crypto_seconds":       crypto["avg_settlement_seconds"],
            "swift_hours":          swift["avg_settlement_hours"],
            "speed_multiplier":     f"{speed_multiplier:,}x faster than SWIFT"
        },
        "esg_carbon": {
            "crypto_co2_g_per_1000": crypto["carbon_g_co2_per_1000_usd"],
            "swift_co2_g_per_1000":  swift["carbon_g_co2_per_1000_usd"],
            "carbon_reduction_pct":  crypto["carbon_reduction_pct"]
        },
        "regulatory_status":  crypto["regulatory_status"],
        "cbdc_supported":     base_currency in crypto.get("supported_cbdc_corridors", [])
    }
