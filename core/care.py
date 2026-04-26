"""
Care-Gap Index Logic – silver economy care service valuation.
Stateless computation from care_index.json dataset.
"""
import json
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "care_index.json"

SERVICE_TYPES = {"visit", "residential", "remote"}

def _load_index() -> dict:
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_care_valuation(
    region:       str,
    service_type: str = "visit",
    hours_per_week: float = 40.0
) -> dict:
    """
    Compute I_care: the Care-Gap Index multiplier and absolute cost valuation
    for silver economy care services in a given country.
    """
    index_data   = _load_index()
    region       = region.upper()
    service_type = service_type.lower()

    regions = index_data["regions"]

    if region not in regions:
        raise ValueError(f"Unsupported region: {region}. Available: {list(regions.keys())}")
    if service_type not in SERVICE_TYPES:
        raise ValueError(f"service_type must be one of: {SERVICE_TYPES}")

    r = regions[region]

    # I_care: composite index for this service type
    i_care      = r["service_types"][service_type]
    base_hourly = r["avg_hourly_usd"]

    # Cost projection
    weekly_cost_usd  = base_hourly * hours_per_week
    monthly_cost_usd = weekly_cost_usd * 4.33  # avg weeks per month

    # Gap vs US baseline (1.00)
    us_hourly    = 28.50
    gap_vs_us    = (us_hourly - base_hourly) / us_hourly
    arbitrage_score = round(gap_vs_us * r["care_worker_shortage_pct"] / 100, 4)

    # Find best arbitrage pair
    arb_insights = []
    for pair in index_data["arbitrage_insights"]["top_cost_efficient_pairs"]:
        if pair["to"] == region or pair["from"] == region:
            arb_insights.append(pair)

    return {
        "region":             region,
        "region_name":        r["name"],
        "service_type":       service_type,
        "i_care":             round(i_care, 4),
        "care_worker_data": {
            "shortage_pct":           r["care_worker_shortage_pct"],
            "avg_hourly_usd":         base_hourly,
            "population_65plus_pct":  r["resident_population_65plus_pct"]
        },
        "cost_projection": {
            "hours_per_week":         hours_per_week,
            "weekly_cost_usd":        round(weekly_cost_usd, 2),
            "monthly_cost_usd":       round(monthly_cost_usd, 2),
            "annual_cost_usd":        round(monthly_cost_usd * 12, 2)
        },
        "gap_vs_us_baseline": {
            "us_hourly_rate_usd":     us_hourly,
            "local_hourly_usd":       base_hourly,
            "cost_gap_pct":           round(gap_vs_us * 100, 1),
            "monthly_savings_vs_us":  round((us_hourly - base_hourly) * hours_per_week * 4.33, 2)
        },
        "arbitrage_score":    arbitrage_score,
        "care_arbitrage_insights": arb_insights if arb_insights else None,
        "residential_daily_usd": r["residential_daily_usd"] if service_type == "residential" else None
    }
