"""
TradeClear — AI Trade Compliance Copilot (Streamlit demo).

Five use cases on ONE shared engine (report.build_report):
  Classification · Duty & FTA · Compliance Risk · Tariff Watch · Audit Packet
Visual, chart-driven dashboard. Runs fully offline (mock AI).

Run:  streamlit run streamlit_app.py
"""
import time
import io

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from report import build_report, build_audit_packet
from hs_data import HS_DATA

st.set_page_config(page_title="TradeClear — AI Trade Compliance Copilot",
                   page_icon="🛳️", layout="wide")

try:
    st.logo("assets/logo.svg", size="large")
except Exception:
    pass

C = {"navy": "#0f2d52", "blue": "#1565c0", "green": "#1a7f44",
     "amber": "#d99a00", "red": "#d04437", "grey": "#c4cbd6"}

st.markdown("""
<style>
  .block-container { padding-top: 2rem; max-width: 1180px; }
  .hero { background: linear-gradient(110deg,#0f2d52 0%,#13477f 55%,#1565c0 100%);
          color:#fff; padding:24px 30px; border-radius:16px; margin-bottom:20px; }
  .hero h1 { margin:0; font-size:27px; font-weight:800; letter-spacing:-.01em; }
  .hero p  { margin:5px 0 0; font-size:14px; opacity:.85; }
  .hero .pill { display:inline-block; background:rgba(255,255,255,.16);
                padding:3px 12px; border-radius:20px; font-size:12px; font-weight:600;
                margin-top:10px; }
  div[data-testid="stMetric"] { background:#fff; border:1px solid #e8edf4;
        border-radius:14px; padding:16px 18px; box-shadow:0 1px 2px rgba(16,40,80,.04); }
  div[data-testid="stMetricValue"] { font-size:24px; font-weight:800; color:#0f2d52; }
  .chip { padding:11px 14px; border-radius:12px; font-size:13px; font-weight:600;
          text-align:center; line-height:1.3; }
  .chip.red{background:#fdecea;color:#c0392b;} .chip.amber{background:#fdf6e3;color:#9a7400;}
  .chip.green{background:#e9f8ef;color:#1a7f44;} .chip.blue{background:#eaf2fd;color:#1565c0;}
  .flagcard { border-radius:10px; padding:9px 13px; margin-bottom:8px; font-size:13px; }
  .flagcard.red{background:#fdecea;border-left:3px solid #d04437;}
  .flagcard.amber{background:#fdf6e3;border-left:3px solid #d99a00;}
  .flagcard.blue{background:#eaf2fd;border-left:3px solid #1565c0;}
  .flagcard.green{background:#e9f8ef;border-left:3px solid #1a7f44;}
  .stTabs [data-baseweb="tab"] { font-weight:600; }
  .footer { color:#9aa3b2; font-size:12px; border-top:1px solid #e8edf4;
            padding-top:12px; margin-top:26px; }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Chart + data helpers
# --------------------------------------------------------------------------- #
def donut(labels, values, colors):
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=.64, sort=False,
                           marker=dict(colors=colors, line=dict(color="#fff", width=2)),
                           textinfo="value", textfont_size=14))
    fig.update_layout(height=240, margin=dict(t=6, b=6, l=6, r=6),
                      paper_bgcolor="rgba(0,0,0,0)",
                      legend=dict(orientation="h", yanchor="bottom", y=-0.15, x=0.5,
                                  xanchor="center"))
    return fig


def hbar(labels, values, colors):
    fig = go.Figure(go.Bar(x=values, y=labels, orientation="h", marker_color=colors,
                           text=[f"${v:,.0f}" for v in values], textposition="outside",
                           cliponaxis=False))
    fig.update_layout(height=max(170, 42 * len(labels) + 50),
                      margin=dict(t=10, b=10, l=10, r=50),
                      paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      yaxis=dict(autorange="reversed"), font=dict(size=13))
    fig.update_xaxes(visible=False, showgrid=False, zeroline=False)
    return fig


PLOT_CFG = {"displayModeBar": False}


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
    stages = [("📥 Parsing catalog", 0.3), ("🔎 Retrieving HS candidates", 0.4),
              ("🧠 AI classification", 0.55), ("💵 Duty & FTA", 0.4),
              ("🛡️ Compliance & tariff scan", 0.45)]
    with st.status(f"Analyzing {n} product(s)…", expanded=True) as status:
        for label, delay in stages:
            st.write(label)
            time.sleep(delay)
        status.update(label="Analysis complete ✓", state="complete", expanded=False)


def insight_chips(reports):
    low = sum(1 for r in reports if r["confidence"] == "low")
    mism = sum(1 for r in reports if r["code_status"] == "mismatch")
    fta = sum(1 for r in reports if "potentially" in r["duty_estimate"].get("fta_flag", ""))
    risk = sum(1 for r in reports if r["compliance"]["level"] in ("high", "medium"))
    tariff = sum(1 for r in reports if r.get("tariff_alerts"))
    out = []
    if tariff: out.append(("amber", f"📈 {tariff} hit by tariff changes"))
    if mism: out.append(("red", f"⚠️ {mism} code mismatches"))
    if risk: out.append(("amber", f"🛡️ {risk} compliance flags"))
    if low: out.append(("blue", f"🔍 {low} need review"))
    if fta: out.append(("green", f"🌎 {fta} FTA opportunities"))
    return out or [("green", "✅ No major issues")]


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
    st.radio("Engine mode", ["Demo (mock AI)", "Live API (soon)"], index=0)
    st.divider()
    st.caption(f"📚 {len(HS_DATA)} HS lines · US + Canada")
    st.download_button("⬇️ Sample CSV", SAMPLE_CSV, file_name="sample_products.csv",
                       mime="text/csv", width="stretch")
    st.divider()
    st.caption("⚠️ Decision-support only — not a customs ruling. Figures illustrative.")


# --------------------------------------------------------------------------- #
# Header + upload
# --------------------------------------------------------------------------- #
st.markdown("""
<div class="hero">
  <h1>🛳️ TradeClear</h1>
  <p>AI trade-compliance copilot — classify, optimize duty, flag risk, track tariffs.</p>
  <span class="pill">● AI engine online · North America</span>
</div>
""", unsafe_allow_html=True)

c1, c2 = st.columns([3, 1])
with c1:
    uploaded = st.file_uploader("Upload product catalog (CSV)", type=["csv"],
                                label_visibility="collapsed")
with c2:
    use_sample = st.button("✨ Try sample data", width="stretch")

df_in = None
if uploaded is not None:
    df_in = pd.read_csv(uploaded)
elif use_sample:
    df_in = pd.read_csv(io.StringIO(SAMPLE_CSV))

if df_in is None:
    st.info("⬆️ Upload a CSV or click **Try sample data** to explore the five use cases.")
    st.stop()

products = rows_to_products(df_in)
fake_processing(len(products))
reports = [build_report(p) for p in products]

# --------------------------------------------------------------------------- #
# KPI row + insight chips
# --------------------------------------------------------------------------- #
total = len(reports)
need_review = sum(1 for r in reports if r["needs_manual_review"])
mismatches = sum(1 for r in reports if r["code_status"] == "mismatch")
fta_count = sum(1 for r in reports if "potentially" in r["duty_estimate"].get("fta_flag", ""))
risk_count = sum(1 for r in reports if r["compliance"]["level"] in ("high", "medium"))
leakage = sum(r["leakage"]["annual_estimate"] for r in reports
              if r.get("leakage") and r["leakage"]["direction"] == "overpayment")
tariff_exposure = sum(a["annual_impact"] or 0 for r in reports
                      for a in r.get("tariff_alerts", []))

k = st.columns(5)
k[0].metric("Products", total)
k[1].metric("Compliance flags", risk_count)
k[2].metric("Code mismatches", mismatches)
k[3].metric("Duty leakage / yr", fmt_money(leakage))
k[4].metric("Tariff exposure / yr", fmt_money(tariff_exposure))

chips = insight_chips(reports)
cc = st.columns(len(chips))
for col, (sev, txt) in zip(cc, chips):
    col.markdown(f"<div class='chip {sev}'>{txt}</div>", unsafe_allow_html=True)

st.write("")

# --------------------------------------------------------------------------- #
# Tabs
# --------------------------------------------------------------------------- #
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧠  Classification", "💵  Duty & FTA", "🛡️  Compliance",
    "📈  Tariff Watch", "📋  Audit Packet"])

# ---- 1. Classification -----------------------------------------------------
with tab1:
    left, right = st.columns([1.6, 1])
    with left:
        rows = [{
            "SKU": r["sku"] or "—", "Product": r["product_summary"][:34],
            "HS code": r["final_hs_code"] or "—",
            "Confidence": r["confidence"].capitalize(),
            "Status": ("Review" if r["needs_manual_review"]
                       else "Mismatch" if r["code_status"] == "mismatch" else "OK"),
        } for r in reports]
        df1 = pd.DataFrame(rows)

        def conf_c(v):
            return {"High": f"background-color:#e9f8ef;color:{C['green']};font-weight:600",
                    "Medium": f"background-color:#fdf6e3;color:{C['amber']};font-weight:600",
                    "Low": f"background-color:#fdecea;color:{C['red']};font-weight:600"}.get(v, "")

        def stat_c(v):
            return {"OK": f"color:{C['green']};font-weight:600",
                    "Mismatch": f"background-color:#fdf6e3;color:{C['amber']};font-weight:600",
                    "Review": f"background-color:#fdecea;color:{C['red']};font-weight:600"}.get(v, "")

        st.dataframe(df1.style.map(conf_c, subset=["Confidence"]).map(stat_c, subset=["Status"]),
                     width="stretch", hide_index=True)
    with right:
        hi = sum(1 for r in reports if r["confidence"] == "high")
        me = sum(1 for r in reports if r["confidence"] == "medium")
        lo = sum(1 for r in reports if r["confidence"] == "low")
        st.plotly_chart(donut(["High", "Medium", "Low"], [hi, me, lo],
                              [C["green"], C["amber"], C["red"]]),
                        use_container_width=True, config=PLOT_CFG)
        st.caption("Classification confidence")

    for r in reports:
        icon = "🔴" if r["needs_manual_review"] else "🟡" if r["code_status"] == "mismatch" else "🟢"
        with st.expander(f"{icon} {r['sku']} — {r['product_summary']}"):
            for c in r["hs_candidates"]:
                st.markdown(f"- `{c['code']}` ({c['confidence']}) — {c['reason']}")

# ---- 2. Duty & FTA ---------------------------------------------------------
with tab2:
    a, b = st.columns(2)
    a.metric("Duty leakage / yr", fmt_money(leakage))
    b.metric("FTA opportunities", fta_count)
    leak = [(r["sku"] or "—", r["leakage"]["annual_estimate"]) for r in reports
            if r.get("leakage") and r["leakage"]["direction"] == "overpayment"]
    if leak:
        leak.sort(key=lambda x: x[1], reverse=True)
        st.plotly_chart(hbar([x[0] for x in leak], [x[1] for x in leak],
                             [C["red"]] * len(leak)), use_container_width=True, config=PLOT_CFG)
        st.caption("Estimated annual duty overpayment by product")
    rows = []
    for r in reports:
        us = r["duty_estimate"].get("us") or {}
        ca = r["duty_estimate"].get("ca") or {}
        rows.append({"SKU": r["sku"] or "—", "HS": r["final_hs_code"] or "—",
                     "US %": us.get("rate_pct"), "CA %": ca.get("rate_pct"),
                     "FTA": "✅" if "potentially" in r["duty_estimate"].get("fta_flag", "") else "—"})
    df2 = pd.DataFrame(rows)
    if country == "United States": df2 = df2.drop(columns=["CA %"])
    elif country == "Canada": df2 = df2.drop(columns=["US %"])
    with st.expander("Duty rate detail"):
        st.dataframe(df2.style.format({"US %": "{:.1f}%", "CA %": "{:.1f}%"}, na_rep="—"),
                     width="stretch", hide_index=True)

# ---- 3. Compliance ---------------------------------------------------------
with tab3:
    levels = {"high": 0, "medium": 0, "low": 0, "clear": 0}
    for r in reports:
        levels[r["compliance"]["level"]] += 1
    left, right = st.columns([1, 1.4])
    with left:
        st.plotly_chart(donut(["High", "Medium", "Low", "Clear"],
                              [levels["high"], levels["medium"], levels["low"], levels["clear"]],
                              [C["red"], C["amber"], C["blue"], C["green"]]),
                        use_container_width=True, config=PLOT_CFG)
        st.caption("Compliance risk distribution")
    with right:
        sev_class = {"high": "red", "medium": "amber", "low": "blue"}
        shown = False
        for r in reports:
            for f in r["compliance"]["flags"]:
                shown = True
                st.markdown(f"<div class='flagcard {sev_class.get(f['severity'],'blue')}'>"
                            f"<b>{r['sku']}</b> · {f['message']}</div>", unsafe_allow_html=True)
        if not shown:
            st.success("No compliance flags raised.")

# ---- 4. Tariff Watch -------------------------------------------------------
with tab4:
    a, b = st.columns(2)
    affected = [r for r in reports if r.get("tariff_alerts")]
    a.metric("Products affected", len(affected))
    b.metric("New exposure / yr", fmt_money(tariff_exposure))
    bars = [(r["sku"] or "—", sum(x["annual_impact"] or 0 for x in r["tariff_alerts"]))
            for r in affected]
    bars = [x for x in bars if x[1]]
    if bars:
        bars.sort(key=lambda x: x[1], reverse=True)
        cols = [C["red"] if v > 0 else C["green"] for _, v in bars]
        st.plotly_chart(hbar([x[0] for x in bars], [x[1] for x in bars], cols),
                        use_container_width=True, config=PLOT_CFG)
        st.caption("Estimated annual duty impact from tariff changes")
    for r in affected:
        for x in r["tariff_alerts"]:
            up = x["delta"] > 0
            cls = "red" if up else "green"
            arrow = "▲" if up else "▼"
            st.markdown(f"<div class='flagcard {cls}'><b>{r['sku']}</b> · {arrow} "
                        f"{x['label']} ({'+' if up else ''}{x['delta']*100:.1f}%, "
                        f"{x['effective']})</div>", unsafe_allow_html=True)
    if not affected:
        st.success("No tracked tariff changes affect this batch.")

# ---- 5. Audit Packet -------------------------------------------------------
with tab5:
    skus = [r["sku"] or f"row-{i}" for i, r in enumerate(reports)]
    pick = st.selectbox("Select a product", skus, label_visibility="collapsed")
    chosen = reports[skus.index(pick)]
    packet = build_audit_packet(chosen)
    with st.container(border=True):
        st.markdown(packet)
    d1, d2 = st.columns(2)
    d1.download_button("⬇️ This packet (.md)", packet, file_name=f"audit_{pick}.md",
                       width="stretch")
    d2.download_button("⬇️ All packets", "\n\n---\n\n".join(build_audit_packet(r) for r in reports),
                       file_name="audit_packets_all.md", width="stretch")

# --------------------------------------------------------------------------- #
# Export + footer
# --------------------------------------------------------------------------- #
st.divider()
export_rows = []
for r in reports:
    us = r["duty_estimate"].get("us") or {}
    lk = r.get("leakage")
    export_rows.append({
        "sku": r["sku"], "product": r["product_summary"],
        "suggested_hs": r["final_hs_code"], "confidence": r["confidence"],
        "status": r["code_status"], "us_duty_pct": us.get("rate_pct"),
        "compliance_level": r["compliance"]["level"],
        "annual_leakage": lk["annual_estimate"] if lk else None,
    })
st.download_button("⬇️ Download full report (CSV)",
                   pd.DataFrame(export_rows).to_csv(index=False),
                   file_name="trade_compliance_report.csv", mime="text/csv")

st.markdown("""
<div class="footer"><b>TradeClear</b> · MVP v0 · Demo build (mock AI) ·
Figures illustrative · Decision-support only.</div>
""", unsafe_allow_html=True)
