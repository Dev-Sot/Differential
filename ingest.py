"""
MEDI-IA Ingestion Pipeline
Lee PDFs médicos, los divide en chunks, genera embeddings y construye un índice FAISS.
Ejecutar: python ingest.py
"""

import os
import re
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

import os as _os
MODEL_NAME = _os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
CHUNK_SIZE = 600    # subido de 400 — más contexto clínico por chunk
CHUNK_OVERLAP = 120  # subido de 80

_SENT_RE = re.compile(r'(?<=[.?!])\s+|\n{2,}')


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


def _split_sentences(text: str) -> list[str]:
    """Divide texto en oraciones respetando puntuación y saltos de línea."""
    parts = _SENT_RE.split(text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Divide texto en chunks respetando límites de oración con solapamiento."""
    sentences = _split_sentences(text)
    if not sentences:
        return []

    chunks = []
    window: list[str] = []
    window_len = 0

    for sent in sentences:
        slen = len(sent)
        gap = 1 if window else 0

        if window_len + gap + slen > chunk_size and window:
            chunk = " ".join(window)
            if len(chunk) > 50:
                chunks.append(chunk)

            # Retener cola del window para solapamiento
            tail: list[str] = []
            tail_len = 0
            for s in reversed(window):
                if tail_len + len(s) + 1 > overlap:
                    break
                tail.insert(0, s)
                tail_len += len(s) + 1
            window = tail
            window_len = tail_len

        if slen > chunk_size:
            # Oración mayor que chunk_size — vaciar window y agregar truncada
            if window:
                chunk = " ".join(window)
                if len(chunk) > 50:
                    chunks.append(chunk)
                window = []
                window_len = 0
            chunks.append(sent[:chunk_size])
            continue

        window.append(sent)
        window_len += slen + (1 if len(window) > 1 else 0)

    if window:
        chunk = " ".join(window)
        if len(chunk) > 50:
            chunks.append(chunk)

    return chunks


def is_junk_chunk(text: str) -> bool:
    """Filtra chunks con >50% dígitos (tablas, índices, bibliografías)."""
    if not text:
        return True
    digit_count = sum(1 for c in text if c.isdigit())
    return digit_count / len(text) > 0.5


def ingest_all_books():
    os.makedirs(INDEX_DIR, exist_ok=True)

    pdf_files = [f for f in os.listdir(LIBROS_DIR) if f.lower().endswith(".pdf")]
    if not pdf_files:
        print("[ERROR] No se encontraron PDFs en libros/")
        sys.exit(1)

    print(f"[MEDI-IA] Cargando modelo de embeddings: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    all_passages = []  # textos con prefijo "passage: ..." para embedding
    all_metadata = []  # info de origen (texto limpio sin prefijo)

    total_filtered = 0

    for pdf_file in pdf_files:
        pdf_path = os.path.join(LIBROS_DIR, pdf_file)
        book_name = os.path.splitext(pdf_file)[0]
        print(f"\n[>>] Procesando: {pdf_file}")

        pages = extract_text_from_pdf(pdf_path)
        print(f"    Páginas con texto: {len(pages)}")

        book_chunks = 0
        book_filtered = 0
        for page_data in pages:
            chunks = chunk_text(page_data["text"])
            for chunk in chunks:
                if is_junk_chunk(chunk):
                    book_filtered += 1
                    total_filtered += 1
                    continue
                # Prefijo "passage: " requerido por e5-base + contexto del libro
                passage = f"passage: {book_name}: {chunk}"
                all_passages.append(passage)
                all_metadata.append({
                    "book": book_name,
                    "page": page_data["page"],
                    "text": chunk  # texto limpio para mostrar en UI
                })
                book_chunks += 1

        print(f"    Chunks válidos: {book_chunks}  |  Filtrados (basura): {book_filtered}")

    print(f"\n[MEDI-IA] Total chunks: {len(all_passages)}  |  Filtrados: {total_filtered}")
    print(f"[MEDI-IA] Generando embeddings... (puede tomar varios minutos)")

    batch_size = 256
    all_embeddings = []
    for i in range(0, len(all_passages), batch_size):
        batch = all_passages[i:i + batch_size]
        embeddings = model.encode(batch, show_progress_bar=False, normalize_embeddings=True)
        all_embeddings.append(embeddings)
        pct = min(100, int((i + batch_size) / len(all_passages) * 100))
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
