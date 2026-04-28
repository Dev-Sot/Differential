"""
MEDI-IA RAG Pipeline
Usa TF-IDF vectorization + cosine similarity para recuperar
el contexto médico más relevante dado un query de síntomas.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data.corpus_medico import CORPUS, GRAVITY_LEVELS
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

class MediIAPipeline:
    def __init__(self):
        self.corpus = CORPUS
        self.vectorizer = None
        self.tfidf_matrix = None
        self._build_index()

    def _build_index(self):
        """Construye el índice TF-IDF sobre el corpus médico."""
        documents = []
        for entry in self.corpus:
            # Combinar título + síntomas + descripción para mejor matching
            doc = f"{entry['titulo']} {entry['sintomas']} {entry['descripcion']}"
            documents.append(doc.lower())

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            max_features=5000,
            stop_words=None  # Mantener palabras médicas en español
        )
        self.tfidf_matrix = self.vectorizer.fit_transform(documents)
        print(f"[MEDI-IA] Índice construido: {len(self.corpus)} condiciones médicas")

    def retrieve(self, query: str, top_k: int = 3):
        """Recupera las condiciones más similares al query del usuario."""
        query_clean = query.lower().strip()
        query_vec = self.vectorizer.transform([query_clean])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        top_indices = similarities.argsort()[::-1][:top_k]
        results = []
        for idx in top_indices:
            if similarities[idx] > 0.01:  # Umbral mínimo de relevancia
                entry = self.corpus[idx].copy()
                entry['score'] = float(similarities[idx])
                results.append(entry)
        
        return results

    def generate_response(self, query: str, retrieved: list) -> dict:
        """Genera una respuesta estructurada basada en los documentos recuperados."""
        if not retrieved:
            return {
                "respuesta": "No pude identificar una condición específica con los síntomas descritos. Por favor, consulta con un médico para una evaluación adecuada.",
                "condicion_principal": "No determinada",
                "gravedad": "moderada",
                "recomendacion": "Consultar con un profesional de la salud.",
                "condiciones_relacionadas": [],
                "urgencia": "media"
            }

        principal = retrieved[0]
        nivel = GRAVITY_LEVELS.get(principal['gravedad'], GRAVITY_LEVELS['moderada'])

        # Construir respuesta contextual
        sintomas_usuario = query.strip()
        
        respuesta = (
            f"Basándome en los síntomas que describes ({sintomas_usuario}), "
            f"los indicadores más compatibles apuntan a: **{principal['titulo']}**.\n\n"
            f"{principal['descripcion']}"
        )

        condiciones_relacionadas = []
        for item in retrieved[1:]:
            condiciones_relacionadas.append({
                "nombre": item['titulo'],
                "gravedad": item['gravedad'],
                "relevancia": round(item['score'] * 100, 1)
            })

        return {
            "respuesta": respuesta,
            "condicion_principal": principal['titulo'],
            "gravedad": principal['gravedad'],
            "gravedad_info": nivel,
            "recomendacion": principal['recomendacion'],
            "condiciones_relacionadas": condiciones_relacionadas,
            "urgencia": principal['urgencia'],
            "score_confianza": round(principal['score'] * 100, 1)
        }

    def query(self, user_input: str) -> dict:
        """Pipeline completo: retrieve + generate."""
        retrieved = self.retrieve(user_input, top_k=3)
        return self.generate_response(user_input, retrieved)


# Singleton para reutilizar en Flask
_pipeline_instance = None

def get_pipeline():
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = MediIAPipeline()
    return _pipeline_instance


if __name__ == "__main__":
    # Test rápido
    pipeline = MediIAPipeline()
    test_queries = [
        "tengo fiebre alta, dolor muscular y escalofríos",
        "me duele el pecho y el brazo izquierdo, sudo mucho",
        "tengo picazón en los ojos y estornudo mucho"
    ]
    for q in test_queries:
        result = pipeline.query(q)
        print(f"\nQuery: {q}")
        print(f"Condición: {result['condicion_principal']}")
        print(f"Gravedad: {result['gravedad']} | Confianza: {result['score_confianza']}%")
        print(f"Recomendación: {result['recomendacion'][:80]}...")
