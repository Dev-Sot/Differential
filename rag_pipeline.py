"""
MEDI-IA RAG Pipeline — Fase 3
Usa sentence-transformers + FAISS para recuperar fragmentos reales
de los libros médicos indexados.
"""

import os
import json
import sys
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

INDEX_DIR = os.path.join(os.path.dirname(__file__), "index")
INDEX_PATH = os.path.join(INDEX_DIR, "books.index")
META_PATH = os.path.join(INDEX_DIR, "metadata.json")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

GRAVITY_LEVELS = {
    "leve": {
        "label": "LEVE",
        "color": "#22c55e",
        "icon": "🟢",
        "description": "No requiere atención urgente. Monitorea síntomas."
    },
    "moderada": {
        "label": "MODERADA",
        "color": "#f59e0b",
        "icon": "🟡",
        "description": "Consulta médica recomendada en las próximas 24-48 horas."
    },
    "grave": {
        "label": "GRAVE",
        "color": "#ef4444",
        "icon": "🔴",
        "description": "Requiere atención médica pronto. No demores la consulta."
    },
    "emergencia": {
        "label": "EMERGENCIA",
        "color": "#8b5cf6",
        "icon": "🚨",
        "description": "Llama al 123 o ve a urgencias AHORA."
    }
}

URGENCY_KEYWORDS = {
    "emergencia": [
        "infarto", "paro cardiaco", "dificultad respiratoria severa", "pérdida de conciencia",
        "convulsiones", "accidente cerebrovascular", "hemorragia", "dolor torácico severo",
        "anafilaxia", "shock", "sepsis"
    ],
    "grave": [
        "fiebre alta", "dolor pecho", "brazo izquierdo", "presión arterial", "meningitis",
        "apendicitis", "fractura", "herida profunda", "deshidratación severa"
    ]
}


def _assess_urgency(query: str, context: str) -> tuple[str, str]:
    """Determina nivel de urgencia basado en query y contexto recuperado."""
    combined = (query + " " + context).lower()
    for level, keywords in URGENCY_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            return level, GRAVITY_LEVELS[level]
    return "moderada", GRAVITY_LEVELS["moderada"]


class MediIAPipeline:
    def __init__(self):
        self._index = None
        self._metadata = None
        self._model = None
        self._use_books = False
        self._load()

    def _load(self):
        """Carga el índice FAISS y los metadatos. Si no existe, avisa."""
        if not os.path.exists(INDEX_PATH) or not os.path.exists(META_PATH):
            print("[MEDI-IA] Índice de libros no encontrado. Ejecuta: python ingest.py")
            print("[MEDI-IA] Usando corpus básico como respaldo.")
            self._load_fallback()
            return

        try:
            import faiss
            from sentence_transformers import SentenceTransformer

            print("[MEDI-IA] Cargando índice FAISS desde libros médicos...")
            self._index = faiss.read_index(INDEX_PATH)
            with open(META_PATH, "r", encoding="utf-8") as f:
                self._metadata = json.load(f)

            print(f"[MEDI-IA] Cargando modelo: {MODEL_NAME}")
            self._model = SentenceTransformer(MODEL_NAME)
            self._use_books = True
            print(f"[MEDI-IA] Sistema listo. {self._index.ntotal} fragmentos de libros indexados.")
        except Exception as e:
            print(f"[MEDI-IA] Error cargando índice: {e}. Usando corpus básico.")
            self._load_fallback()

    def _load_fallback(self):
        """Carga el corpus hardcodeado como respaldo."""
        from corpus_medico import CORPUS
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        self._corpus = CORPUS
        documents = [
            f"{e['titulo']} {e['sintomas']} {e['descripcion']}".lower()
            for e in CORPUS
        ]
        self._vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=5000)
        self._tfidf_matrix = self._vectorizer.fit_transform(documents)
        self._use_books = False
        print(f"[MEDI-IA] Corpus básico cargado: {len(CORPUS)} condiciones.")

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """Recupera los fragmentos más relevantes del índice."""
        if self._use_books:
            return self._retrieve_faiss(query, top_k)
        return self._retrieve_tfidf(query, top_k)

    def _retrieve_faiss(self, query: str, top_k: int) -> list[dict]:
        query_vec = self._model.encode([query], normalize_embeddings=True).astype("float32")
        scores, indices = self._index.search(query_vec, top_k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and score > 0.2:
                meta = self._metadata[idx].copy()
                meta["score"] = float(score)
                results.append(meta)
        return results

    def _retrieve_tfidf(self, query: str, top_k: int) -> list[dict]:
        from sklearn.metrics.pairwise import cosine_similarity
        query_vec = self._vectorizer.transform([query.lower()])
        sims = cosine_similarity(query_vec, self._tfidf_matrix).flatten()
        top_indices = sims.argsort()[::-1][:top_k]
        results = []
        for idx in top_indices:
            if sims[idx] > 0.01:
                entry = self._corpus[idx].copy()
                entry["score"] = float(sims[idx])
                results.append(entry)
        return results

    def generate_response(self, query: str, retrieved: list) -> dict:
        """Genera respuesta estructurada a partir de los fragmentos recuperados."""
        if not retrieved:
            return {
                "respuesta": "No encontré información suficiente para los síntomas descritos en los libros médicos disponibles. Por favor consulta con un médico.",
                "condicion_principal": "No determinada",
                "gravedad": "moderada",
                "gravedad_info": GRAVITY_LEVELS["moderada"],
                "recomendacion": "Consultar con un profesional de la salud.",
                "condiciones_relacionadas": [],
                "urgencia": "media",
                "score_confianza": 0,
                "fuente": "Sin fuente"
            }

        if self._use_books:
            return self._generate_from_books(query, retrieved)
        return self._generate_from_corpus(query, retrieved)

    def _generate_from_books(self, query: str, retrieved: list) -> dict:
        top = retrieved[0]
        context_texts = "\n\n".join(f"[{r['book']} p.{r['page']}]\n{r['text']}" for r in retrieved)

        urgency_level, urgency_info = _assess_urgency(query, context_texts)

        respuesta = (
            f"Basándome en los libros médicos de la base de datos, los fragmentos más relevantes "
            f"para los síntomas descritos ({query}) provienen de **{top['book']}** (página {top['page']}):\n\n"
            f"{top['text']}"
        )

        fuentes = list({r["book"] for r in retrieved})
        condiciones_relacionadas = [
            {
                "nombre": f"{r['book']} — p.{r['page']}",
                "gravedad": urgency_level,
                "relevancia": round(r["score"] * 100, 1)
            }
            for r in retrieved[1:3]
        ]

        nivel_info = GRAVITY_LEVELS.get(urgency_level, GRAVITY_LEVELS["moderada"])

        recomendacion = (
            "Información extraída de fuentes médicas de referencia. "
            "Consulta con un profesional de salud para diagnóstico formal y tratamiento. "
            f"Fuentes: {', '.join(fuentes)}."
        )

        return {
            "respuesta": respuesta,
            "condicion_principal": top["book"],
            "gravedad": urgency_level,
            "gravedad_info": nivel_info,
            "recomendacion": recomendacion,
            "condiciones_relacionadas": condiciones_relacionadas,
            "urgencia": urgency_level,
            "score_confianza": round(top["score"] * 100, 1),
            "fuente": ", ".join(fuentes)
        }

    def _generate_from_corpus(self, query: str, retrieved: list) -> dict:
        from corpus_medico import GRAVITY_LEVELS as GL
        principal = retrieved[0]
        nivel = GL.get(principal["gravedad"], GL["moderada"])

        respuesta = (
            f"Basándome en los síntomas que describes ({query}), "
            f"los indicadores más compatibles apuntan a: **{principal['titulo']}**.\n\n"
            f"{principal['descripcion']}"
        )

        condiciones_relacionadas = [
            {"nombre": item["titulo"], "gravedad": item["gravedad"], "relevancia": round(item["score"] * 100, 1)}
            for item in retrieved[1:]
        ]

        return {
            "respuesta": respuesta,
            "condicion_principal": principal["titulo"],
            "gravedad": principal["gravedad"],
            "gravedad_info": nivel,
            "recomendacion": principal["recomendacion"],
            "condiciones_relacionadas": condiciones_relacionadas,
            "urgencia": principal["urgencia"],
            "score_confianza": round(principal["score"] * 100, 1),
            "fuente": "Corpus médico básico"
        }

    def query(self, user_input: str) -> dict:
        retrieved = self.retrieve(user_input, top_k=5)
        return self.generate_response(user_input, retrieved)

    def reload_index(self):
        """Recarga el índice después de agregar nuevos libros."""
        self._index = None
        self._metadata = None
        self._model = None
        self._use_books = False
        self._load()


_pipeline_instance = None

def get_pipeline():
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = MediIAPipeline()
    return _pipeline_instance


if __name__ == "__main__":
    pipeline = MediIAPipeline()
    queries = [
        "tengo fiebre alta, dolor muscular y escalofríos",
        "me duele el pecho y el brazo izquierdo, sudo mucho",
    ]
    for q in queries:
        result = pipeline.query(q)
        print(f"\nQuery: {q}")
        print(f"Fuente: {result.get('fuente', 'N/A')}")
        print(f"Gravedad: {result['gravedad']} | Confianza: {result['score_confianza']}%")
        print(f"Respuesta: {result['respuesta'][:200]}...")
