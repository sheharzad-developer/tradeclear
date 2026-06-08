"""
TradeClear — AI Trade Compliance Copilot (Streamlit demo).

Four use cases on ONE shared engine (report.build_report):
  1. HS Classification   2. Duty & FTA Optimization
  3. Compliance Risk      4. Audit Packet
plus a duty-leakage headline. Runs fully offline (mock AI).

Run:  streamlit run streamlit_app.py
"""
import time
import io

import pandas as pd
import streamlit as st

from report import build_report, build_audit_packet
from hs_data import HS_DATA

st.set_page_config(page_title="TradeClear — AI Trade Compliance Copilot",
                   page_icon="🛳️", layout="wide")

try:
    st.logo("assets/logo.svg", size="large")
except Exception:
    pass

st.markdown("""
<style>
  .block-container { padding-top: 2rem; max-width: 1200px; }
  .hero { background: linear-gradient(110deg,#0f2d52 0%,#13477f 60%,#1565c0 100%);
          color:#fff; padding:26px 32px; border-radius:14px; margin-bottom:22px; }
  .hero h1 { margin:0; font-size:28px; font-weight:800; letter-spacing:-.01em; }
  .hero p  { margin:6px 0 0; font-size:15px; opacity:.9; }
  .hero .pill { display:inline-block; background:rgba(255,255,255,.16);
                padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600;
                margin-top:12px; }
  div[data-testid="stMetric"] { background:#f7f9fc; border:1px solid #e6ebf2;
        border-radius:12px; padding:14px 18px; }
  div[data-testid="stMetricValue"] { font-size:24px; font-weight:800; }
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
            "sku": g("sku"), "description": g("description") or "",
            "material": g("material"), "origin": g("origin"),
            "customs_value": float(cv) if cv is not None else None,
            "current_hs_code": g("current_hs_code"),
        })
    return products


def fake_processing(n):
    stages = [
        ("📥 Parsing product catalog", 0.3),
        ("🔎 Retrieving HS code candidates", 0.45),
        ("🧠 Running AI classification engine", 0.6),
        ("💵 Estimating US & Canada duties + FTA", 0.45),
        ("🛡️ Scanning for compliance risks", 0.4),
        ("📋 Compiling audit trail", 0.3),
    ]
    with st.status(f"Analyzing {n} product(s)…", expanded=True) as status:
        for label, delay in stages:
            st.write(label)
            time.sleep(delay)
        status.update(label="Analysis complete ✓", state="complete", expanded=False)


def build_insights(reports):
    low = [r for r in reports if r["confidence"] == "low"]
    mism = [r for r in reports if r["code_status"] == "mismatch"]
    fta = [r for r in reports if "potentially" in r["duty_estimate"].get("fta_flag", "")]
    risk = [r for r in reports if r["compliance"]["level"] in ("high", "medium")]
    tariff = [r for r in reports if r.get("tariff_alerts")]
    items = []
    if tariff:
        items.append(("amber", f"📈 <b>{len(tariff)} product(s)</b> are affected by recent "
                              f"tariff changes — duty exposure has moved. See Tariff Watch."))
    if mism:
        items.append(("red", f"⚠️ <b>{len(mism)} product(s)</b> differ from the current "
                             f"HS code — potential over/under-payment. Review before next entry."))
    if risk:
        items.append(("amber", f"🛡️ <b>{len(risk)} product(s)</b> raised compliance flags "
                              f"(restricted origin, missing data, or high value)."))
    if low:
        items.append(("blue", f"🔍 <b>{len(low)} product(s)</b> need customs-broker review "
                            f"(low classification confidence)."))
    if fta:
        items.append(("green", f"🌎 <b>{len(fta)} product(s)</b> are potentially FTA "
                            f"(USMCA/CUSMA) eligible — verify rules of origin."))
    if not items:
        items.append(("green", "✅ No major issues detected in this batch."))
    return items


def fmt_money(v):
    return f"${v:,.0f}" if v else "—"


SAMPLE_CSV = """sku,description,material,origin,customs_value,current_hs_code
TS-001,Men's cotton t-shirt knitted,cotton,MX,5000,
TS-009,Men's polyester performance t-shirt knitted,polyester,CN,6000,6109.10.00.10
BP-002,Nylon travel backpack,nylon,CN,8000,4202.92.31.20
LP-003,14 inch laptop notebook computer,aluminum,CN,40000,
MUG-004,Ceramic stoneware coffee mug,ceramic,CN,1500,6911.10.10.00
CHR-005,USB power adapter wall charger,plastic,MX,3000,
SOFA-006,Upholstered armchair with wooden frame,wood,CA,12000,
STL-013,Stainless steel kitchen knife set,steel,RU,7000,
WID-008,Mystery industrial gadget thingamajig,,CN,1000,
"""


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    country = st.selectbox("Import destination", ["United States", "Canada", "Both"])
    mode = st.radio("Engine mode", ["Demo (mock AI)", "Live API (coming soon)"], index=0)
    if mode.startswith("Live"):
        st.info("Live LLM mode is wired but disabled in this demo build.")
    st.divider()
    st.markdown("**What this copilot does**")
    st.caption("🧠 HS classification\n\n💵 Duty & FTA optimization\n\n"
               "🛡️ Compliance risk checks\n\n📋 Audit-packet generation")
    st.divider()
    st.caption(f"📚 Knowledge base: **{len(HS_DATA)} HS lines** (US + Canada).")
    st.download_button("⬇️ Download sample CSV", SAMPLE_CSV,
                       file_name="sample_products.csv", mime="text/csv", width="stretch")
    st.divider()
    st.caption("⚠️ Decision-support only. Not a customs ruling or legal advice. "
               "Compliance & duty figures are illustrative. Importer of record remains "
               "responsible for final classification.")


# --------------------------------------------------------------------------- #
# Header + upload
# --------------------------------------------------------------------------- #
st.markdown("""
<div class="hero">
  <h1>🛳️ TradeClear — AI Trade Compliance Copilot</h1>
  <p>Classification · duty &amp; FTA optimization · compliance risk · audit packets —
     for importers into the US &amp; Canada.</p>
  <span class="pill">● AI engine online · North America</span>
</div>
""", unsafe_allow_html=True)

st.subheader("Upload your product catalog")
c1, c2 = st.columns([3, 1])
with c1:
    uploaded = st.file_uploader("CSV columns: sku, description, material, origin, "
                                "customs_value, current_hs_code (only *description* required)",
                                type=["csv"])
with c2:
    st.write(""); st.write("")
    use_sample = st.button("✨ Try sample data", width="stretch")

df_in = None
if uploaded is not None:
    df_in = pd.read_csv(uploaded)
elif use_sample:
    df_in = pd.read_csv(io.StringIO(SAMPLE_CSV))

if df_in is None:
    st.info("⬆️ Upload a CSV or click **Try sample data** to see all four use cases.")
    st.stop()

# ----- run the shared (mock) engine -----
products = rows_to_products(df_in)
fake_processing(len(products))
reports = [build_report(p) for p in products]

# --------------------------------------------------------------------------- #
# KPI row + insights
# --------------------------------------------------------------------------- #
total = len(reports)
need_review = sum(1 for r in reports if r["needs_manual_review"])
mismatches = sum(1 for r in reports if r["code_status"] == "mismatch")
fta_count = sum(1 for r in reports if "potentially" in r["duty_estimate"].get("fta_flag", ""))
risk_count = sum(1 for r in reports if r["compliance"]["level"] in ("high", "medium"))
leakage = sum(r["leakage"]["annual_estimate"] for r in reports
              if r.get("leakage") and r["leakage"]["direction"] == "overpayment")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Products analyzed", total)
k2.metric("Compliance flags", risk_count)
k3.metric("Code mismatches", mismatches)
k4.metric("FTA opportunities", fta_count)
k5.metric("Est. duty leakage / yr", fmt_money(leakage),
          help="Illustrative annual overpayment from items whose current code differs "
               "from the suggested code (US rate, ~monthly shipments).")

for sev, text in build_insights(reports):
    st.markdown(f"<div class='insight {sev}'>{text}</div>", unsafe_allow_html=True)

# --------------------------------------------------------------------------- #
# Four use-case tabs
# --------------------------------------------------------------------------- #
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧠  Classification", "💵  Duty & FTA", "🛡️  Compliance Risk",
    "📈  Tariff Watch", "📋  Audit Packet"])

# ---- 1. Classification -----------------------------------------------------
with tab1:
    rows = [{
        "SKU": r["sku"] or "—", "Product": r["product_summary"],
        "Suggested HS": r["final_hs_code"] or "—",
        "Confidence": r["confidence"].capitalize(),
        "Status": ("Needs review" if r["needs_manual_review"]
                   else "Code mismatch" if r["code_status"] == "mismatch" else "OK"),
    } for r in reports]
    df1 = pd.DataFrame(rows)

    def conf_c(v):
        return {"High": "background-color:#e6f7ed;color:#1a7f44;font-weight:600",
                "Medium": "background-color:#fef6e0;color:#b8860b;font-weight:600",
                "Low": "background-color:#fdeaea;color:#c0392b;font-weight:600"}.get(v, "")

    def stat_c(v):
        return {"OK": "color:#1a7f44;font-weight:600",
                "Code mismatch": "background-color:#fef6e0;color:#b8860b;font-weight:600",
                "Needs review": "background-color:#fdeaea;color:#c0392b;font-weight:600"}.get(v, "")

    st.dataframe(df1.style.map(conf_c, subset=["Confidence"]).map(stat_c, subset=["Status"]),
                 width="stretch", hide_index=True)
    st.caption("Each suggestion includes cited reasoning — expand a product for the audit trail.")
    for r in reports:
        icon = "🔴" if r["needs_manual_review"] else "🟡" if r["code_status"] == "mismatch" else "🟢"
        with st.expander(f"{icon} {r['sku']} — {r['product_summary']}"):
            st.markdown(f"**Suggested HS:** `{r['final_hs_code'] or 'n/a'}` · "
                        f"confidence **{r['confidence']}**")
            for c in r["hs_candidates"]:
                st.markdown(f"- `{c['code']}` ({c['confidence']}) — {c['reason']}  \n"
                            f"  _source: {c['source']}_")

# ---- 2. Duty & FTA ---------------------------------------------------------
with tab2:
    rows = []
    for r in reports:
        us = r["duty_estimate"].get("us") or {}
        ca = r["duty_estimate"].get("ca") or {}
        lk = r.get("leakage")
        rows.append({
            "SKU": r["sku"] or "—", "Product": r["product_summary"],
            "HS": r["final_hs_code"] or "—",
            "US %": us.get("rate_pct"), "CA %": ca.get("rate_pct"),
            "FTA": "✅ potential" if "potentially" in r["duty_estimate"].get("fta_flag", "") else "—",
            "Leakage / yr": (lk["annual_estimate"] if lk and lk["direction"] == "overpayment" else None),
        })
    df2 = pd.DataFrame(rows)
    if country == "United States":
        df2 = df2.drop(columns=["CA %"])
    elif country == "Canada":
        df2 = df2.drop(columns=["US %"])
    st.dataframe(
        df2.style.format({"US %": "{:.1f}%", "CA %": "{:.1f}%",
                          "Leakage / yr": "${:,.0f}"}, na_rep="—"),
        width="stretch", hide_index=True)
    a, b = st.columns(2)
    a.metric("Total est. duty leakage / yr", fmt_money(leakage))
    b.metric("FTA savings opportunities", fta_count)
    st.caption("Leakage = current-code duty minus suggested-code duty, annualized "
               "(illustrative). FTA flags require rules-of-origin verification.")

# ---- 3. Compliance Risk ----------------------------------------------------
with tab3:
    levels = {"high": 0, "medium": 0, "low": 0, "clear": 0}
    for r in reports:
        levels[r["compliance"]["level"]] += 1
    c = st.columns(4)
    c[0].metric("🔴 High risk", levels["high"])
    c[1].metric("🟠 Medium", levels["medium"])
    c[2].metric("🔵 Low", levels["low"])
    c[3].metric("🟢 Clear", levels["clear"])
    st.divider()
    sev_class = {"high": "red", "medium": "amber", "low": "blue"}
    any_flag = False
    for r in reports:
        flags = r["compliance"]["flags"]
        if not flags:
            continue
        any_flag = True
        st.markdown(f"**{r['sku']} — {r['product_summary']}**  "
                    f"· risk: `{r['compliance']['level'].upper()}`")
        for f in flags:
            st.markdown(f"<div class='insight {sev_class.get(f['severity'],'blue')}'>"
                        f"[{f['severity'].upper()}] {f['message']}</div>",
                        unsafe_allow_html=True)
    if not any_flag:
        st.success("No compliance flags raised for this batch.")
    st.caption("⚠️ Illustrative checks (restricted origin, missing data, high value, "
               "classification discrepancy). Not a substitute for formal sanctions / "
               "denied-party screening.")

# ---- 4. Tariff Watch -------------------------------------------------------
with tab4:
    st.markdown("**Continuous monitoring:** recent & upcoming tariff changes mapped to "
                "*your* products — the recurring value (we alert you when duty moves).")
    affected = [r for r in reports if r.get("tariff_alerts")]
    total_impact = sum(a["annual_impact"] or 0 for r in reports
                       for a in r.get("tariff_alerts", []))
    m1, m2 = st.columns(2)
    m1.metric("Products affected by tariff changes", len(affected))
    m2.metric("New annual duty exposure (est.)", fmt_money(total_impact))
    st.divider()
    if not affected:
        st.success("No tracked tariff changes affect this batch.")
    for r in affected:
        st.markdown(f"**{r['sku']} — {r['product_summary']}**  · HS `{r['final_hs_code']}`")
        for a in r["tariff_alerts"]:
            up = a["delta"] > 0
            sev = "red" if up else "green"
            arrow = "▲" if up else "▼"
            impact = (f" · est. {'+' if up else ''}${a['annual_impact']:,.0f}/yr"
                      if a["annual_impact"] is not None else "")
            st.markdown(f"<div class='insight {sev}'>{arrow} <b>{a['label']}</b> — "
                        f"duty {'+' if up else ''}{a['delta']*100:.1f}% "
                        f"(effective {a['effective']}, {a['status']}){impact}</div>",
                        unsafe_allow_html=True)
    st.caption("⚠️ Illustrative tariff changes for demo purposes — not live tariff data.")

# ---- 5. Audit Packet -------------------------------------------------------
with tab5:
    st.markdown("Generate an **audit-ready justification packet** for any product — "
                "classification reasoning, sources, duty, and compliance review in one document.")
    skus = [r["sku"] or f"row-{i}" for i, r in enumerate(reports)]
    pick = st.selectbox("Select a product", skus)
    chosen = reports[skus.index(pick)]
    packet = build_audit_packet(chosen)
    with st.container(border=True):
        st.markdown(packet)
    d1, d2 = st.columns(2)
    d1.download_button("⬇️ Download this packet (.md)", packet,
                       file_name=f"audit_{pick}.md", width="stretch")
    all_packets = "\n\n\\newpage\n\n".join(build_audit_packet(r) for r in reports)
    d2.download_button("⬇️ Download all packets", all_packets,
                       file_name="audit_packets_all.md", width="stretch")

# --------------------------------------------------------------------------- #
# Export + footer
# --------------------------------------------------------------------------- #
st.divider()
export_rows = []
for r in reports:
    us = r["duty_estimate"].get("us") or {}
    ca = r["duty_estimate"].get("ca") or {}
    lk = r.get("leakage")
    export_rows.append({
        "sku": r["sku"], "product": r["product_summary"],
        "suggested_hs": r["final_hs_code"], "confidence": r["confidence"],
        "current_hs": r["current_hs_code"], "status": r["code_status"],
        "us_duty_pct": us.get("rate_pct"), "ca_duty_pct": ca.get("rate_pct"),
        "fta_flag": r["duty_estimate"].get("fta_flag"),
        "compliance_level": r["compliance"]["level"],
        "annual_leakage": lk["annual_estimate"] if lk else None,
    })
st.download_button("⬇️ Download full report (CSV)",
                   pd.DataFrame(export_rows).to_csv(index=False),
                   file_name="trade_compliance_report.csv", mime="text/csv")

st.markdown("""
<div class="footer">
  <b>TradeClear</b> · MVP v0 · Demo build (mock AI engine) ·
  Duty &amp; compliance figures are illustrative, not authoritative ·
  Decision-support only — not a customs ruling or legal advice.
</div>
""", unsafe_allow_html=True)
