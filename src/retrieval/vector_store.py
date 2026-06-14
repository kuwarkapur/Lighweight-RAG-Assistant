import uuid
from pathlib import Path

import chromadb
from chromadb.config import Settings

from src.config import CHROMA_DIR, TOP_K
from src.retrieval.embedder import Embedder


def _build_embed_text(chunk: dict) -> str:
    section = chunk.get("section_title", "Introduction")
    return f"Document: {chunk['source_file']}\nSection: {section}\n\n{chunk['text']}"


class VectorStore:
    """ChromaDB wrapper for document chunk storage and similarity search."""

    def __init__(self, persist_dir: Path | None = None, embedder: Embedder | None = None):
        self.persist_dir = persist_dir or CHROMA_DIR
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embedder = embedder or Embedder()
        self._client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        return self._collection.count()

    def clear(self) -> None:
        self._client.delete_collection("documents")
        self._collection = self._client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[dict]) -> int:
        if not chunks:
            return 0

        embed_texts = [_build_embed_text(c) for c in chunks]
        embeddings = self.embedder.embed(embed_texts)
        ids = [str(uuid.uuid4()) for _ in chunks]

        metadatas = []
        for c in chunks:
            meta = {
                "source_file": c["source_file"],
                "chunk_id": str(c["chunk_id"]),
                "section_title": c.get("section_title", "Introduction"),
            }
            if c.get("page") is not None:
                meta["page"] = str(c["page"])
            metadatas.append(meta)

        self._collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=embed_texts,
            metadatas=metadatas,
        )
        return len(chunks)

    def search(self, query: str, top_k: int = TOP_K) -> list[dict]:
        if self.count == 0:
            return []

        query_embedding = self.embedder.embed_query(query)
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.count),
            include=["documents", "metadatas", "distances"],
        )

        hits: list[dict] = []
        if not results["ids"] or not results["ids"][0]:
            return hits

        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i] if results["distances"] else 1.0
            similarity = max(0.0, 1.0 - distance)
            meta = results["metadatas"][0][i] if results["metadatas"] else {}
            hits.append(
                {
                    "id": doc_id,
                    "text": results["documents"][0][i],
                    "source_file": meta.get("source_file", "unknown"),
                    "chunk_id": int(meta.get("chunk_id", 0)),
                    "section_title": meta.get("section_title", ""),
                    "page": meta.get("page"),
                    "score": round(similarity, 4),
                }
            )

        return hits

    def list_sources(self) -> list[str]:
        if self.count == 0:
            return []
        all_meta = self._collection.get(include=["metadatas"])
        sources = set()
        for meta in all_meta.get("metadatas") or []:
            if meta and "source_file" in meta:
                sources.add(meta["source_file"])
        return sorted(sources)
