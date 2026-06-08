from retriever import retrieve_candidates
from ranker import rank
from duty import estimate_duty
from compliance import check_compliance
from tariffs import affected_changes
from hs_data import CODE_INDEX

DISCLAIMER = ("This report is AI-assisted decision-support for review by a licensed "
              "customs broker. It is not a customs ruling or legal advice. The importer "
              "of record remains responsible for the final classification and entry. "
              "Duty rates shown are illustrative demo values, not authoritative tariffs.")


def _assumptions(product, ranked):
    notes = []
    if not product.get("material"):
        notes.append("Material not provided — matched on description only.")
    if not product.get("origin"):
        notes.append("Country of origin not provided — FTA eligibility not assessed.")
    if ranked["needs_manual_review"]:
        notes.append("Low confidence — recommend manual broker review.")
    return notes


def _leakage(product, final_code):
    """Illustrative duty leakage vs. the current code (US rate)."""
    current = product.get("current_hs_code")
    cv = product.get("customs_value")
    if not current or not final_code or current == final_code or not cv:
        return None
    cur, sug = CODE_INDEX.get(current), CODE_INDEX.get(final_code)
    if not cur or not sug:
        return None
    cur_rate, sug_rate = cur.get("us_duty_rate"), sug.get("us_duty_rate")
    if cur_rate is None or sug_rate is None:
        return None
    diff = cur_rate - sug_rate                 # positive => currently overpaying
    per_shipment = round(diff * cv, 2)
    return {
        "per_shipment": per_shipment,
        "annual_estimate": round(per_shipment * 12, 2),
        "direction": "overpayment" if diff > 0 else "underpayment",
        "basis": "vs. current code · US rate · assumes ~monthly shipments (illustrative)",
    }


def build_report(product):
    """Full per-SKU pipeline: retrieve -> rank (mock AI) -> duty -> risk -> assemble."""
    candidates = retrieve_candidates(product.get("description"), product.get("material"))
    ranked = rank(product, candidates)
    duty = estimate_duty(ranked["final"], product.get("origin"),
                         product.get("customs_value"))

    # Compare against the importer's current code (the "your code looks off" signal).
    current = product.get("current_hs_code")
    if not current or not ranked["final"]:
        code_status = "no_current_code"
    elif current.strip() == ranked["final"]:
        code_status = "match"
    else:
        code_status = "mismatch"

    desc = product.get("description") or ""
    summary = desc.strip().capitalize()[:120] or "Unspecified product"

    report = {
        "sku": product.get("sku"),
        "product_summary": summary,
        "hs_candidates": ranked["candidates"],
        "final_hs_code": ranked["final"],
        "confidence": ranked["confidence"],
        "needs_manual_review": ranked["needs_manual_review"],
        "current_hs_code": current,
        "code_status": code_status,
        "duty_estimate": duty,
        "leakage": _leakage(product, ranked["final"]),
        "tariff_alerts": affected_changes(ranked["final"], product.get("customs_value")),
        "assumptions": _assumptions(product, ranked),
        "disclaimer": DISCLAIMER,
    }
    report["compliance"] = check_compliance(product, report)
    return report


def build_audit_packet(r):
    """One-click audit-ready justification bundle (Markdown) for a single product."""
    duty = r["duty_estimate"]
    us = duty.get("us") or {}
    ca = duty.get("ca") or {}
    lines = [
        f"# Audit Packet — {r['sku'] or 'Product'}",
        f"**Product:** {r['product_summary']}",
        "",
        "## 1. Classification",
        f"- **Suggested HS code:** {r['final_hs_code'] or 'n/a'} "
        f"(confidence: {r['confidence']})",
        f"- **Current code on file:** {r['current_hs_code'] or '— none —'}",
    ]
    if r["code_status"] == "mismatch":
        lines.append(f"- ⚠️ **Discrepancy:** declared code differs from suggested code.")
    lines.append("")
    lines.append("## 2. Classification reasoning (audit trail)")
    for c in r["hs_candidates"]:
        lines.append(f"- `{c['code']}` ({c['confidence']}) — {c['reason']}")
        lines.append(f"  - *Source:* {c['source']}")
    lines += [
        "",
        "## 3. Duty assessment (illustrative)",
        f"- USA: {us.get('rate_pct', '–')}%  ·  est. duty "
        f"{('$'+format(us['estimated_duty'],',.2f')) if us.get('estimated_duty') is not None else '–'}",
        f"- Canada: {ca.get('rate_pct', '–')}%  ·  est. duty "
        f"{('$'+format(ca['estimated_duty'],',.2f')) if ca.get('estimated_duty') is not None else '–'}",
        f"- FTA: {duty.get('fta_flag', '')}",
        "",
        "## 4. Compliance review",
        f"- Risk level: **{r['compliance']['level'].upper()}**",
    ]
    for f in r["compliance"]["flags"]:
        lines.append(f"- [{f['severity'].upper()}] {f['message']}")
    if not r["compliance"]["flags"]:
        lines.append("- No flags raised.")
    lines += ["", "---", f"_{r['disclaimer']}_"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Printable HTML report (open in browser -> Print -> Save as PDF).
# ---------------------------------------------------------------------------

def _fmt_money(v):
    return f"${v:,.2f}" if v is not None else "–"


def _summary_banner(reports):
    total = len(reports)
    flagged = sum(1 for r in reports if r["needs_manual_review"])
    mismatches = sum(1 for r in reports if r["code_status"] == "mismatch")
    fta = sum(1 for r in reports if "potentially" in r["duty_estimate"].get("fta_flag", ""))
    us_total = sum((r["duty_estimate"].get("us") or {}).get("estimated_duty") or 0
                   for r in reports)
    return f"""
    <div class="banner">
      <div class="stat"><span class="num">{total}</span><span class="lbl">products analyzed</span></div>
      <div class="stat"><span class="num warn">{flagged}</span><span class="lbl">need broker review</span></div>
      <div class="stat"><span class="num alert">{mismatches}</span><span class="lbl">differ from current code</span></div>
      <div class="stat"><span class="num good">{fta}</span><span class="lbl">potential FTA savings</span></div>
      <div class="stat"><span class="num">{_fmt_money(us_total) if us_total else '–'}</span><span class="lbl">est. US duty (where value given)</span></div>
    </div>"""


def _row(r):
    cands = "".join(
        f"<li><b>{c['code']}</b> "
        f"<span class='conf {c['confidence']}'>{c['confidence']}</span><br>"
        f"<small>{c['reason']}</small></li>"
        for c in r["hs_candidates"]
    ) or "<li><em>No candidate matched — manual review required.</em></li>"

    duty = r["duty_estimate"]
    us = duty.get("us") or {}
    ca = duty.get("ca") or {}

    if r["needs_manual_review"]:
        status_html = "<span class='status flag'>NEEDS REVIEW</span>"
    elif r["code_status"] == "mismatch":
        status_html = "<span class='status alert'>CODE MISMATCH</span>"
    else:
        status_html = "<span class='status ok'>OK</span>"

    # Surface the current-vs-suggested comparison prominently when they differ.
    compare_html = ""
    if r["code_status"] == "mismatch":
        compare_html = (f"<div class='compare'>⚠ Current code "
                        f"<b>{r['current_hs_code']}</b> differs from suggested "
                        f"<b>{r['final_hs_code']}</b> — confirm with your broker.</div>")

    return f"""
    <div class="card">
      <div class="head">
        <span class="sku">{r['sku'] or '-'}</span>
        {status_html}
      </div>
      <div class="summary">{r['product_summary']}</div>
      {compare_html}
      <div class="grid">
        <div>
          <h4>Suggested HS classification</h4>
          <ul class="cands">{cands}</ul>
          <p class="final">Best match: <b>{r['final_hs_code'] or 'n/a'}</b>
             <span class="conf {r['confidence']}">{r['confidence']}</span></p>
        </div>
        <div>
          <h4>Estimated duty (illustrative)</h4>
          <table class="duty">
            <tr><th></th><th>Rate</th><th>Est. duty</th></tr>
            <tr><td>🇺🇸 USA</td><td>{us.get('rate_pct', '–')}%</td>
                <td>{_fmt_money(us.get('estimated_duty'))}</td></tr>
            <tr><td>🇨🇦 Canada</td><td>{ca.get('rate_pct', '–')}%</td>
                <td>{_fmt_money(ca.get('estimated_duty'))}</td></tr>
          </table>
          <p class="fta">{duty.get('fta_flag', '')}</p>
        </div>
      </div>
      {('<div class="assume"><b>Notes:</b> ' + ' '.join(r['assumptions']) + '</div>') if r['assumptions'] else ''}
    </div>"""


def render_html(reports):
    cards = "".join(_row(r) for r in reports)
    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>HS Classification Report</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; color:#1a1a2e;
         max-width: 920px; margin: 32px auto; padding: 0 16px; }}
  h1 {{ font-size: 22px; margin-bottom: 2px; }}
  .meta {{ color:#666; font-size: 13px; margin-bottom: 16px; }}
  .disclaimer {{ background:#fff8e6; border:1px solid #f0d98a; border-radius:8px;
                 padding:10px 14px; font-size:12px; color:#6b5800; margin-bottom:22px; }}
  .banner {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:24px; }}
  .stat {{ flex:1; min-width:120px; background:#f7f7fb; border:1px solid #ececf4;
           border-radius:10px; padding:12px 14px; display:flex; flex-direction:column; }}
  .stat .num {{ font-size:24px; font-weight:800; }}
  .stat .num.warn {{ color:#c0392b; }} .stat .num.alert {{ color:#b8860b; }}
  .stat .num.good {{ color:#1a7f44; }}
  .stat .lbl {{ font-size:11px; color:#777; text-transform:uppercase; letter-spacing:.03em; }}
  .card {{ border:1px solid #e2e2ea; border-radius:10px; padding:16px 20px;
          margin-bottom:18px; box-shadow:0 1px 3px rgba(0,0,0,.04); }}
  .head {{ display:flex; justify-content:space-between; align-items:center; }}
  .sku {{ font-weight:700; font-size:15px; }}
  .status {{ font-size:11px; font-weight:700; padding:3px 9px; border-radius:20px; }}
  .status.ok {{ background:#e6f7ed; color:#1a7f44; }}
  .status.flag {{ background:#fdeaea; color:#c0392b; }}
  .status.alert {{ background:#fef6e0; color:#b8860b; }}
  .summary {{ color:#444; margin:6px 0 10px; }}
  .compare {{ background:#fef6e0; border:1px solid #f0d98a; border-radius:6px;
              padding:8px 12px; font-size:13px; color:#7a5c00; margin-bottom:12px; }}
  .grid {{ display:grid; grid-template-columns:1.25fr 1fr; gap:24px; }}
  h4 {{ margin:0 0 8px; font-size:12px; text-transform:uppercase; color:#888; letter-spacing:.04em; }}
  ul.cands {{ list-style:none; padding:0; margin:0; }}
  ul.cands li {{ margin-bottom:8px; }}
  .conf {{ font-size:10px; font-weight:700; padding:1px 7px; border-radius:10px; }}
  .conf.high {{ background:#e6f7ed; color:#1a7f44; }}
  .conf.medium {{ background:#fef6e0; color:#b8860b; }}
  .conf.low {{ background:#fdeaea; color:#c0392b; }}
  .final {{ margin-top:10px; }}
  table.duty {{ border-collapse:collapse; width:100%; font-size:13px; }}
  table.duty th, table.duty td {{ text-align:left; padding:4px 8px; border-bottom:1px solid #eee; }}
  .fta {{ font-size:12px; color:#555; margin-top:8px; font-style:italic; }}
  .assume {{ margin-top:12px; font-size:12px; color:#555; background:#f7f7fb;
             padding:8px 10px; border-radius:6px; }}
  .foot {{ margin-top:24px; font-size:11px; color:#999; border-top:1px solid #eee; padding-top:12px; }}
</style></head><body>
<h1>AI Trade Compliance Copilot</h1>
<div class="meta">HS classification &amp; indicative US / Canada duty · generated for broker review</div>
<div class="disclaimer">{DISCLAIMER}</div>
{_summary_banner(reports)}
{cards}
<div class="foot">{DISCLAIMER}</div>
</body></html>"""
