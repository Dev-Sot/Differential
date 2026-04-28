# MEDI-IA — Agente Inteligente para Evaluación de Síntomas

## Fase 2: RAG Pipeline + App Web

### Descripción
MEDI-IA es un agente conversacional que usa Retrieval-Augmented Generation (RAG) para evaluar síntomas médicos.
El sistema recupera información relevante de un corpus médico estructurado usando embeddings TF-IDF + similitud coseno,
y genera respuestas contextualizadas con nivel de triaje.

### Stack Técnico
- **Backend:** Flask (Python)
- **RAG Pipeline:** TF-IDF Vectorization + Cosine Similarity (scikit-learn)
- **Vector Index:** FAISS-CPU
- **Corpus:** 20 condiciones médicas en español (síntomas, descripción, recomendación)
- **Frontend:** HTML5 + CSS3 + JavaScript vanilla

### Instalación

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Ejecutar la app
python app.py

# 3. Abrir en el navegador
http://localhost:5000
```

### Estructura del Proyecto
```
medi-ia/
├── app.py                  # Servidor Flask + rutas API
├── rag_pipeline.py         # Pipeline RAG (TF-IDF + retrieval + generación)
├── requirements.txt
├── data/
│   └── corpus_medico.py    # Corpus de 20 condiciones médicas en español
└── templates/
    └── index.html          # UI web (chat interface)
```

### API Endpoints
- `GET /` — Interfaz web principal
- `POST /api/query` — Recibe síntomas, retorna evaluación JSON
- `GET /api/health` — Estado del sistema

### Uso
Describe tus síntomas en lenguaje natural (español) en el chat.
El agente:
1. Vectoriza el texto usando TF-IDF
2. Busca las condiciones más similares en el corpus (cosine similarity)
3. Genera una respuesta con: condición principal, nivel de gravedad, recomendación
4. Clasifica urgencia: leve / moderada / grave / emergencia

### Nota
Este sistema es para fines académicos. No reemplaza la consulta médica profesional.
