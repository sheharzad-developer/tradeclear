# TradeClear — Vision vs. MVP (alignment one-pager)

**Positioning:** An AI decision engine for trade compliance — a *system of record + duty-optimization layer* for importers. Not a chatbot. Legacy trade software (SAP GTS, Descartes, ONESOURCE, e2open) is rules-based and manual; the work is document- and text-heavy, which is exactly where AI wins.

---

## North Star (where this goes — the vision)

> Continuously monitor every product an importer brings in, keep classifications correct as tariffs change, automatically surface duty leakage and FTA savings, and produce audit-ready justification on demand — embedded in their ERP and compliance workflow.

That's the 3-year picture. **We do not build it first. We earn our way to it.**

---

## The wedge (what we build first — ONE thing)

**Classification + Duty + FTA second-opinion.**
Importer uploads a product list → gets, per item: suggested HS code(s) with cited reasoning + confidence, US/Canada duty estimate, FTA (USMCA) flag, and a "this code looks off vs. your current one" alert.

> Framed as decision-support for a licensed customs broker to review. The importer of record stays responsible. Cited reasoning = credibility *and* liability shield.

**Status: already built and running** (FastAPI + Streamlit demo, mock AI engine, ~95-line HS dataset). This is real, not a slide.

---

## The cut line (draw it and hold it)

| In the MVP (now) | Deferred — Phase 2 | Deferred — Phase 3 (vision) |
|---|---|---|
| HS classification + confidence + cited reasoning | **Duty leakage finder** (retrospective: "you're leaking $X/yr" from past entries) | Sanctions / restricted-party screening |
| US + Canada duty estimate | Tariff-change monitoring → product impact | Audit-packet generator |
| FTA (USMCA) flag | Real LLM over full HTS + grounded retrieval | ERP integrations (SAP / NetSuite) |
| Current-vs-suggested mismatch alert | | Trade-scenario simulation ("what if +10%?") |

**Everything in the right two columns is the vision doc, not the MVP.** Sanctions, audit packets, and ERP each have different data sources, buyers, and liability — bundling them now kills focus.

---

## The one sequencing decision (and why)

The strongest *headline* is duty leakage ("you overpaid $X"). The safest *first build* is the forward-looking second-opinion. Same destination — different on-ramp:

- **Leakage** needs historical entry data (CBP 7501 / ACE) and makes authoritative claims about the past → higher trust barrier + higher liability. Risky while we have **no in-house customs expert**.
- **Second-opinion** gets ~80% of the punch ("your current code looks off here"), is forward-looking and lower-liability, and **earns the data access + trust** to do leakage next.

➡️ Ship the second-opinion → use it to unlock the leakage finder.

---

## Who we validate with (ICP)

SMB / mid-market importers into the US & Canada who self-file or feel under-served by their broker. **Pick by access first, then duty pain.** Lock ONE vertical for the first 2–3 conversations (apparel, electronics, or kitchenware all work with our current dataset).

---

## 2-week validation plan

**Week 0 (this week):**
- [ ] Lock a fractional licensed customs broker (advisor) — validates rates, gives domain credibility.
- [ ] Choose the first vertical (by where we can get a meeting).
- [ ] Build the target list: 15–20 importers.

**Week 1:**
- [ ] Validate the duty rates for that vertical's demo SKUs with the broker.
- [ ] Produce 2–3 polished sample reports from public catalogs.
- [ ] Send the free-analysis offer (email + LinkedIn) to the list.

**Week 2:**
- [ ] Run the free analysis on 1–2 importers' real SKUs (20–50 each).
- [ ] Deliver reports; hold 15-min discovery calls.
- [ ] Score the signal → go / no-go.

---

## Go / no-go (decide on behavior, not compliments)

**Validated** = 1–2 importers who: share real SKUs without much friction · forward the report to their broker · ask "can you do all our products / our past entries?" · ask about price.

**That green light** = invest in real LLM + full-HTS retrieval and the Phase-2 duty-leakage finder. Until then, we do **not** build more — we sell what we have.

---

## Founder alignment check (for the two of us)

- We agree the **vision** is the system-of-record/decision-engine above. ✅
- We agree the **MVP is one thing**: classification + duty + FTA second-opinion. ◻️
- We agree to **sequence second-opinion → leakage**, not leakage-first. ◻️
- We agree to **not build** sanctions / audit-packet / ERP until post-validation. ◻️
- We agree the next action is **validation with 2–3 companies**, not more features. ◻️
