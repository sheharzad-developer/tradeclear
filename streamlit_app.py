"""
AI Trade Compliance Copilot — Streamlit demo UI.

Reuses the SAME mock engine as the FastAPI app (report.build_report), so the
classification logic never drifts between the two. Runs fully offline.

Run:  streamlit run streamlit_app.py
"""
import time
import io

import pandas as pd
import streamlit as st

from report import build_report
from hs_data import HS_DATA

# --------------------------------------------------------------------------- #
# Page config + global styling
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="TradeClear — AI Trade Compliance Copilot",
    page_icon="🛳️",
    layout="wide",
)

try:
    st.logo("assets/logo.svg", size="large")
except Exception:
    pass

st.markdown("""
<style>
  .block-container { padding-top: 2rem; max-width: 1200px; }
  /* Header */
  .hero { background: linear-gradient(110deg,#0f2d52 0%,#13477f 60%,#1565c0 100%);
          color:#fff; padding:26px 32px; border-radius:14px; margin-bottom:22px; }
  .hero h1 { margin:0; font-size:28px; font-weight:800; letter-spacing:-.01em; }
  .hero p  { margin:6px 0 0; font-size:15px; opacity:.9; }
  .hero .pill { display:inline-block; background:rgba(255,255,255,.16);
                padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600;
                margin-top:12px; }
  /* KPI cards */
  div[data-testid="stMetric"] { background:#f7f9fc; border:1px solid #e6ebf2;
        border-radius:12px; padding:14px 18px; }
  div[data-testid="stMetricValue"] { font-size:26px; font-weight:800; }
  /* Insight rows */
  .insight { border-left:4px solid #ccc; padding:10px 14px; border-radius:6px;
             margin-bottom:10px; font-size:14px; background:#fafbfd; }
  .insight.red   { border-color:#c0392b; background:#fdf0ef; }
  .insight.amber { border-color:#b8860b; background:#fdf8ec; }
  .insight.green { border-color:#1a7f44; background:#eefaf2; }
  .insight.blue  { border-color:#1565c0; background:#eef4fd; }
  .footer { color:#8a93a3; font-size:12px; border-top:1px solid #e6ebf2;
            padding-top:14px; margin-top:30px; }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def rows_to_products(df):
    products = []
    for _, row in df.iterrows():
        def g(k):
            v = row.get(k)
            return None if pd.isna(v) or v == "" else v
        cv = g("customs_value")
        products.append({
            "sku": g("sku"),
            "description": g("description") or "",
            "material": g("material"),
            "origin": g("origin"),
            "customs_value": float(cv) if cv is not None else None,
            "current_hs_code": g("current_hs_code"),
        })
    return products


def fake_processing(n):
    """Staged 'AI is working' feedback (deterministic, no real API)."""
    stages = [
        ("📥 Parsing product catalog", 0.35),
        ("🔎 Retrieving HS code candidates", 0.5),
        ("🧠 Running AI classification engine", 0.7),
        ("💵 Estimating US & Canada duties", 0.45),
        ("🛡️ Scanning for compliance risks", 0.4),
    ]
    with st.status(f"Analyzing {n} product(s)…", expanded=True) as status:
        for label, delay in stages:
            st.write(label)
            time.sleep(delay)
        status.update(label="Analysis complete ✓", state="complete", expanded=False)


def build_insights(reports):
    n = len(reports)
    low = [r for r in reports if r["confidence"] == "low"]
    mism = [r for r in reports if r["code_status"] == "mismatch"]
    fta = [r for r in reports if "potentially" in r["duty_estimate"].get("fta_flag", "")]
    high_duty = [r for r in reports
                 if (r["duty_estimate"].get("us") or {}).get("rate_pct", 0) and
                 r["duty_estimate"]["us"]["rate_pct"] >= 15]

    items = []
    if mism:
        items.append(("red", f"⚠️ <b>{len(mism)} product(s)</b> have a suggested HS code that "
                             f"differs from the current code — potential mis-declaration / "
                             f"over- or under-payment. Review before next entry."))
    if low:
        items.append(("amber", f"🔍 <b>{len(low)} product(s)</b> could not be confidently "
                              f"classified and are flagged for customs-broker review."))
    if high_duty:
        items.append(("blue", f"💰 <b>{len(high_duty)} product(s)</b> sit in high-duty brackets "
                            f"(≥15%). Confirm classification and check for tariff-engineering "
                            f"or FTA opportunities."))
    if fta:
        items.append(("green", f"🌎 <b>{len(fta)} product(s)</b> are potentially FTA "
                            f"(USMCA/CUSMA) eligible — verify rules of origin to capture "
                            f"preferential duty."))
    if not items:
        items.append(("green", "✅ No major compliance risks detected in this batch."))
    return items, {"low": len(low), "mism": len(mism), "fta": len(fta)}


def reports_to_df(reports, country):
    rows = []
    for r in reports:
        us = r["duty_estimate"].get("us") or {}
        ca = r["duty_estimate"].get("ca") or {}
        status = ("Needs review" if r["needs_manual_review"]
                  else "Code mismatch" if r["code_status"] == "mismatch" else "OK")
        rows.append({
            "SKU": r["sku"] or "—",
            "Product": r["product_summary"],
            "Suggested HS": r["final_hs_code"] or "—",
            "Confidence": r["confidence"].capitalize(),
            "US Duty %": us.get("rate_pct"),
            "CA Duty %": ca.get("rate_pct"),
            "Status": status,
        })
    df = pd.DataFrame(rows)
    return df


def style_table(df):
    def conf_color(v):
        return {"High": "background-color:#e6f7ed;color:#1a7f44;font-weight:600",
                "Medium": "background-color:#fef6e0;color:#b8860b;font-weight:600",
                "Low": "background-color:#fdeaea;color:#c0392b;font-weight:600"}.get(v, "")

    def status_color(v):
        return {"OK": "color:#1a7f44;font-weight:600",
                "Code mismatch": "background-color:#fef6e0;color:#b8860b;font-weight:600",
                "Needs review": "background-color:#fdeaea;color:#c0392b;font-weight:600"}.get(v, "")

    return (df.style
            .map(conf_color, subset=["Confidence"])
            .map(status_color, subset=["Status"])
            .format({"US Duty %": "{:.1f}%", "CA Duty %": "{:.1f}%"}, na_rep="—"))


SAMPLE_CSV = """sku,description,material,origin,customs_value,current_hs_code
TS-001,Men's cotton t-shirt knitted,cotton,MX,5000,
TS-009,Men's polyester performance t-shirt knitted,polyester,CN,6000,6109.10.00.10
BP-002,Nylon travel backpack,nylon,CN,8000,4202.92.31.20
LP-003,14 inch laptop notebook computer,aluminum,CN,40000,
MUG-004,Ceramic stoneware coffee mug,ceramic,CN,1500,6911.10.10.00
CHR-005,USB power adapter wall charger,plastic,MX,3000,
SOFA-006,Upholstered armchair with wooden frame,wood,CA,12000,
WID-008,Mystery industrial gadget thingamajig,,CN,1000,
"""


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    country = st.selectbox("Import destination", ["United States", "Canada", "Both"])
    mode = st.radio("Engine mode", ["Demo (mock AI)", "Live API (coming soon)"],
                    index=0)
    if mode.startswith("Live"):
        st.info("Live LLM mode is wired but disabled in this demo build.")
    st.divider()
    st.caption(f"📚 Knowledge base: **{len(HS_DATA)} HS lines** loaded "
               "(US + Canada duty rates).")
    st.download_button("⬇️ Download sample CSV", SAMPLE_CSV,
                       file_name="sample_products.csv", mime="text/csv",
                       width="stretch")
    st.divider()
    st.caption("⚠️ Decision-support only. Not a customs ruling or legal advice. "
               "Importer of record remains responsible for final classification.")


# --------------------------------------------------------------------------- #
# Header
# --------------------------------------------------------------------------- #
st.markdown("""
<div class="hero">
  <h1>🛳️ TradeClear — AI Trade Compliance Copilot</h1>
  <p>Instant HS classification, US &amp; Canada duty estimates, and compliance
     risk insights for importers & exporters.</p>
  <span class="pill">● AI engine online · North America</span>
</div>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Upload + workflow
# --------------------------------------------------------------------------- #
st.subheader("1 · Upload your product catalog")
c1, c2 = st.columns([3, 1])
with c1:
    uploaded = st.file_uploader("CSV with columns: sku, description, material, "
                                "origin, customs_value, current_hs_code "
                                "(only *description* is required)", type=["csv"])
with c2:
    st.write("")
    st.write("")
    use_sample = st.button("✨ Try sample data", width="stretch")

df_in = None
if uploaded is not None:
    df_in = pd.read_csv(uploaded)
elif use_sample:
    df_in = pd.read_csv(io.StringIO(SAMPLE_CSV))

if df_in is None:
    st.info("⬆️ Upload a CSV or click **Try sample data** to see the copilot in action.")
    st.stop()

# ----- run the (mock) engine -----
products = rows_to_products(df_in)
fake_processing(len(products))
reports = [build_report(p) for p in products]
insights, counts = build_insights(reports)

# ----- KPI row -----
st.subheader("2 · Results overview")
total = len(reports)
us_exposure = sum((r["duty_estimate"].get("us") or {}).get("estimated_duty") or 0
                  for r in reports)
ca_exposure = sum((r["duty_estimate"].get("ca") or {}).get("estimated_duty") or 0
                  for r in reports)
exposure = ca_exposure if country == "Canada" else us_exposure

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Products analyzed", total)
k2.metric("Need review", counts["low"])
k3.metric("Code mismatches", counts["mism"])
k4.metric("Potential FTA savings", counts["fta"])
k5.metric(f"Est. duty ({'CA' if country=='Canada' else 'US'})",
          f"${exposure:,.0f}" if exposure else "—")

# ----- results table -----
df_out = reports_to_df(reports, country)
if country == "United States":
    df_out = df_out.drop(columns=["CA Duty %"])
elif country == "Canada":
    df_out = df_out.drop(columns=["US Duty %"])
st.dataframe(style_table(df_out), width="stretch", hide_index=True)

# ----- AI insights panel + details -----
left, right = st.columns([1, 1])
with left:
    st.subheader("3 · AI compliance insights")
    for sev, text in insights:
        st.markdown(f"<div class='insight {sev}'>{text}</div>", unsafe_allow_html=True)

with right:
    st.subheader("Per-product detail")
    for r in reports:
        icon = "🔴" if r["needs_manual_review"] else "🟡" if r["code_status"] == "mismatch" else "🟢"
        with st.expander(f"{icon} {r['sku']} — {r['product_summary']}"):
            if r["code_status"] == "mismatch":
                st.warning(f"Current code **{r['current_hs_code']}** differs from "
                           f"suggested **{r['final_hs_code']}** — confirm with broker.")
            st.markdown(f"**Suggested HS:** `{r['final_hs_code'] or 'n/a'}`  "
                        f"· confidence: **{r['confidence']}**")
            for c in r["hs_candidates"]:
                st.markdown(f"- `{c['code']}` ({c['confidence']}) — {c['reason']}")
            st.caption(f"Duty — US: {(r['duty_estimate'].get('us') or {}).get('rate_pct','–')}% · "
                       f"CA: {(r['duty_estimate'].get('ca') or {}).get('rate_pct','–')}%")
            st.caption(f"FTA: {r['duty_estimate'].get('fta_flag','')}")

# ----- export -----
st.subheader("4 · Export")
export_df = reports_to_df(reports, "Both")
e1, e2 = st.columns([1, 2])
with e1:
    st.download_button("⬇️ Download report (CSV)",
                       export_df.to_csv(index=False),
                       file_name="trade_compliance_report.csv",
                       mime="text/csv", width="stretch")
with e2:
    st.caption("📄 PDF export: open the FastAPI `/report` view in a browser and "
               "Print → Save as PDF for a client-ready branded report (coming "
               "natively in a later build).")

# ----- footer -----
st.markdown(f"""
<div class="footer">
  <b>TradeClear</b> · MVP v0 · Demo build (mock AI engine) ·
  Duty rates are illustrative, not authoritative tariffs ·
  Decision-support only — not a customs ruling or legal advice.
</div>
""", unsafe_allow_html=True)
