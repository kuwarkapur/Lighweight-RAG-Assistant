import re

from src.config import CONTEXT_SCORE_FLOOR, LLM_CONTEXT_MAX, TOP_K

WORKFLOW_PATTERN = re.compile(
    r"\b(workflow|process|steps|procedure|approval|escalation)\b", re.I
)


def _is_workflow_question(question: str) -> bool:
    return bool(WORKFLOW_PATTERN.search(question))


def filter_hits_for_context(
    hits: list[dict],
    question: str = "",
    score_floor: float = CONTEXT_SCORE_FLOOR,
    max_chunks: int | None = None,
    min_chunks: int = 1,
) -> list[dict]:
    """Filter low-score hits and cap context size.

    Workflow/process questions allow more chunks from the same document so
    multi-step policies (e.g. procurement Steps 1-6) are not collapsed to one hit.
    """
    if not hits:
        return []

    cap = max_chunks or (5 if _is_workflow_question(question) else LLM_CONTEXT_MAX)

    filtered = [h for h in hits if h["score"] >= score_floor]
    if len(filtered) < min_chunks:
        filtered = hits[: max(min_chunks, len(hits))]

    # Keep unique chunks by (file, chunk_id); do NOT collapse to one chunk per file
    seen: set[tuple[str, int]] = set()
    result: list[dict] = []
    for h in sorted(filtered, key=lambda x: x["score"], reverse=True):
        key = (h["source_file"], h["chunk_id"])
        if key in seen:
            continue
        seen.add(key)
        result.append(h)
        if len(result) >= cap:
            break

    return result


def filter_hits_for_display(hits: list[dict], top_k: int = TOP_K) -> list[dict]:
    """Return top-k hits for UI source panel (unfiltered by score floor)."""
    return hits[:top_k]
