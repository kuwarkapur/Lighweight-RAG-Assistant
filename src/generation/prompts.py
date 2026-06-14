import re

SYSTEM_PROMPT = """You are a business knowledge assistant. Answer questions using ONLY the provided context.

Rules:
1. Synthesize a concise answer in your own words. Never copy, quote, or repeat context block headers or raw excerpts.
2. Base every factual claim on the context. Do not use outside knowledge.
3. Cite sources inline using [Source: filename, chunk N] after each claim or step.
4. Use only context blocks that directly support your answer; ignore irrelevant blocks.
5. If no block fully answers the question, state what is missing — do not guess.
6. Do not invent policies, numbers, names, or processes not present in the context.
7. Use exact role names, policy terms, and KPI labels from the source documents."""

WORKFLOW_INSTRUCTIONS = """Using only the provided context:

- Summarize the workflow as a numbered list.
- Include only steps explicitly present in the sources.
- Do not invent additional workflow levels, approvers, or escalation stages.
- Stop after the last documented step.
- Cite each step using [Source: filename, chunk N].
"""

GENERAL_INSTRUCTIONS = """Format your answer as follows:
- Write 1–3 concise paragraphs that directly answer the question.
- Synthesize facts from the context; do not paste or paraphrase entire context blocks verbatim.
- Add an inline citation [Source: filename, chunk N] after each key claim."""

WORKFLOW_QUERY_PATTERN = re.compile(
    r"\b(workflow|process|steps|procedure|approval|escalation)\b", re.I
)

UNCERTAINTY_PREFIX = {
    "medium": (
        "Note: I found partially relevant information. My confidence is moderate — "
        "please verify critical details.\n\n"
    ),
    "low": (
        "Note: Evidence is weak. I can only share limited information from available sources. "
        "Key details may be missing.\n\n"
    ),
}


def is_workflow_question(question: str) -> bool:
    return bool(WORKFLOW_QUERY_PATTERN.search(question))


def build_context_block(chunks: list[dict]) -> str:
    blocks = []
    for i, c in enumerate(chunks, 1):
        score = c.get("score", "n/a")
        section = c.get("section_title", "")
        section_label = f" | {section}" if section else ""
        label = f"[{i}] {c['source_file']}, chunk {c['chunk_id']}{section_label} (score: {score})"
        blocks.append(f"--- {label} ---\n{c['text']}")
    return "\n\n".join(blocks)


def build_user_prompt(question: str, chunks: list[dict]) -> str:
    context = build_context_block(chunks)
    format_instructions = (
        WORKFLOW_INSTRUCTIONS if is_workflow_question(question) else GENERAL_INSTRUCTIONS
    )
    return f"""Reference material (for your use only — do not copy into the answer):
{context}

Question: {question}

{format_instructions}

Write only the final answer below. Do not include context headers, "Document:" lines, or raw excerpts.

Answer:"""


ABSTAIN_MESSAGE = (
    "I don't have enough relevant information in the available documents to answer "
    "this question reliably. Please try rephrasing your question or ask about topics "
    "covered in our policies, SOPs, or operational data."
)

CLARIFICATION_TEMPLATE = (
    "Your question seems ambiguous. Could you clarify: {details}"
)
