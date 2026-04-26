"""
Omni-Settlement Index Suite – Global Standard Settlement & Care-Tax API
"The Final Mile for Cross-Border Silver Economy Payments."

FastAPI main application – Vercel serverless entry point.
4 core endpoints: /bridge/rate, /tax/calculate, /care/valuation, /total/settlement
"""
import sys
import os

_HERE = os.path.dirname(os.path.abspath(__file__))   # …/api/
_ROOT = os.path.dirname(_HERE)                        # …/ (project root)
sys.path.insert(0, _ROOT)

from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal
from pathlib import Path
import time

from core.bridge     import get_bridge_rate
from core.tax        import calculate_tax
from core.care       import get_care_valuation
from core.settlement import calculate_ssi

# ─── App Initialization ─────────────────────────────────────────────────────

app = FastAPI(
    title       = "Omni-Settlement Index Suite",
    description = """
## Global Standard Settlement & Care-Tax API

**"The Final Mile for Cross-Border Silver Economy Payments."**

A stateless, zero-infrastructure B2B API that bridges **CBDC** (Central Bank Digital Currencies)
with **decentralized crypto rails** (XRP, ETH, USDC) — optimized for the **Silver Economy**:
cross-border elder care payments, remittances, and regulatory tax compliance.

### Core Settlement Formula
```
S_rate = (V_base × I_care) × (1 + T_global) × B_eff
```

| Symbol | Description |
|---|---|
| `V_base` | CBDC ↔ Crypto bridge exchange index |
| `I_care` | Care-Gap Index (country care service weight) |
| `T_global` | Global Tax Index (withholding + service tax) |
| `B_eff` | Bridge Efficiency vs SWIFT baseline |

### Pricing Tiers
- **Basic** (Free): 100 calls/month – `/bridge/rate`, `/care/valuation`
- **Pro** ($29/mo): 5,000 calls/month – + `/tax/calculate` + volatility scores
- **Ultra** ($99/mo): 50,000 calls/month – All endpoints + `/total/settlement` + ESG carbon data

### ESG Compliance
Every response includes **Carbon-Footprint per Transaction** vs SWIFT baseline,
enabling European and North American ESG-compliant payment platforms.
""",
    version     = "1.0.0",
    contact     = {
        "name":  "Omni-Settlement Index Suite",
        "url":   "https://omni-settlement.vercel.app",
        "email": "api@omni-settlement.io"
    },
    license_info = {"name": "Proprietary – Commercial Use via RapidAPI"},
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ─── Static files (landing page) ────────────────────────────────────────────
# Vercel environment: files are bundled relative to the root
_POSSIBLE_PUBLIC_DIRS = [
    Path(os.path.join(_ROOT, "public")),
    Path(os.getcwd()) / "public",
    Path("/var/task/public")
]

PUBLIC_DIR = _POSSIBLE_PUBLIC_DIRS[0]
for d in _POSSIBLE_PUBLIC_DIRS:
    if d.exists():
        PUBLIC_DIR = d
        break

if PUBLIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")

# ─── Pydantic Models ─────────────────────────────────────────────────────────

class SettlementRequest(BaseModel):
    origin_cbdc:   str   = Field("USD",  description="CBDC currency code (USD/EUR/KRW/JPY/CNY/SGD/AED/GBP/AUD/CAD)", example="USD")
    dest_country:  str   = Field("PH",   description="Destination ISO 3166-1 alpha-2 country code", example="PH")
    amount:        float = Field(5000.0, description="Transaction amount in USD", ge=1.0, le=10_000_000, example=5000)
    target_crypto: str   = Field("XRP",  description="Target crypto bridge asset (XRP/ETH/USDC/BTC)", example="XRP")
    service_type:  str   = Field("care", description="Service type: care | remittance | general", example="care")

# ─── Helper ──────────────────────────────────────────────────────────────────

def _wrap(data: dict, endpoint: str, elapsed_ms: float) -> dict:
    return {
        "status":       "success",
        "api":          "Omni-Settlement Index Suite v1.0",
        "endpoint":     endpoint,
        "elapsed_ms":   round(elapsed_ms, 2),
        "data":         data
    }

def _error(code: int, msg: str):
    raise HTTPException(status_code=code, detail={"status": "error", "message": msg})

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing_page():
    html_path = PUBLIC_DIR / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return HTMLResponse("<h1>Omni-Settlement Index Suite API – Visit /docs</h1>")


@app.get("/health", tags=["System"], summary="API Health Check")
async def health():
    return {
        "status":  "operational",
        "api":     "Omni-Settlement Index Suite",
        "version": "1.0.0",
        "uptime":  "serverless"
    }


@app.get(
    "/bridge/rate",
    tags=["Bridge Rate"],
    summary="CBDC ↔ Crypto Real-Time Settlement Index",
    description="""
Returns the **V_base** bridge exchange index between a CBDC and a target cryptocurrency,
including Bridge Efficiency score, fee comparison vs SWIFT, settlement speed, and ESG carbon data.

**Tier Required**: Basic (Free)

### Key Output Fields
- `v_base` – Units of crypto per 1 USD equivalent
- `bridge_efficiency` – B_eff score (risk-adjusted)
- `fee_comparison.savings_usd` – Dollar savings vs SWIFT per transaction
- `esg_carbon.carbon_reduction_pct` – CO₂ reduction vs SWIFT
""",
    response_description="Bridge rate and efficiency metrics"
)
async def bridge_rate(
    base_currency: str = Query("USD",  description="CBDC currency code", example="USD"),
    target_crypto: str = Query("XRP",  description="Target crypto ticker (XRP/ETH/USDC/BTC)", example="XRP"),
    amount:       float = Query(1000.0, description="Transaction amount in USD", ge=1.0, le=10_000_000, example=1000)
):
    t0 = time.perf_counter()
    try:
        data = get_bridge_rate(base_currency, target_crypto, amount)
    except ValueError as e:
        _error(400, str(e))
    return _wrap(data, "/bridge/rate", (time.perf_counter() - t0) * 1000)


@app.get(
    "/tax/calculate",
    tags=["Global Tax Index"],
    summary="Cross-Border Service Tax & Withholding Rate",
    description="""
Returns the **T_global** effective tax rate for a cross-border payment corridor,
including withholding tax, service tax, VAT, treaty discounts, and silver care deductions.

**Tier Required**: Pro ($29/mo)

### Key Output Fields
- `t_global` – Combined effective tax rate (decimal)
- `tax_breakdown` – Component-level breakdown (withholding, service tax, VAT)
- `tax_amount_usd` – Exact tax liability in USD
- `compliance_notes` – Regulatory guidance text
""",
    response_description="Cross-border tax calculation result"
)
async def tax_calculate(
    from_country: str  = Query("US",          description="Origin country ISO 3166-1 alpha-2 code", example="US"),
    to_country:   str  = Query("PH",          description="Destination country ISO code", example="PH"),
    amount:      float = Query(5000.0,         description="Payment amount in USD", ge=1.0, example=5000),
    service_type: str  = Query("care",         description="Service type: care | remittance | general", example="care")
):
    t0 = time.perf_counter()
    try:
        data = calculate_tax(from_country, to_country, amount, service_type)
    except ValueError as e:
        _error(400, str(e))
    return _wrap(data, "/tax/calculate", (time.perf_counter() - t0) * 1000)


@app.get(
    "/care/valuation",
    tags=["Care-Gap Index"],
    summary="Silver Care Service Standard Value (Care-Gap Index)",
    description="""
Returns the **I_care** Care-Gap Index for a destination country, including absolute care cost
projections, gap vs. US baseline, arbitrage score, and optimal payment recommendations.

**Tier Required**: Basic (Free)

### Key Output Fields
- `i_care` – Care-Gap Index multiplier (0.0–1.0+)
- `cost_projection` – Weekly/monthly/annual care costs
- `gap_vs_us_baseline.monthly_savings_vs_us` – USD savings vs hiring in the US
- `arbitrage_score` – Composite arbitrage opportunity score
- `care_arbitrage_insights` – Best-practice payment corridor hints
""",
    response_description="Care-Gap valuation result"
)
async def care_valuation(
    region:          str   = Query("PH",    description="Country ISO code for care service region", example="PH"),
    service_type:    str   = Query("visit", description="Service type: visit | residential | remote", example="visit"),
    hours_per_week: float  = Query(40.0,    description="Weekly care hours (default 40 = full-time)", ge=1.0, le=168.0, example=40)
):
    t0 = time.perf_counter()
    try:
        data = get_care_valuation(region, service_type, hours_per_week)
    except ValueError as e:
        _error(400, str(e))
    return _wrap(data, "/care/valuation", (time.perf_counter() - t0) * 1000)


@app.post(
    "/total/settlement",
    tags=["Total Settlement (SSI)"],
    summary="⭐ Killer Feature: Full Standard Settlement Rate Calculation",
    description="""
**The Omni-Settlement Index Suite's flagship endpoint.**

Applies the complete SSI formula to produce the final Standard Settlement Rate (S_rate),
integrating all three indices in a single response:

```
S_rate = (V_base × I_care) × (1 + T_global) × B_eff
```

**Tier Required**: Ultra ($99/mo)

### Output Highlights
- `s_rate` – The final composite settlement rate
- `settlement_summary` – Exact crypto amount received + care coverage months
- `cost_efficiency` – SWIFT savings + bridge fee breakdown
- `esg.carbon_saved_g` – Carbon footprint reduction (grams CO₂)
- `compliance` – Tax treaty status + regulatory notes
- `care_arbitrage` – Optimal payment corridor recommendations

### Example Use Case
A US senior care agency sends $5,000 to hire a Philippine care worker via XRP.
This endpoint returns the exact crypto amount received, taxes deducted, months of care covered,
and how much was saved vs wiring through SWIFT.
""",
    response_description="Full SSI settlement rate and breakdown"
)
async def total_settlement(body: SettlementRequest):
    t0 = time.perf_counter()
    try:
        data = calculate_ssi(
            body.origin_cbdc,
            body.dest_country,
            body.amount,
            body.target_crypto,
            body.service_type
        )
    except ValueError as e:
        _error(400, str(e))
    return _wrap(data, "/total/settlement", (time.perf_counter() - t0) * 1000)
