import re

from src.config import (
    ABSTAIN_MIN_SCORE_GAP,
    ABSTAIN_WEAK_TOP_SCORE,
    THRESHOLD_HIGH,
    THRESHOLD_LOW,
    THRESHOLD_MEDIUM,
)
from src.generation.prompts import ABSTAIN_MESSAGE

ConfidenceLevel = str  # "high" | "medium" | "low" | "abstain"

CITATION_PATTERN = re.compile(r"\[Source:\s*[^\]]+\]", re.IGNORECASE)


def classify_confidence(max_score: float) -> ConfidenceLevel:
    if max_score >= THRESHOLD_HIGH:
        return "high"
    if max_score >= THRESHOLD_MEDIUM:
        return "medium"
    if max_score >= THRESHOLD_LOW:
        return "low"
    return "abstain"


def should_abstain(hits: list[dict] | float) -> bool:
    """Return True when retrieval evidence is too weak or ambiguous to answer."""
    if isinstance(hits, (int, float)):
        return classify_confidence(float(hits)) == "abstain"

    if not hits:
        return True

    max_score = hits[0]["score"]
    if classify_confidence(max_score) == "abstain":
        return True

    # Ambiguous retrieval: weak top score with no clear winner
    if max_score < ABSTAIN_WEAK_TOP_SCORE and len(hits) > 1:
        gap = hits[0]["score"] - hits[1]["score"]
        if gap < ABSTAIN_MIN_SCORE_GAP:
            return True

    return False


def enforce_citations(answer: str, chunks: list[dict], confidence: ConfidenceLevel) -> str:
    """Ensure factual answers include at least one citation when evidence exists."""
    if confidence == "abstain":
        return ABSTAIN_MESSAGE

    if not chunks:
        return ABSTAIN_MESSAGE

    if CITATION_PATTERN.search(answer):
        return answer

    refs = []
    seen = set()
    for c in chunks[:3]:
        key = (c["source_file"], c["chunk_id"])
        if key not in seen:
            seen.add(key)
            refs.append(f"[Source: {c['source_file']}, chunk {c['chunk_id']}]")

    if refs:
        return answer + "\n\nSources used: " + " ".join(refs)

    return answer
