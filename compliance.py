"""Mock compliance-risk checker (illustrative — not a real sanctions/denied-party
screen). Deterministic rules over the product + classification result."""

# Illustrative restricted/sanctioned origins — NOT an official or complete list.
RESTRICTED_ORIGINS = {
    "IR": "Iran", "IRAN": "Iran",
    "KP": "North Korea", "NORTH KOREA": "North Korea",
    "SY": "Syria", "SYRIA": "Syria",
    "CU": "Cuba", "CUBA": "Cuba",
    "RU": "Russia", "RUSSIA": "Russia",
}
HIGH_VALUE_THRESHOLD = 25000


def check_compliance(product, report):
    flags = []
    origin = (product.get("origin") or "").strip().upper()

    if origin in RESTRICTED_ORIGINS:
        flags.append(("high", f"Origin **{RESTRICTED_ORIGINS[origin]}** appears on a "
                              f"restricted/sanctioned watchlist — screening required "
                              f"before import."))

    missing = [f for f in ("material", "origin", "customs_value") if not product.get(f)]
    if missing:
        flags.append(("medium", f"Missing {', '.join(missing)} — entry is not "
                                f"audit-ready; complete before filing."))

    if not product.get("current_hs_code"):
        flags.append(("low", "No HS code on file — classification is undocumented."))

    cv = product.get("customs_value")
    if cv and cv >= HIGH_VALUE_THRESHOLD:
        flags.append(("medium", f"High-value shipment (${cv:,.0f}) — higher audit "
                                f"scrutiny; ensure valuation support is on file."))

    if report.get("needs_manual_review"):
        flags.append(("high", "Low-confidence classification — broker review required "
                              "before filing."))

    if report.get("code_status") == "mismatch":
        flags.append(("high", "Declared code differs from the suggested code — "
                              "potential mis-declaration."))

    level = ("high" if any(s == "high" for s, _ in flags)
             else "medium" if any(s == "medium" for s, _ in flags)
             else "low" if flags else "clear")

    return {"level": level,
            "flags": [{"severity": s, "message": m} for s, m in flags]}
