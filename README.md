# Omni-Settlement Index Suite
## Global Standard Settlement & Care-Tax API

> **"The Final Mile for Cross-Border Silver Economy Payments."**

A stateless, zero-infrastructure B2B API bridging **CBDC** (Central Bank Digital Currencies) with decentralized crypto rails (XRP, ETH, USDC) — optimized for the **Silver Economy**.

---

## Core Settlement Formula

```
S_rate = (V_base × I_care) × (1 + T_global) × B_eff
```

| Symbol | Description |
|---|---|
| `V_base` | CBDC ↔ Crypto bridge exchange index |
| `I_care` | Care-Gap Index (country care service weight) |
| `T_global` | Global Tax Index (withholding + service tax) |
| `B_eff` | Bridge Efficiency vs SWIFT baseline |

---

## 4 API Endpoints

| Endpoint | Method | Tier | Description |
|---|---|---|---|
| `/bridge/rate` | GET | Free | CBDC ↔ XRP/ETH real-time settlement index |
| `/tax/calculate` | GET | Pro | Cross-border withholding & service tax |
| `/care/valuation` | GET | Free | Care-Gap Index service valuation |
| `/total/settlement` | POST | Ultra | **Killer feature** – Full SSI formula output |

---

## Quick Start

```bash
pip install -r requirements.txt
uvicorn api.index:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs
```

---

## Tech Stack

- **Runtime**: Python 3.11 + FastAPI + Uvicorn
- **Deploy**: Vercel Serverless (Zero cost)
- **Docs**: Swagger UI at `/docs` + OpenAPI 3.0 spec
- **Data**: Stateless JSON datasets (no database)

---

## Pricing

| Tier | Calls/Month | Price |
|---|---|---|
| Basic | 100 | Free |
| Pro | 5,000 | $29/mo |
| Ultra | 50,000 | $99/mo |

---

## Available on RapidAPI

[Subscribe on RapidAPI →](https://rapidapi.com)

---

## License

Proprietary – Commercial use via RapidAPI marketplace.
