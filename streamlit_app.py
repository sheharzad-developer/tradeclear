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

C = {"navy": "#0f172a", "blue": "#2563eb", "green": "#16a34a",
     "amber": "#d97706", "red": "#dc2626", "grey": "#cbd5e1"}

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  html, body, .stApp, [data-testid="stMarkdownContainer"], button, input, select {
        font-family: 'Inter', -apple-system, Segoe UI, sans-serif !important; }
  .stApp { background: #f4f6fb; }
  /* hide Streamlit chrome for an app (not 'tool') feel */
  [data-testid="stHeader"] { background: transparent; height: 0; }
  [data-testid="stToolbar"], #MainMenu, footer { display: none; }
  .block-container { padding-top: 1.4rem; max-width: 1200px; }

  /* clean light nav rail */
  section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid #e7ecf3; }
  section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
  section[data-testid="stSidebar"] label,
  section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2,
  section[data-testid="stSidebar"] h3 { color: #334155 !important; }

  /* slim header bar instead of a marketing hero */
  .hero { background:#fff; border:1px solid #e7ecf3; padding:18px 24px; border-radius:16px;
          margin-bottom:18px; box-shadow:0 1px 3px rgba(15,23,42,.04);
          display:flex; align-items:center; justify-content:space-between; }
  .hero h1 { margin:0; font-size:22px; font-weight:800; color:#0f172a; letter-spacing:-.02em; }
  .hero p  { margin:3px 0 0; font-size:13px; color:#64748b; }
  .hero .pill { display:inline-block; background:#ecfdf3; color:#16a34a;
                padding:5px 13px; border-radius:20px; font-size:12px; font-weight:700; }

  /* modern KPI cards */
  div[data-testid="stMetric"] { background:#fff; border:1px solid #e7ecf3;
        border-radius:16px; padding:18px 20px; box-shadow:0 1px 3px rgba(15,23,42,.05); }
  div[data-testid="stMetricLabel"] p { font-size:12px; font-weight:600; color:#64748b;
        text-transform:uppercase; letter-spacing:.04em; }
  div[data-testid="stMetricValue"] { font-size:25px; font-weight:800; color:#0f172a; }

  .chip { padding:12px 14px; border-radius:14px; font-size:13px; font-weight:600;
          text-align:center; line-height:1.3; border:1px solid transparent; }
  .chip.red{background:#fef2f2;color:#b91c1c;border-color:#fee2e2;}
  .chip.amber{background:#fffbeb;color:#b45309;border-color:#fef3c7;}
  .chip.green{background:#f0fdf4;color:#15803d;border-color:#dcfce7;}
  .chip.blue{background:#eff6ff;color:#1d4ed8;border-color:#dbeafe;}
  .flagcard { border-radius:12px; padding:11px 14px; margin-bottom:8px; font-size:13px;
              background:#fff; border:1px solid #eef1f6; }
  .flagcard.red{border-left:4px solid #dc2626;} .flagcard.amber{border-left:4px solid #d97706;}
  .flagcard.blue{border-left:4px solid #2563eb;} .flagcard.green{border-left:4px solid #16a34a;}

  /* modern tabs */
  .stTabs [data-baseweb="tab-list"] { gap:6px; border-bottom:1px solid #e7ecf3; }
  .stTabs [data-baseweb="tab"] { font-weight:600; padding:8px 16px; color:#64748b; }
  .stTabs [aria-selected="true"] { color:#2563eb !important; }
  .footer { color:#94a3b8; font-size:12px; border-top:1px solid #e7ecf3;
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
BRD-014,Bamboo composite serving board,bamboo,CN,2000,
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
  <div>
    <h1>🛳️ TradeClear</h1>
    <p>AI trade-compliance copilot — classify · optimize duty · flag risk · track tariffs</p>
  </div>
  <span class="pill">● AI engine online</span>
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
