"""
Recuperacion puntual: reconstruye index/books.index a partir de index/metadata.json
ya existente, sin volver a leer los PDFs de libros/. Usa el mismo modelo y el mismo
prefijo "passage: {book}: {text}" que ingest.py.

Guarda progreso parcial cada CHECKPOINT_EVERY chunks: si el proceso se corta,
queda un books.index valido y usable (cubre los primeros libros procesados,
en vez de nada). El orden de metadata.json determina que libros quedan
cubiertos primero — ver ingest.py, itera libros en el orden que devuelve
os.listdir(LIBROS_DIR).

Ejecutar: venv/Scripts/python.exe rebuild_index_from_metadata.py
"""

import json
import os
import sys

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_DIR = os.path.join(os.path.dirname(__file__), "index")
INDEX_PATH = os.path.join(INDEX_DIR, "books.index")
META_PATH = os.path.join(INDEX_DIR, "metadata.json")

MODEL_NAME = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
BATCH_SIZE = 256
CHECKPOINT_EVERY = 10_000  # chunks


def main():
    with open(META_PATH, encoding="utf-8") as f:
        metadata = json.load(f)

    total = len(metadata)
    print(f"[MEDI-IA] Chunks en metadata.json: {total}", flush=True)
    print(f"[MEDI-IA] Cargando modelo de embeddings: {MODEL_NAME}", flush=True)
    model = SentenceTransformer(MODEL_NAME)

    passages = [f"passage: {m['book']}: {m['text']}" for m in metadata]

    all_embeddings = []
    done = 0
    last_checkpoint = 0

    print("[MEDI-IA] Generando embeddings...", flush=True)
    for i in range(0, total, BATCH_SIZE):
        batch = passages[i : i + BATCH_SIZE]
        emb = model.encode(batch, show_progress_bar=False, normalize_embeddings=True)
        all_embeddings.append(emb)
        done += len(batch)

        pct = done / total * 100
        print(f"    Progreso: {done}/{total} ({pct:.1f}%)", flush=True)

        if done - last_checkpoint >= CHECKPOINT_EVERY or done == total:
            matrix = np.vstack(all_embeddings).astype("float32")
            dim = matrix.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(matrix)
            faiss.write_index(index, INDEX_PATH)
            last_checkpoint = done
            print(f"[MEDI-IA] Checkpoint guardado: {done}/{total} chunks en {INDEX_PATH}", flush=True)

    print(f"[OK] Indice FAISS final guardado: {INDEX_PATH}", flush=True)
    print(f"[OK] Vectores indexados: {done}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[MEDI-IA] Interrumpido — el ultimo checkpoint guardado sigue siendo valido.", flush=True)
        sys.exit(1)
