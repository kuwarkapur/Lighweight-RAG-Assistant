from dataclasses import dataclass, field

import re

from src.config import TOP_K, TOP_K_WORKFLOW
from src.generation.llm import DEFAULT_MAX_TOKENS, LLMClient
from src.generation.prompts import (
    ABSTAIN_MESSAGE,
    UNCERTAINTY_PREFIX,
    build_user_prompt,
    is_workflow_question,
)
from src.guardrails.injection_detector import detect_prompt_injection
from src.guardrails.pii_masker import mask_pii
from src.guardrails.retrieval_threshold import (
    classify_confidence,
    enforce_citations,
    should_abstain,
)
from src.retrieval.postprocess import filter_hits_for_context, filter_hits_for_display
from src.retrieval.vector_store import VectorStore
from src.router import build_clarification, route_query
from src.structured.csv_analyzer import CSVAnalyzer

OUT_OF_DOMAIN_PATTERN = re.compile(
    r"\b(salary|bake|baking|recipe|chocolate cake|cook)\b", re.I
)
WORKFLOW_QUERY_PATTERN = re.compile(
    r"\b(workflow|process|steps|procedure|approval|escalation)\b", re.I
)


@dataclass
class PipelineResponse:
    answer: str
    sources: list[dict] = field(default_factory=list)
    confidence: str = "high"
    query_type: str = "document"
    clarification: bool = False


class RAGPipeline:
    def __init__(
        self,
        vector_store: VectorStore | None = None,
        llm: LLMClient | None = None,
        csv_analyzer: CSVAnalyzer | None = None,
    ):
        self.vector_store = vector_store or VectorStore()
        self.llm = llm or LLMClient()
        self.csv_analyzer = csv_analyzer or CSVAnalyzer()

    def ask(self, question: str) -> PipelineResponse:
        is_injection, block_msg = detect_prompt_injection(question)
        if is_injection:
            return PipelineResponse(
                answer=block_msg,
                confidence="abstain",
                query_type="blocked",
            )

        route = route_query(question, self.csv_analyzer)

        if route == "clarify":
            return PipelineResponse(
                answer=build_clarification(question),
                confidence="medium",
                query_type="clarification",
                clarification=True,
            )

        if route == "structured":
            result = self.csv_analyzer.answer(question)
            if result:
                return PipelineResponse(
                    answer=result["answer"],
                    sources=result["sources"],
                    confidence=result["confidence"],
                    query_type="structured",
                )

        return self._document_query(question)

    def _document_query(self, question: str) -> PipelineResponse:
        if self.vector_store.count == 0:
            return PipelineResponse(
                answer=(
                    "The document index is empty. Please run "
                    "`python3 scripts/ingest.py` to index documents first."
                ),
                confidence="abstain",
                query_type="document",
            )

        top_k = TOP_K_WORKFLOW if WORKFLOW_QUERY_PATTERN.search(question) else TOP_K
        hits = self.vector_store.search(question, top_k=top_k)
        max_score = hits[0]["score"] if hits else 0.0
        confidence = classify_confidence(max_score)

        if OUT_OF_DOMAIN_PATTERN.search(question):
            return PipelineResponse(
                answer=ABSTAIN_MESSAGE,
                sources=[],
                confidence="abstain",
                query_type="document",
            )

        if should_abstain(hits):
            return PipelineResponse(
                answer=ABSTAIN_MESSAGE,
                sources=[],
                confidence="abstain",
                query_type="document",
            )

        context_hits = filter_hits_for_context(hits, question=question)
        display_hits = filter_hits_for_display(hits, top_k=top_k)

        sources = [
            {
                "file": h["source_file"],
                "snippet": mask_pii(h["text"][:400]),
                "score": h["score"],
                "chunk_id": h["chunk_id"],
            }
            for h in display_hits
        ]

        user_prompt = build_user_prompt(question, context_hits)
        max_tokens = 384 if is_workflow_question(question) else DEFAULT_MAX_TOKENS
        raw_answer = self.llm.generate(user_prompt, max_tokens=max_tokens)

        answer = enforce_citations(raw_answer, context_hits, confidence)

        if confidence in UNCERTAINTY_PREFIX:
            answer = UNCERTAINTY_PREFIX[confidence] + answer

        return PipelineResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            query_type="document",
        )

    def retrieve_only(self, question: str) -> list[dict]:
        """Expose retrieval for evaluation."""
        return self.vector_store.search(question)

    def list_sources(self) -> list[str]:
        doc_sources = self.vector_store.list_sources()
        csv_name = self.csv_analyzer.csv_path.name
        if csv_name not in doc_sources:
            doc_sources.append(csv_name)
        return sorted(doc_sources)
