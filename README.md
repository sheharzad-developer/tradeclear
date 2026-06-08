# TradeClear — AI Trade Compliance Copilot (MVP)

An AI decision-support tool for importers: upload a product list → get **HS code
classification** (with cited reasoning + confidence), **US & Canada duty estimates**,
**FTA (USMCA) flags**, and **"this code looks off vs. your current one"** alerts.

> Decision-support for licensed customs-broker review — not a customs ruling or legal
> advice. The importer of record remains responsible for the final classification.
> Duty rates in the demo dataset are **illustrative**, not authoritative tariffs.

**Stage:** pre-customer validation. The AI is intentionally **mocked** (no API cost);
a real-LLM path is wired and gated behind one env var.

---

## Quickstart

```bash
# from the project/ folder
python3.12 -m venv ../.venv          # 3.12 recommended (ML libs lag on 3.14)
source ../.venv/bin/activate
pip install -r requirements.txt
```

**Streamlit demo (use this in front of prospects):**
```bash
streamlit run streamlit_app.py        # http://localhost:8501
```

**FastAPI service (the eventual product backend):**
```bash
uvicorn main:app --reload             # http://localhost:8000/docs
# /classify  /classify/batch  /upload (CSV)  /report (printable HTML → PDF)
```

Both share the **same engine**, so they never disagree.

---

## How it works (pipeline)

```
product → retrieve candidates → rank (mock AI / LLM) → estimate duty → report
          retriever.py          ranker.py             duty.py        report.py
```

- **retriever.py** — keyword candidate fetch over the local HS dataset (recall stage).
- **ranker.py** — the swappable "AI". Mock = deterministic keyword scoring. Real =
  LLM call (gated). Either way, output is **re-validated against the candidate set**
  so a hallucinated code can never reach the report.
- **duty.py** — US/CA duty lookup + USMCA flag + amount calc.
- **report.py** — assembles per-SKU JSON + a styled printable HTML report.
- **hs_data.py** — ~95 HS lines across 24 chapters (apparel, electronics, kitchenware,
  furniture, etc.) with keywords + illustrative US/CA rates + FTA.

## Turning on the real LLM (later)

```bash
cp .env.example .env
# set USE_LLM=true and OPENAI_API_KEY=sk-...
```
No other code changes — retriever, duty, and report stay as-is. Prompt lives in
`prompt.py`.

---

## Files

| File | Role |
|---|---|
| `streamlit_app.py` | SaaS demo UI (upload → results → insights → export) |
| `main.py` | FastAPI service |
| `retriever.py` `ranker.py` `duty.py` `report.py` `hs_data.py` `text_utils.py` | shared engine |
| `prompt.py` | LLM system prompt (for the real-AI swap) |
| `sample_products.csv` | test data (incl. mismatch + low-confidence cases) |
| `outreach_kit.md` | pitch, free-analysis offer, email/LinkedIn scripts, discovery guide |
| `vision_vs_mvp.md` | vision-vs-MVP alignment one-pager (founder checklist) |

## What's deliberately NOT built (yet)

Duty-leakage finder (Phase 2), sanctions screening, audit-packet generator, ERP
integrations, tariff-change monitoring. See `vision_vs_mvp.md` for the cut line and
the 2-week validation plan.
