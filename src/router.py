import re

from src.structured.csv_analyzer import CSVAnalyzer

structured_keywords = {
    "sales", "branch", "branches", "average", "mean", "top", "sku", "skus",
    "aging", "highest", "lowest", "inventory",
}

document_phrases = (
    "exceeded",
    "threshold",
    "which branches",
    "who is responsible",
    "workflow",
    "approval workflow",
    "escalation process",
    "explain the",
)

vague_terms = {"bad", "wrong", "issue", "issues", "problem", "problems", "terrible", "awful"}
entity_terms = {
    "report", "shipment", "shipments", "inventory", "procurement", "purchase",
    "order", "kpi", "policy", "sop", "branch", "sku", "sales", "aging",
}


def is_document_style_question(question: str) -> bool:
    q_lower = question.lower()
    return any(phrase in q_lower for phrase in document_phrases)


def route_query(question: str, csv_analyzer: CSVAnalyzer) -> str:
    """Return 'structured', 'clarify', or 'document'."""
    if needs_clarification(question):
        return "clarify"

    if is_document_style_question(question):
        return "document"

    if csv_analyzer.can_answer(question):
        return "structured"

    q_lower = question.lower()
    words = set(re.findall(r"\b\w+\b", q_lower))
    if len(words & structured_keywords) >= 2 and any(
        w in q_lower for w in ("branch", "sku", "sales", "aging")
    ):
        return "structured"

    return "document"


def needs_clarification(question: str) -> bool:
    q = question.strip().lower()
    words = q.split()
    word_set = set(re.findall(r"\b\w+\b", q))

    has_vague = bool(word_set & vague_terms)
    has_entity = bool(word_set & entity_terms)

    if has_vague and not has_entity:
        return True

    if len(words) < 6 and has_vague:
        return True

    if has_vague and "report" in word_set and len(words) < 10:
        return True

    return False


def build_clarification(question: str) -> str:
    q = question.lower()
    if "report" in q:
        return (
            "Which report are you referring to, and what is your main concern"
            "(accuracy, completeness, timeliness, or performance)? "
            "Please also tell us the timeframe if relevant."
        )
    if any(w in q for w in ("bad", "wrong", "problem", "issue")):
        return (
            "Could you specify what you're asking about (e.g., a shipment, report, "
            "inventory metric, or procurement request) and what is incorrect?"
        )
    return (
        "Your question is quite vague. Could you provide more context about "
        "which document, process, or data you need help with?"
    )
