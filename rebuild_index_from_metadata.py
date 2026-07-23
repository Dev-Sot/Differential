"""
Recuperacion puntual: reconstruye index/books.index a partir de index/metadata.json
ya existente, sin volver a leer los PDFs de libros/. Usa el mismo modelo y el mismo
prefijo "passage: {book}: {text}" que ingest.py.

Ejecutar una sola vez: venv/Scripts/python.exe rebuild_index_from_metadata.py
"""

import json
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_DIR = os.path.join(os.path.dirname(__file__), "index")
INDEX_PATH = os.path.join(INDEX_DIR, "books.index")
META_PATH = os.path.join(INDEX_DIR, "metadata.json")

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")


def main():
    with open(META_PATH, encoding="utf-8") as f:
        metadata = json.load(f)

    print(f"[MEDI-IA] Chunks en metadata.json: {len(metadata)}")
    print(f"[MEDI-IA] Cargando modelo de embeddings: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    passages = [f"passage: {m['book']}: {m['text']}" for m in metadata]

    print("[MEDI-IA] Generando embeddings... (puede tomar varios minutos)")
    batch_size = 256
    all_embeddings = []
    for i in range(0, len(passages), batch_size):
        batch = passages[i:i + batch_size]
        embeddings = model.encode(batch, show_progress_bar=False, normalize_embeddings=True)
        all_embeddings.append(embeddings)
        pct = min(100, int((i + batch_size) / len(passages) * 100))
        print(f"    Progreso: {pct}%", end="\r")

    print()
    embeddings_matrix = np.vstack(all_embeddings).astype("float32")

    dim = embeddings_matrix.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings_matrix)

    faiss.write_index(index, INDEX_PATH)

    print(f"[OK] Indice FAISS reconstruido: {INDEX_PATH}")
    print(f"[OK] Vectores indexados: {index.ntotal}")


if __name__ == "__main__":
    main()
