from hs_data import CODE_INDEX

# Countries whose origin can make goods *potentially* eligible for USMCA/CUSMA.
USMCA_COUNTRIES = {
    "US", "USA", "UNITED STATES", "CA", "CAN", "CANADA",
    "MX", "MEX", "MEXICO",
}


def _amount(rate, customs_value):
    if rate is None or customs_value is None:
        return None
    return round(rate * customs_value, 2)


def estimate_duty(final_code, origin=None, customs_value=None):
    """Look up illustrative US + CA duty for a code and flag potential FTA savings.

    Rates are demo values from the local dataset, NOT authoritative tariffs.
    """
    entry = CODE_INDEX.get(final_code)
    if not entry:
        return {
            "us": None,
            "ca": None,
            "fta_flag": "no rate on file — manual review required",
        }

    us_rate = entry.get("us_duty_rate")
    ca_rate = entry.get("ca_duty_rate")

    origin_norm = (origin or "").strip().upper()
    fta = entry.get("fta") or {}
    if not origin:
        fta_flag = "country of origin not provided — FTA eligibility not assessed"
    elif fta and origin_norm in USMCA_COUNTRIES:
        program = next(iter(fta))
        fta_flag = (f"potentially {program}-eligible (preferential rate "
                    f"{fta[program]*100:.1f}%) — verify rules of origin")
    else:
        fta_flag = "no preferential program flagged for this origin"

    return {
        "us": {
            "rate_pct": round(us_rate * 100, 2) if us_rate is not None else None,
            "estimated_duty": _amount(us_rate, customs_value),
            "note": "general (MFN) rate — illustrative",
        },
        "ca": {
            "rate_pct": round(ca_rate * 100, 2) if ca_rate is not None else None,
            "estimated_duty": _amount(ca_rate, customs_value),
            "note": "general (MFN) rate — illustrative",
        },
        "fta_flag": fta_flag,
    }
