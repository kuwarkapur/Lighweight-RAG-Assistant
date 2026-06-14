"""Basic streamlit UI for the RAG assistant."""

import subprocess
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.config import HF_TOKEN
from src.pipeline import RAGPipeline

st.set_page_config(page_title="Business Knowledge Assistant", page_icon="📚", layout="wide")

CONFIDENCE_COLORS = {
    "high": "🟢",
    "medium": "🟡",
    "low": "🟠",
    "abstain": "🔴",
}


@st.cache_resource
def get_pipeline() -> RAGPipeline:
    return RAGPipeline()


def run_ingest() -> str:
    result = subprocess.run(
        [sys.executable or "python3", "scripts/ingest.py"],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).resolve().parent),
    )
    if result.returncode != 0:
        return f"Ingest failed:\n{result.stderr}"
    get_pipeline.cache_clear()
    return result.stdout or "Ingest complete."


def main() -> None:
    st.title("Business Knowledge Assistant")
    st.caption("Grounded answers from policies, SOPs, emails, and operational CSV data.")

    with st.sidebar:
        st.header("Settings")
        if not HF_TOKEN:
            st.warning("Set `HF_TOKEN` in `.env` for cloud model access.")
        else:
            st.success("HF_TOKEN configured")

        pipeline = get_pipeline()
        st.subheader("Indexed sources")
        for src in pipeline.list_sources():
            st.text(f"• {src}")

        if st.button("Rebuild index"):
            with st.spinner("Indexing documents via HF cloud embeddings..."):
                output = run_ingest()
            st.code(output)
            st.rerun()

        st.divider()
        st.markdown("**Example questions**")
        examples = [
            "What is the escalation process for delayed shipments?",
            "What is the approval workflow for procurement requests?",
            "Explain the inventory aging KPI.",
            "Which branch has the highest sales?",
            "What is the average inventory aging?",
            "Show top 5 SKUs by aging days.",
            "Why is the report bad?",
            "What is the CEO's salary?",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{hash(ex)}"):
                st.session_state["pending_question"] = ex

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("confidence"):
                badge = CONFIDENCE_COLORS.get(msg["confidence"], "⚪")
                st.caption(f"{badge} Confidence: **{msg['confidence']}** | Type: {msg.get('query_type', 'n/a')}")
            if msg.get("sources"):
                with st.expander("Sources"):
                    for i, src in enumerate(msg["sources"], 1):
                        st.markdown(f"**{i}. {src['file']}** (score: {src.get('score', 'n/a')})")
                        st.text(src.get("snippet", "")[:500])

    pending = st.session_state.pop("pending_question", None)
    question = pending or st.chat_input("Ask a question about policies, processes, or inventory data...")

    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                pipeline = get_pipeline()
                response = pipeline.ask(question)

            st.markdown(response.answer)
            badge = CONFIDENCE_COLORS.get(response.confidence, "⚪")
            st.caption(
                f"{badge} Confidence: **{response.confidence}** | Type: {response.query_type}"
            )

            if response.sources:
                with st.expander("Sources"):
                    for i, src in enumerate(response.sources, 1):
                        st.markdown(
                            f"**{i}. {src['file']}** (score: {src.get('score', 'n/a')})"
                        )
                        st.text(src.get("snippet", "")[:500])

        st.session_state.messages.append(
            {
                "role": "assistant",
                "content": response.answer,
                "sources": response.sources,
                "confidence": response.confidence,
                "query_type": response.query_type,
            }
        )


if __name__ == "__main__":
    main()
