from hs_data import HS_DATA
from text_utils import tokenize

# Stage 1: broad candidate retrieval (optimize for RECALL).
# Return any HS line that shares at least one keyword with the product text,
# ranked by overlap count. The ranker refines from here.


def retrieve_candidates(description, material=None, top_k=15):
    query_tokens = tokenize(description) | tokenize(material or "")
    scored = []

    for item in HS_DATA:
        keywords = set(item["keywords"])
        overlap = query_tokens & keywords
        if overlap:
            scored.append((len(overlap), item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]
