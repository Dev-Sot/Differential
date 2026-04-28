"""
MEDI-IA Ingestion Pipeline
Lee PDFs médicos, los divide en chunks, genera embeddings y construye un índice FAISS.
Ejecutar: python ingest.py
"""

import os
import json
import sys
import fitz  # PyMuPDF
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

LIBROS_DIR = os.path.join(os.path.dirname(__file__), "libros")
INDEX_DIR = os.path.join(os.path.dirname(__file__), "index")
INDEX_PATH = os.path.join(INDEX_DIR, "books.index")
META_PATH = os.path.join(INDEX_DIR, "metadata.json")

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # ~400MB, español + inglés
CHUNK_SIZE = 400   # caracteres por chunk (aprox 80-100 tokens)
CHUNK_OVERLAP = 80 # solapamiento entre chunks


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """Extrae texto página por página de un PDF."""
    pages = []
    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text").strip()
            if len(text) > 50:  # ignorar páginas casi vacías
                pages.append({"page": page_num + 1, "text": text})
        doc.close()
    except Exception as e:
        print(f"  [ERROR] No se pudo leer {pdf_path}: {e}")
    return pages


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide texto en chunks con solapamiento."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if len(chunk) > 50:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def ingest_all_books():
    os.makedirs(INDEX_DIR, exist_ok=True)

    pdf_files = [f for f in os.listdir(LIBROS_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("[ERROR] No se encontraron PDFs en libros/")
        sys.exit(1)

    print(f"[MEDI-IA] Cargando modelo de embeddings: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    all_chunks = []    # textos
    all_metadata = []  # info de origen

    for pdf_file in pdf_files:
        pdf_path = os.path.join(LIBROS_DIR, pdf_file)
        book_name = os.path.splitext(pdf_file)[0]
        print(f"\n[>>] Procesando: {pdf_file}")

        pages = extract_text_from_pdf(pdf_path)
        print(f"    Páginas con texto: {len(pages)}")

        book_chunks = 0
        for page_data in pages:
            chunks = chunk_text(page_data["text"])
            for chunk in chunks:
                all_chunks.append(chunk)
                all_metadata.append({
                    "book": book_name,
                    "page": page_data["page"],
                    "text": chunk
                })
                book_chunks += 1

        print(f"    Chunks generados: {book_chunks}")

    print(f"\n[MEDI-IA] Total chunks: {len(all_chunks)}")
    print(f"[MEDI-IA] Generando embeddings... (puede tomar varios minutos)")

    batch_size = 64
    all_embeddings = []
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        embeddings = model.encode(batch, show_progress_bar=False, normalize_embeddings=True)
        all_embeddings.append(embeddings)
        pct = min(100, int((i + batch_size) / len(all_chunks) * 100))
        print(f"    Progreso: {pct}%", end="\r")

    print()
    embeddings_matrix = np.vstack(all_embeddings).astype("float32")

    dim = embeddings_matrix.shape[1]
    index = faiss.IndexFlatIP(dim)  # Inner Product = cosine similarity con vectores normalizados
    index.add(embeddings_matrix)

    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(all_metadata, f, ensure_ascii=False, indent=2)

    print(f"[OK] Indice FAISS guardado: {INDEX_PATH}")
    print(f"[OK] Metadata guardada:     {META_PATH}")
    print(f"[OK] Vectores indexados:    {index.ntotal}")
    print(f"\n[MEDI-IA] Ingesta completada. El sistema usara los libros medicos reales.")


if __name__ == "__main__":
    ingest_all_books()
