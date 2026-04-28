"""
Singleton para el modelo de embeddings.
Carga una sola vez y reutiliza en todo el sistema.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

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
    return model.encode(texts, normalize_embeddings=normalize, show_progress_bar=False).astype("float32")
