import os
import json

from text_utils import tokenize
from prompt import SYSTEM_PROMPT

try:  # load .env so OPENAI_API_KEY / USE_LLM are available, if present
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ---------------------------------------------------------------------------
# SWAPPABLE RANKER.
# rank(product, candidates) -> {
#   "candidates": [{"code","confidence","reason","source"}, ...],  # top 1-3
#   "final": <code or None>,
#   "confidence": "high|medium|low",
#   "needs_manual_review": <bool>,
# }
#
# Two backends behind one interface:
#   - LLM   (real AI) when USE_LLM=true AND an API key is set
#   - mock  (keyword scoring) otherwise — so the app always runs.
# Either way the output is re-validated against the retrieved candidate set,
# so no hallucinated code can ever reach the report.
# ---------------------------------------------------------------------------


def rank(product, candidates):
    if not candidates:
        return {"candidates": [], "final": None,
                "confidence": "low", "needs_manual_review": True}

    if _llm_enabled():
        try:
            return _validate(_llm_rank(product, candidates), candidates)
        except Exception as e:  # never let a bad API call break the demo
            print(f"[ranker] LLM call failed ({e}); falling back to mock.")

    return _mock_rank(product, candidates)


def _llm_enabled():
    return (os.getenv("USE_LLM", "").lower() in ("1", "true", "yes")
            and os.getenv("OPENAI_API_KEY"))


# ----------------------------- LLM backend -----------------------------

def _llm_rank(product, candidates):
    from openai import OpenAI
    client = OpenAI()

    cand_payload = [{
        "code": c["code"],
        "official_description": c["description"],
        "source": f"{c['code']} — {c['description']}",
    } for c in candidates]

    product_payload = {
        "sku": product.get("sku"),
        "product_description": product.get("description"),
        "material_composition": product.get("material"),
        "country_of_origin": product.get("origin"),
        "intended_use": product.get("intended_use"),
        "current_hs_code": product.get("current_hs_code"),
    }

    resp = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "gpt-4.1-mini"),
        response_format={"type": "json_object"},
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "PRODUCT:\n" + json.dumps(product_payload)},
            {"role": "user", "content": "RETRIEVED_HTS_CANDIDATES:\n" + json.dumps(cand_payload)},
        ],
    )
    return json.loads(resp.choices[0].message.content)


def _validate(data, candidates):
    """Hard gate: drop any code the LLM returned that isn't in the candidate set."""
    valid = {c["code"] for c in candidates}
    desc_by_code = {c["code"]: c["description"] for c in candidates}

    out = []
    for c in (data.get("candidates") or []):
        code = c.get("code")
        if code in valid:
            out.append({
                "code": code,
                "confidence": c.get("confidence") or data.get("confidence") or "medium",
                "reason": c.get("reason", ""),
                "source": c.get("source") or f"{code} — {desc_by_code[code]}",
            })
    out = out[:3]

    final = data.get("final")
    if final not in valid:
        final = out[0]["code"] if out else None

    confidence = data.get("confidence") or (out[0]["confidence"] if out else "low")
    needs_review = bool(data.get("needs_manual_review")) or not out or final is None

    return {"candidates": out, "final": final,
            "confidence": confidence, "needs_manual_review": needs_review}


# ----------------------------- mock backend -----------------------------

def _confidence(top_score, runner_up_score):
    if top_score == 0:
        return "low"
    if runner_up_score == top_score:   # ambiguous tie
        return "medium"
    return "high" if top_score >= 4 else "medium"


def _mock_rank(product, candidates):
    desc_tokens = tokenize(product.get("description"))
    mat_tokens = tokenize(product.get("material"))

    scored = []
    for c in candidates:
        keywords = set(c["keywords"])
        desc_overlap = desc_tokens & keywords
        score = len(desc_overlap) * 2          # description is primary signal
        if desc_overlap and (mat_tokens & keywords):
            score += 1                          # material reinforces a real match
        scored.append((score, sorted(desc_overlap), c))

    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored or scored[0][0] == 0:
        return {"candidates": [], "final": None,
                "confidence": "low", "needs_manual_review": True}

    top = scored[:3]
    runner_up = top[1][0] if len(top) > 1 else 0
    confidence = _confidence(top[0][0], runner_up)

    out = []
    for score, overlap, c in top:
        attrs = ", ".join(overlap) if overlap else "the product description"
        out.append({
            "code": c["code"],
            "confidence": confidence,
            "reason": f"Product attributes ({attrs}) align with the HS heading text "
                      f"“{c['description']}”.",
            "source": f"HS {c['code']} — {c['description']}",
        })

    return {"candidates": out, "final": top[0][2]["code"],
            "confidence": confidence, "needs_manual_review": confidence == "low"}
