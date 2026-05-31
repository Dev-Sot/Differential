# MEDI-IA — Asistente Médico con IA

[![CI](https://github.com/Milan32555/medi-ia-medical-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Milan32555/medi-ia-medical-agent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.13-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/flask-3.x-000000?logo=flask&logoColor=white)
![Tests](https://img.shields.io/badge/tests-185-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

Agente de diagnóstico diferencial basado en **14 libros médicos reales** (~136 000 chunks). Combina recuperación híbrida BM25+FAISS con fusión RRF, reranking con cross-encoder multilingüe y un agente ReAct con Qwen2.5-7B via HuggingFace.

---

## Arquitectura

```
Consulta del usuario
        │
        ▼
┌───────────────────┐
│    Guardrails     │  ← filtro regex pre-LLM (médico vs no-médico)
└────────┬──────────┘
         │
    ¿HF_TOKEN?
    ┌────┴─────────────────────────────┐
    │ Sí                               │ No
    ▼                                  ▼
┌──────────────────────┐   ┌──────────────────────┐
│   ReAct Agent        │   │    RAG Template       │
│   Qwen2.5-7B (HF)    │   │    (sin LLM)          │
│   max 6 iteraciones  │   └──────────┬───────────┘
│   4 tools            │              │
└──────────┬───────────┘              │
           └──────────┬───────────────┘
                      ▼
        ┌──────────────────────────────────┐
        │   BM25 + FAISS IndexFlatIP        │
        │   Reciprocal Rank Fusion (RRF)    │
        │   + CrossEncoder reranker         │
        │   mMARCO multilingüe (26 idiomas) │
        │   14 libros médicos indexados     │
        └──────────────────────────────────┘
```

---

## Características

| Feature | Descripción |
|---------|-------------|
| **Agente ReAct** | Qwen2.5-7B con 4 tools: `search_symptoms`, `assess_urgency`, `get_drug_info`, `get_section` |
| **Retrieval híbrido** | BM25 + FAISS `IndexFlatIP` fusionados con Reciprocal Rank Fusion (RRF, k=60) |
| **Reranker multilingüe** | cross-encoder mMARCO (26 idiomas) con umbral configurable |
| **Streaming SSE** | Razonamiento token a token en tiempo real |
| **TTS neural** | Text-to-speech con `edge-tts` (`es-ES-AlvaroNeural`) + modo manos libres |
| **Mapa corporal SVG** | 24 zonas interactivas (frontal + dorsal) — inyecta contexto en la query |
| **Perfil clínico** | Modal con alergias, medicamentos y condiciones — inyección silenciosa en cada consulta |
| **Visualización RAG** | Panel colapsable por respuesta: pasos FAISS → reranker → LLM con scores reales |
| **Demo chips** | 6 queries reales del benchmark (IAM, meningitis, apendicitis, LES, NAC, ICC) |
| **Follow-ups contextuales** | Preguntas de seguimiento generadas a partir del diagnóstico |
| **Dashboard métricas** | Gráfico queries/hora, latencia avg/p95, uptime (Chart.js) |
| **Dashboard evaluación** | Recall@1/3/5, MRR, Precision@5 por categoría con 40 queries anotadas |
| **Live monitor** | `/live` — dashboard tiempo real con refresh automático (5 s) |
| **PWA** | Manifest `/manifest.json` — instalable desde el browser |
| **Feedback** | Botones 👍👎 por respuesta, persistidos en SQLite |
| **Export PDF** | Por diagnóstico individual o sesión completa |
| **Historial** | Consultas anteriores en sidebar (localStorage) |
| **Dark mode** | Toggle luna/sol, persiste en localStorage |
| **Input de voz** | Web Speech API, resultados en tiempo real (Chrome) |
| **Autenticación** | Password opcional via `AUTH_PASSWORD` |
| **Cron cleanup** | Limpieza automática de sesiones inactivas (daemon thread) |
| **Docker** | Dockerfile + docker-compose + nginx (SSE-ready) |
| **185 tests** | pytest: guardrails, tools, memory, api, metrics, feedback, evaluation, pipeline |

---

## Métricas de evaluación

Dataset v1.3 — 40 queries anotadas (35 médicas + 5 guardrails), 14 libros:

| Métrica | MiniLM · 4 libros | e5-base · 4 libros | **e5-base · 14 libros (actual)** |
|---------|:-----------------:|:------------------:|:--------------------------------:|
| Recall@1 | 74.3% | 91.4% | **97.1%** |
| Recall@3 | 94.3% | 100% | **100%** |
| Recall@5 | 97.1% | 100% | **100%** |
| MRR | 0.8405 | 0.9571 | **0.9857** |
| Precision@5 | 74.3% | 94.3% | **80.6%** |
| Guardrails | 100% | 100% | **100%** |

### Por categoría (configuración actual)

| Categoría | Recall@1 | Recall@3 | Recall@5 | MRR |
|-----------|:--------:|:--------:|:--------:|:---:|
| Síntomas → Diagnóstico | 100% | 100% | 100% | 1.000 |
| Urgencias y Triaje | 100% | 100% | 100% | 1.000 |
| Farmacología | 90% | 100% | 100% | 0.950 |
| Fisiopatología | 100% | 100% | 100% | 1.000 |

---

## Libros indexados (14)

| Libro | Especialidad |
|-------|-------------|
| Harrison Principios de Medicina Interna 19ª ed. | Diagnóstico diferencial general |
| Oxford Handbook of Clinical Medicine 10th ed. | Referencia clínica rápida |
| Symptoms to Diagnosis | Razonamiento clínico basado en síntomas |
| The Top 100 Drugs Clinical | Farmacología y tratamientos |
| Tintinalli Emergency Medicine Manual | Urgencias y emergencias |
| Adams & Victor's Principles of Neurology 8th ed. | Neurología |
| Harrison's Infectious Disease | Enfermedades infecciosas |
| Infectious Diseases: A Clinical Short Course | Infectología clínica |
| Compendio de Robbins y Cotran Patología | Fisiopatología |
| Nelson Textbook of Pediatrics | Pediatría |
| Kaplan-Sadock Pocket Handbook | Psiquiatría |
| Williams Obstetrics | Obstetricia y ginecología |
| Lange Case Files (Medical) | Casos clínicos integrados |
| ABC of Dermatology | Dermatología |

---

## Stack técnico

| Capa | Tecnología |
|------|-----------|
| Backend | Flask 3.x + Gunicorn (2 workers sync) |
| Embeddings | `intfloat/multilingual-e5-base` (~500 MB, 768 dims, retrieval-optimized) |
| Índice vectorial | FAISS `IndexFlatIP` (cosine via inner product) |
| BM25 | `rank-bm25` — fusión con FAISS vía Reciprocal Rank Fusion |
| Reranker | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (~120 MB, 26 idiomas) |
| LLM | Qwen2.5-7B-Instruct via HuggingFace Inference API (remoto) |
| TTS | `edge-tts` — `es-ES-AlvaroNeural` streaming progresivo |
| Persistencia | SQLite — sesiones, historial, feedback, métricas |
| Frontend | HTML5 + CSS3 + JS vanilla + Chart.js + Lucide Icons |
| PDF | fpdf2 (pure Python, sin dependencias nativas) |
| Tests | pytest 185 aserciones |
| CI | GitHub Actions (Python 3.13, ubuntu-latest) |
| Deploy | Docker + docker-compose + nginx |

---

## Inicio rápido

### Requisitos previos
- Python 3.13+
- PDFs de los libros en `libros/` (ver tabla de libros indexados)
- Token de HuggingFace (opcional, pero requerido para el agente ReAct)

```bash
# 1. Clonar el repositorio
git clone https://github.com/Milan32555/medi-ia-medical-agent.git
cd medi-ia-medical-agent

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / Mac
make install

# 3. Configurar variables de entorno
copy .env.example .env         # Windows
# cp .env.example .env         # Linux / Mac
# Editar .env: agregar HF_TOKEN y SECRET_KEY

# 4. Indexar los libros (primera vez, tarda ~5-15 min según cantidad de libros)
make ingest

# 5. Iniciar el servidor
make run
# Abre http://localhost:5000
```

### Sin HF_TOKEN (modo RAG básico)
El sistema funciona sin token. Las respuestas son fragmentos del libro sin análisis del LLM — útil para pruebas de desarrollo.

---

## Variables de entorno

| Variable | Default | Descripción |
|----------|---------|-------------|
| `HF_TOKEN` | — | Activa el agente ReAct. Sin él → modo RAG Template |
| `HF_MODEL` | `Qwen/Qwen2.5-7B-Instruct` | Modelo LLM via HuggingFace Inference API |
| `SECRET_KEY` | (random) | **Definir en producción** — clave Flask para sesiones |
| `AUTH_PASSWORD` | — | Si se define, protege toda la app con password |
| `EMBEDDING_MODEL` | `intfloat/multilingual-e5-base` | Modelo de embeddings (768 dims) |
| `RERANKER_MODEL` | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | Modelo reranker |
| `RERANK_THRESHOLD` | `-3.0` | Umbral de relevancia (chunks > 0 = relevantes) |
| `CLEANUP_DAYS` | `30` | Días de inactividad para eliminar sesiones |
| `CLEANUP_INTERVAL_HOURS` | `24` | Frecuencia del cron de limpieza automática |
| `MEMORY_DB_PATH` | `data/memory.db` | Ruta del archivo SQLite |
| `PORT` | `5000` | Puerto del servidor |

---

## API Endpoints

| Endpoint | Método | Rate limit | Descripción |
|----------|--------|-----------|-------------|
| `/` | GET | — | Interfaz de chat |
| `/metrics` | GET | — | Dashboard de métricas con Chart.js |
| `/live` | GET | — | Monitor en tiempo real (refresh 5 s) |
| `/evaluate` | GET | — | Dashboard de evaluación RAG |
| `/login` | GET | — | Página de login (solo si AUTH_PASSWORD definido) |
| `/manifest.json` | GET | — | PWA manifest |
| `/api/query` | POST | 10/min | Consulta RAG/ReAct — respuesta completa |
| `/api/stream` | POST | 10/min | SSE streaming del agente token a token |
| `/api/tts` | POST | — | Text-to-speech neural (edge-tts) |
| `/api/export/pdf` | POST | 5/min | Exportar diagnóstico como PDF |
| `/api/export/conversation` | GET | 5/min | Exportar sesión completa como PDF |
| `/api/feedback` | POST | 30/min | Registrar valoración 👍 (1) o 👎 (-1) |
| `/api/metrics` | GET | — | Métricas del sistema en JSON |
| `/api/health` | GET | — | Estado del índice, modelo y modo |
| `/api/reset` | POST | — | Limpiar historial de la sesión actual |
| `/api/reload` | POST | — | Recargar índice FAISS sin reiniciar servidor |
| `/api/evaluate/full` | GET | — | Resultados de evaluación completa (JSON) |
| `/api/evaluate/snapshot` | GET | — | Snapshot actual de métricas RAG |
| `/api/evaluate/run` | POST | — | Lanzar evaluación completa en background |

---

## Tests

```bash
make test                                    # Todos los tests (185)
venv\Scripts\pytest.exe tests/ -v           # Con salida detallada

# Por módulo
pytest tests/test_guardrails.py -v          # Lógica pura de filtro médico
pytest tests/test_tools.py -v              # Tools del agente (mocks FAISS)
pytest tests/test_memory.py -v             # SQLite — sesiones e historial
pytest tests/test_api.py -v               # Endpoints Flask
pytest tests/test_metrics.py -v           # Métricas en memoria
pytest tests/test_feedback.py -v          # Feedback SQLite + endpoint
pytest tests/test_evaluation.py -v        # Pipeline de evaluación RAG
pytest tests/test_pipeline.py -v          # Pipeline completo end-to-end
```

Los tests de `test_retriever.py` hacen skip automático si el índice FAISS no existe — comportamiento intencional para CI.

---

## Deploy con Docker

```bash
# Construir imagen
make docker-build

# Crear .env con las variables necesarias
copy .env.example .env

# Levantar (requiere índice FAISS pre-construido en ./index/)
make docker-run

# Si el índice no existe, construirlo dentro del contenedor
make docker-ingest

# Ver logs en tiempo real
docker compose logs -f

# Bajar
make docker-stop
```

Para producción con nginx, usar `nginx/medi-ia.conf` — incluye `proxy_buffering off` para el endpoint SSE `/api/stream`.

---

## Estructura del proyecto

```
medi-ia/
├── app.py                     # Flask app, endpoints, métricas, cron cleanup, TTS
├── ingest.py                  # Indexación de PDFs → FAISS (chunk 600/120, sentence-aware)
├── manage.py                  # CLI: listar sesiones, cleanup, clear
├── gunicorn.conf.py           # Config producción (2 workers sync, preload_app)
├── src/
│   ├── agent.py               # Orquestador: ReAct vs RAG fallback
│   ├── agent_loop.py          # Bucle ReAct + generador SSE (max 6 iteraciones)
│   ├── guardrails.py          # Filtro regex pre-LLM
│   ├── llm.py                 # Cliente HuggingFace InferenceClient
│   ├── memory.py              # Historial + feedback en SQLite
│   ├── schemas.py             # Pydantic: ConsultaRequest, DiagnosticoResponse
│   ├── tools.py               # 4 herramientas del agente ReAct
│   ├── evaluation_full.py     # Evaluación completa con dataset anotado
│   └── rag/
│       ├── embeddings.py      # Singleton SentenceTransformer (e5-base, 768 dims)
│       ├── retriever.py       # FAISS + BM25 con Reciprocal Rank Fusion
│       ├── bm25_retriever.py  # BM25 lazy-loaded desde metadata.json
│       ├── reranker.py        # CrossEncoder reranker
│       ├── section_mapping.py # Página → capítulo por libro
│       └── semantic_fallback.py  # Fallback cuando rerank_score < threshold
├── templates/
│   ├── index.html             # UI chat (TTS, mapa corporal, perfil clínico, onboarding)
│   ├── metrics.html           # Dashboard métricas con Chart.js
│   ├── evaluate.html          # Dashboard evaluación RAG
│   ├── live.html              # Monitor tiempo real
│   └── login.html             # Página de autenticación
├── data/
│   ├── memory.db              # SQLite — sesiones, feedback (generado en runtime)
│   ├── eval_dataset.json      # 40 queries anotadas para evaluación (v1.3)
│   └── eval_full_results.json # Resultados de la última evaluación completa
├── tests/                     # 185 tests pytest
├── index/                     # Índice FAISS (generado por ingest.py, no incluido en repo)
├── libros/                    # PDFs fuente (no incluidos en el repo)
├── nginx/medi-ia.conf         # Config nginx para producción
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml   # CI: pytest en cada push/PR
```

---

## Gestión de sesiones

```bash
# Listar sesiones activas
make sessions

# Limpiar sesiones inactivas > 30 días
make cleanup

# Limpiar sesiones inactivas > N días
make cleanup DAYS=7

# Borrar sesión específica
venv\Scripts\python.exe manage.py clear <session_id>
```

---

## Nota académica

Este sistema es un proyecto de investigación académica sobre aplicación de técnicas RAG y agentes conversacionales en el dominio médico. **No reemplaza la consulta médica profesional.** En caso de emergencia, llame al **123** (Colombia) o diríjase a urgencias inmediatamente.
