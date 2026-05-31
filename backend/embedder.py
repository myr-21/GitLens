"""
embedder.py — BERT embedding logic using sentence-transformers (all-MiniLM-L6-v2).

Loads the model once at import time and exposes helper functions
for generating single or batch embeddings as numpy arrays.
"""
from __future__ import annotations

import logging
from typing import List

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Model singleton — loaded once, reused forever
# ---------------------------------------------------------------------------
_model = None
MODEL_NAME = "all-MiniLM-L6-v2"


def _get_model():
    """Lazily load the sentence-transformer model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            logger.info("Loading sentence-transformer model: %s", MODEL_NAME)
            _model = SentenceTransformer(MODEL_NAME)
            logger.info("Model loaded successfully.")
        except Exception as exc:
            logger.error("Failed to load sentence-transformer model: %s", exc)
            raise
    return _model


def embed_text(text: str) -> np.ndarray:
    """
    Generate a BERT embedding for a single text string.

    Returns:
        numpy array of shape (384,)  — all-MiniLM-L6-v2 dimension
    """
    model = _get_model()
    embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    return embedding.astype(np.float32)


def embed_texts(texts: List[str]) -> np.ndarray:
    """
    Generate BERT embeddings for a list of strings (batch).

    Returns:
        numpy array of shape (N, 384)
    """
    model = _get_model()
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=False,
    )
    return embeddings.astype(np.float32)
