import re

# Minimal stopwords so generic words don't create false matches.
STOPWORDS = {
    "the", "a", "an", "of", "for", "with", "and", "or", "in", "on", "to",
    "made", "new", "set", "pack", "pcs", "pc", "size", "color", "colour",
}


def _singular(t):
    """Crude singularization so plurals match keywords (shirts->shirt)."""
    if t.endswith("ies") and len(t) > 4:
        return t[:-3] + "y"
    if t.endswith(("ches", "shes", "xes", "zes", "ses")):
        return t[:-2]
    if t.endswith("s") and not t.endswith("ss") and len(t) > 3:
        return t[:-1]
    return t


def tokenize(text):
    """Lowercase, split on non-letters, drop stopwords/short tokens, add singulars."""
    if not text:
        return set()
    tokens = {t for t in re.findall(r"[a-z]+", text.lower())
              if len(t) > 2 and t not in STOPWORDS}
    return tokens | {_singular(t) for t in tokens}
