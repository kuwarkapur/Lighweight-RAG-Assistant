import numpy as np
from huggingface_hub import InferenceClient

from src.config import HF_EMBEDDING_MODEL, HF_TOKEN


class Embedder:
    """Compute embeddings via Hugging Face Inference API."""

    def __init__(self, model: str | None = None, token: str | None = None):
        self.model = model or HF_EMBEDDING_MODEL
        self.client = InferenceClient(token=token or HF_TOKEN or None)

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings = []
        for text in texts:
            result = self.client.feature_extraction(text, model=self.model)
            arr = np.array(result, dtype=np.float32)
            # Mean-pool token embeddings if output is 2D
            if arr.ndim == 2:
                vec = arr.mean(axis=0)
            elif arr.ndim == 3:
                vec = arr.mean(axis=1).squeeze()
            else:
                vec = arr
            embeddings.append(vec.tolist())

        return embeddings

    def embed_query(self, query: str) -> list[float]:
        return self.embed([query])[0]
