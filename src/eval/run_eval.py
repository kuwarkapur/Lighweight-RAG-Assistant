"""Evaluating the RAG assistant."""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.pipeline import RAGPipeline
from src.structured.csv_analyzer import CSVAnalyzer

citation_pattern = re.compile(r"\[Source:", re.I)
test_cases_file = Path(__file__).parent / "test_cases.json"

# Synonym aliases (acceptable alternatives)
Alternatives: dict[str, list[str]] = {
    "requisition": ["pr", "purchase requisition", "purchase request"],
    "approval": ["approve", "approved"],
    "vp": ["vice president"],
    "supply chain": ["supply-chain"],
}


def _normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _term_matches(term: str, answer: str) -> bool:
    norm_answer = _normalize_text(answer)
    norm_term = _normalize_text(term)
    if norm_term in norm_answer:
        return True
    for alias in Alternatives.get(norm_term, []):
        if _normalize_text(alias) in norm_answer:
            return True
    return False


def check_answer_facts(answer: str, case: dict) -> bool | None:
    required_all = case.get("answer_must_contain")
    required_any = case.get("answer_must_contain_any")

    if required_all:
        if not all(_term_matches(term, answer) for term in required_all):
            return False

    if required_any:
        if not any(_term_matches(term, answer) for term in required_any):
            return False

    if required_all or required_any:
        return True

    return None


def load_cases() -> list[dict]:
    with open(test_cases_file, encoding="utf-8") as f:
        return json.load(f)


def check_retrieval(pipeline: RAGPipeline, case: dict) -> tuple[bool | None, dict]:
    if case.get("type") != "document" or not case.get("expected_source"):
        return None, {}

    hits = pipeline.retrieve_only(case["question"])
    expected = case["expected_source"]
    max_rank = case.get("max_expected_rank", len(hits))

    scores = {
        "top_score": hits[0]["score"] if hits else 0.0,
        "expected_source_score": None,
        "expected_source_rank": None,
    }

    for rank, h in enumerate(hits, 1):
        if h["source_file"] == expected:
            scores["expected_source_score"] = h["score"]
            scores["expected_source_rank"] = rank
            in_top_k = True
            within_rank = rank <= max_rank
            return in_top_k and within_rank, scores

    return False, scores


def check_structured(pipeline: RAGPipeline, case: dict) -> bool | None:
    if case.get("type") != "structured":
        return None
    response = pipeline.ask(case["question"])
    expected = case.get("expected_answer_contains", "")
    return expected.lower() in response.answer.lower()


def evaluate_case(pipeline: RAGPipeline, case: dict, retrieval_only: bool = False) -> dict:
    result = {"id": case["id"], "passed": True, "checks": [], "scores": {}}

    if case.get("type") == "structured":
        ok = check_structured(pipeline, case)
        result["checks"].append(("structured_accuracy", ok))
        if not ok:
            result["passed"] = False
        return result

    if case.get("must_clarify"):
        if retrieval_only:
            result["checks"].append(("clarification", None))
            return result
        response = pipeline.ask(case["question"])
        ok = response.clarification or response.query_type == "clarification"
        result["checks"].append(("clarification", ok))
        if not ok:
            result["passed"] = False
        return result

    retrieval_ok, scores = check_retrieval(pipeline, case)
    result["scores"] = scores

    if retrieval_ok is not None:
        result["checks"].append(("retrieval_relevance", retrieval_ok))
        if not retrieval_ok:
            result["passed"] = False

        if case.get("max_expected_rank") and scores.get("expected_source_rank"):
            rank_ok = scores["expected_source_rank"] <= case["max_expected_rank"]
            result["checks"].append(("retrieval_rank", rank_ok))
            if not rank_ok:
                result["passed"] = False

    if retrieval_only:
        return result

    response = pipeline.ask(case["question"])

    if case.get("must_abstain"):
        ok = response.confidence == "abstain" or response.query_type == "blocked"
        result["checks"].append(("abstain", ok))
        if not ok:
            result["passed"] = False
        return result

    if case.get("must_have_citation"):
        ok = bool(citation_pattern.search(response.answer))
        result["checks"].append(("citation_coverage", ok))
        if not ok:
            result["passed"] = False

    facts_ok = check_answer_facts(response.answer, case)
    if facts_ok is not None:
        result["checks"].append(("answer_groundedness", facts_ok))
        if not facts_ok:
            result["passed"] = False

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RAG assistant quality")
    parser.add_argument(
        "--retrieval-only",
        action="store_true",
        help="Run retrieval checks only (skip LLM generation)",
    )
    args = parser.parse_args()

    print("Loading pipeline...")
    pipeline = RAGPipeline()

    if pipeline.vector_store.count == 0:
        print("WARNING: Vector store is empty. Run `python3 scripts/ingest.py` first.")
        print("Retrieval checks will fail without an index.\n")

    cases = load_cases()
    results = []
    passed = 0

    mode = "retrieval-only" if args.retrieval_only else "full"
    print(f"Running {len(cases)} evaluation cases ({mode})...\n")
    print(f"{'ID':<30} {'Status':<8} Checks")
    print("-" * 80)

    for case in cases:
        r = evaluate_case(pipeline, case, retrieval_only=args.retrieval_only)
        results.append(r)
        status = "PASS" if r["passed"] else "FAIL"
        if r["passed"]:
            passed += 1
        checks_str = ", ".join(
            f"{name}={ok}" for name, ok in r["checks"] if ok is not None
        )
        score_str = ""
        if r.get("scores"):
            s = r["scores"]
            if s.get("top_score") is not None:
                score_str = f" | top={s['top_score']:.3f}"
            if s.get("expected_source_rank"):
                score_str += f", rank={s['expected_source_rank']}, exp_score={s['expected_source_score']:.3f}"
        print(f"{r['id']:<30} {status:<8} {checks_str}{score_str}")

    print("-" * 80)
    print(f"Score: {passed}/{len(cases)} ({100 * passed / len(cases):.0f}%)")

    # Print score distribution for threshold calibration
    doc_scores = [
        r["scores"].get("expected_source_score")
        for r in results
        if r.get("scores") and r["scores"].get("expected_source_score") is not None
    ]
    if doc_scores:
        print(f"\nExpected-source score range: {min(doc_scores):.3f} – {max(doc_scores):.3f}")
        print(f"Mean expected-source score: {sum(doc_scores) / len(doc_scores):.3f}")

    out_path = Path(__file__).parent / "eval_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(
            {"passed": passed, "total": len(cases), "mode": mode, "results": results},
            f,
            indent=2,
        )
    print(f"Results saved to {out_path}")


if __name__ == "__main__":
    main()
