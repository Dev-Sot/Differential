"""
Singleton para el modelo de embeddings.
Carga una sola vez y reutiliza en todo el sistema.

Modelo activo: intfloat/multilingual-e5-base (768 dims, retrieval-optimized)
  - Requiere prefijo "query: " para queries — lo agrega encode() automáticamente
  - Requiere prefijo "passage: {libro}: {texto}" en ingesta — lo agrega ingest.py
  - Si cambias MODEL_NAME debes re-ingestar: make ingest
"""

import os
import numpy as np
from sentence_transformers import SentenceTransformer

# Permite sobreescribir via variable de entorno para pruebas
MODEL_NAME = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")

_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        print(f"[Embeddings] Cargando modelo: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        print("[Embeddings] Modelo listo.")
    return _model


def encode(texts: list[str], normalize: bool = True) -> np.ndarray:
    model = get_model()
    # e5-base requiere prefijo "query: " en búsquedas (vs "passage: " en ingesta)
    prefixed = [f"query: {t}" for t in texts]
    return model.encode(prefixed, normalize_embeddings=normalize, show_progress_bar=False).astype("float32")
