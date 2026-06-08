"""Mock tariff-change monitor (illustrative — not real tariff actions).
Maps recent/upcoming duty changes to a product by HS chapter, with $ impact.
This is the 'continuous monitoring / system of record' hook (recurring value)."""

from hs_data import CODE_INDEX

# Illustrative tariff changes by HS chapter. delta = change to the US duty rate.
TARIFF_CHANGES = [
    {"chapter": "84", "label": "Electronics — Section 301 List 4 duties reinstated",
     "delta": 0.075, "effective": "2026-04-01", "status": "in effect"},
    {"chapter": "85", "label": "Electrical components — import surcharge",
     "delta": 0.075, "effective": "2026-04-01", "status": "in effect"},
    {"chapter": "69", "label": "Ceramic tableware — antidumping duty review",
     "delta": 0.12, "effective": "2026-02-15", "status": "in effect"},
    {"chapter": "42", "label": "Travel goods & bags — tariff reinstatement",
     "delta": 0.10, "effective": "2026-05-01", "status": "in effect"},
    {"chapter": "73", "label": "Steel articles — Section 232 surcharge",
     "delta": 0.25, "effective": "2026-03-01", "status": "in effect"},
    {"chapter": "61", "label": "Apparel — proposed FTA expansion (reduction)",
     "delta": -0.02, "effective": "2026-07-01", "status": "proposed"},
]


def affected_changes(final_code, customs_value):
    """Tariff changes that hit this product's HS chapter, with annualized impact."""
    if not final_code:
        return []
    chapter = (CODE_INDEX.get(final_code) or {}).get("chapter") or final_code[:2]
    out = []
    for c in TARIFF_CHANGES:
        if c["chapter"] == chapter:
            impact = round(c["delta"] * customs_value * 12, 2) if customs_value else None
            out.append({**c, "annual_impact": impact})
    return out
