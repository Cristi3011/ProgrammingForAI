"""Adapter around the pretrained sentence-transformer model."""
from __future__ import annotations

import numpy as np


class SentenceTransformerEncoder:
    """Load the pretrained encoder only when encoding is first requested."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self._model = None

    def _get_model(self):
        if self._model is None:
            # Import here so pure retrieval tests do not need to load the ML stack.
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name, device="cpu")
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        """Encode texts on CPU and return normalized float32 embeddings."""
        model = self._get_model()
        vectors = model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)