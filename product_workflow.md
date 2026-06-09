# TradeClear — Product Workflow (the non-AI core)

**What this doc is for:** align the team on what the product *does as a business* — the
workflow, inputs, and outputs — independent of any AI. "Intelligence" is an enhancement
added later; the value below stands on its own.

> **One-sentence definition:** TradeClear is a simple workspace where importers look up
> the right HS code, instantly see their US & Canada duties, catch costly classification
> mistakes, and keep an audit-ready record — replacing the spreadsheets and guesswork
> they rely on today.

---

## 1. Who it's for

**Primary user — "Maria", Import/Operations Manager** at a small-to-mid importer
($2M–$50M revenue, 50–2,000 SKUs) bringing goods into the US and/or Canada. Not a
customs expert; runs compliance on **spreadsheets, email, her broker, and memory.**

**Secondary (later):** the customs broker — channel partner / reviewer, not the v1 buyer.

## 2. How she works today (manual)

Copies last year's HS code or asks the broker → broker files → duty paid (often unseen
until after landing) → product/code data scattered across spreadsheets → scrambles to
reconstruct "what code and why" at reorder or audit. Reactive, undocumented,
broker-dependent.

## 3. Where she loses money & time

- Overpays duty from lazy/wrong classifications (invisible until it adds up)
- Underpays → penalty + audit risk she doesn't know she carries
- No landed-cost visibility **before** committing to a purchase order
- Misses FTA (USMCA) savings she's eligible for
- Inconsistent codes across SKUs / over time → audit red flag
- No single source of truth; broker is a black box

## 4. The product workflow (step-by-step)

A structured trade catalog + duty calculator — not a spreadsheet.

| Step | What she does | What she gets |
|---|---|---|
| 1 · Add products | Upload a spreadsheet or fill a form | Products in one place |
| 2 · Find HS code | Guided lookup in a built-in HS reference (search/filter) | Right code + official description |
| 3 · See duty | Pick destination (US / Canada) | Duty rate + estimated duty / landed cost |
| 4 · Check flags | Review rule-based alerts | Missing data, code mismatch, FTA opportunity, high-duty flag |
| 5 · Save to catalog | Store product + code + duty + reasoning | Reusable **system of record** |
| 6 · Export report | One click | Clean PDF/CSV for broker review & audit |

**Inputs:** product description, material, country of origin, shipment value, current HS
code (optional).
**Outputs:** HS code + description, US/CA duty + estimated cost, FTA flag, issue flags,
exportable report.

## 5. MVP v1 — what we build first

1. **Product catalog** (spreadsheet upload + form)
2. **Guided HS code lookup** (structured US/Canada reference)
3. **Duty estimator** (US + Canada rate + estimated duty / landed cost)
4. **Basic issue flags** (missing data · code mismatch · FTA opportunity · high duty) — simple rules
5. **Exportable report** (broker-ready, audit-ready)

Replaces her spreadsheets, gives duty visibility she's never had, becomes her source of truth.

## 6. NOT in v1 (later, on purpose)

❌ Any system that classifies *for* her (v1 = guided lookup; she stays in control) ·
❌ Sanctions / denied-party screening · ❌ Automated audit-packet generation ·
❌ ERP / accounting integrations · ❌ Live tariff-change monitoring ·
❌ Automated customs filing · ❌ Countries beyond US + Canada ·
❌ Multi-user roles / approval workflows

## 7. The business in one line

This is **not an AI product — it's a system of record + duty calculator** that gives
importers visibility and control they've never had. AI later just makes the lookup
faster; the value doesn't depend on it.

---

### Team alignment check
- We agree the **core value is workflow + visibility**, not intelligence. ◻️
- We agree v1 = **catalog + HS lookup + duty + flags + report**. ◻️
- We agree the user stays **in control** (guided lookup, not auto-classification). ◻️
- We agree everything in §6 is **deferred**. ◻️
- We agree the next step is **validating this workflow with 2–3 importers**. ◻️
