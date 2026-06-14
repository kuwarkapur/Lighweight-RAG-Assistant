#!/usr/bin/env python3
"""Build or rebuild the vector index from sample documents."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.chunker import chunk_documents
from scripts.loaders import load_documents
from src.retrieval.vector_store import VectorStore


def main() -> None:
    print("Loading documents...")
    documents = load_documents()
    print(f"  Loaded {len(documents)} document(s)")

    print("Chunking...")
    chunks = chunk_documents(documents)
    print(f"  Created {len(chunks)} chunk(s)")

    print("Indexing into ChromaDB (HF cloud embeddings)...")
    store = VectorStore()
    store.clear()
    added = store.add_chunks(chunks)
    print(f"  Indexed {added} chunk(s)")
    print(f"  Sources: {', '.join(store.list_sources())}")
    print("Done.")


if __name__ == "__main__":
    main()
