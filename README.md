# MEDI-IA — Asistente Médico con IA

[![CI](https://github.com/Dev-Sot/medical-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Dev-Sot/medical-agent/actions/workflows/ci.yml)
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
| **Autenticación** | Cuentas reales (email + password hasheado) — `/signup`, `/login` |
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

## Libros indexados (8 de 14 activos — ver nota)

> El índice se reconstruyó manualmente tras un incidente que borró `index/books.index` local (ver historial de commits). Para tener algo funcional rápido se re-indexó con un modelo de embeddings más liviano y se cortó a propósito en 8 libros completos — los 6 restantes quedan como trabajo pendiente, no perdidos (el texto ya extraído de los 14 libros sigue completo en `index/metadata.json`, re-indexarlos es solo tiempo de cómputo vía `make ingest` o `rebuild_index_from_metadata.py`).

| Libro | Especialidad | Estado |
|-------|-------------|--------|
| Harrison Principios de Medicina Interna 19ª ed. | Diagnóstico diferencial general | ✅ Indexado |
| Adams & Victor's Principles of Neurology 8th ed. | Neurología | ✅ Indexado |
| Harrison's Infectious Disease | Enfermedades infecciosas | ✅ Indexado |
| Infectious Diseases: A Clinical Short Course | Infectología clínica | ✅ Indexado |
| Compendio de Robbins y Cotran Patología | Fisiopatología | ✅ Indexado |
| Kaplan-Sadock Pocket Handbook | Psiquiatría | ✅ Indexado |
| Lange Case Files (Medical) | Casos clínicos integrados | ✅ Indexado |
| ABC of Dermatology | Dermatología | ✅ Indexado |
| Nelson Textbook of Pediatrics | Pediatría | ⏳ Pendiente (libro más grande del corpus, ~1/3 de todos los chunks) |
| Oxford Handbook of Clinical Medicine 10th ed. | Referencia clínica rápida | ⏳ Pendiente |
| Symptoms to Diagnosis | Razonamiento clínico basado en síntomas | ⏳ Pendiente |
| The Top 100 Drugs Clinical | Farmacología y tratamientos | ⏳ Pendiente |
| Tintinalli Emergency Medicine Manual | Urgencias y emergencias | ⏳ Pendiente |
| Williams Obstetrics | Obstetricia y ginecología | ⏳ Pendiente |

**Próximo paso propuesto:** completar la re-indexación de los 6 libros pendientes (~1h40min adicionales con el modelo liviano actual, según benchmark real de 13.8 chunks/seg) y, si se quiere volver a la mayor calidad de retrieval de `intfloat/multilingual-e5-base`, re-ingestar todo el corpus con GPU o en un proceso overnight — en CPU tomaría varias horas para los 136k chunks completos.

---

## Stack técnico

| Capa | Tecnología |
|------|-----------|
| Backend | Flask 3.x + Gunicorn (2 workers sync) |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (384 dims) — temporal tras recuperación de índice, ver [Libros indexados](#libros-indexados-8-de-14-activos--ver-nota); `intfloat/multilingual-e5-base` (768 dims) es el objetivo de mayor calidad |
| Índice vectorial | FAISS `IndexFlatIP` (cosine via inner product) |
| BM25 | `rank-bm25` — fusión con FAISS vía Reciprocal Rank Fusion |
| Reranker | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (~120 MB, 26 idiomas) |
| LLM | Qwen2.5-7B-Instruct via HuggingFace Inference API (remoto) |
| TTS | `edge-tts` — `es-ES-AlvaroNeural` streaming progresivo |
| Persistencia | SQLite — sesiones, historial, feedback, métricas |
| Rate limiting | flask-limiter, respaldado por Redis (memoria solo en dev local) |
| Frontend | TypeScript + Vite (build propio) + Chart.js + Lucide Icons |
| PDF | fpdf2 (pure Python, sin dependencias nativas) |
| Tests | pytest 185 aserciones · tsc --noEmit para el frontend |
| Calidad | ruff + black + mypy (`pyproject.toml`) |
| CI | GitHub Actions — lint + tests (Python 3.13) y build + typecheck (Node 20) |
| Deploy | Docker (build multi-stage) + docker-compose (app + redis) + nginx |

---

## Inicio rápido

### Requisitos previos
- Python 3.13+
- Node.js 20+ (solo para compilar el frontend — no se necesita en runtime)
- PDFs de los libros en `libros/` (ver tabla de libros indexados)
- Token de HuggingFace (opcional, pero requerido para el agente ReAct)

```bash
# 1. Clonar el repositorio
git clone https://github.com/Dev-Sot/medical-agent.git
cd medi-ia-medical-agent

# 2. Crear entorno virtual e instalar dependencias
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / Mac
make install

# 3. Compilar el frontend (Vite -> static/dist)
make frontend-install
make frontend-build

# 4. Configurar variables de entorno
copy .env.example .env         # Windows
# cp .env.example .env         # Linux / Mac
# Editar .env: agregar HF_TOKEN y SECRET_KEY (obligatoria fuera de FLASK_DEBUG=True)

# 5. Indexar los libros (primera vez, tarda ~5-15 min según cantidad de libros)
make ingest

# 6. Iniciar el servidor
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
| `EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Modelo de embeddings (384 dims) — debe coincidir con el usado para construir `index/books.index` |
| `RERANKER_MODEL` | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` | Modelo reranker |
| `RERANK_THRESHOLD` | `-3.0` | Umbral de relevancia (chunks > 0 = relevantes) |
| `CLEANUP_DAYS` | `30` | Días de inactividad para eliminar sesiones |
| `CLEANUP_INTERVAL_HOURS` | `24` | Frecuencia del cron de limpieza automática |
| `MEMORY_DB_PATH` | `data/memory.db` | Ruta del archivo SQLite |
| `PORT` | `5000` | Puerto del servidor |
| `REDIS_URL` | — | Store compartido para el rate limiter. Sin esto, con >1 worker de gunicorn el límite no se aplica correctamente (ver `gunicorn.conf.py`) |

---

## API Endpoints

| Endpoint | Método | Rate limit | Descripción |
|----------|--------|-----------|-------------|
| `/` | GET | — | Interfaz de chat (requiere sesión iniciada) |
| `/metrics` | GET | — | Dashboard de métricas con Chart.js |
| `/live` | GET | — | Monitor en tiempo real (refresh 5 s) |
| `/evaluate` | GET | — | Dashboard de evaluación RAG |
| `/login` | GET | — | Página de inicio de sesión |
| `/signup` | GET | — | Página de registro (cuenta nueva) |
| `/auth/signup` | POST | 10/hora | Crear cuenta — email + password (min. 8 caracteres) |
| `/auth/login` | POST | 5/min | Iniciar sesión |
| `/auth/logout` | POST | — | Cerrar sesión |
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
# Construir imagen (incluye un stage de Node que compila el frontend)
make docker-build

# Crear .env con las variables necesarias
copy .env.example .env

# Levantar app + redis (requiere índice FAISS pre-construido en ./index/)
make docker-run

# Si el índice no existe, construirlo dentro del contenedor
make docker-ingest

# Ver logs en tiempo real
docker compose logs -f

# Bajar
make docker-stop
```

`docker-compose.yml` levanta un servicio `redis` junto con la app y define `REDIS_URL` automáticamente — el rate limiter queda correctamente compartido entre los workers de gunicorn sin configuración adicional.

Para producción con nginx, usar `nginx/medi-ia.conf` — incluye `proxy_buffering off` para el endpoint SSE `/api/stream`.

---

## Estructura del proyecto

```
medi-ia/
├── app.py                     # Flask app: rutas HTTP + auth + orquestacion (delgado)
├── ingest.py                  # Indexación de PDFs → FAISS (chunk 600/120, sentence-aware)
├── rebuild_index_from_metadata.py  # Reconstruye books.index desde metadata.json sin PDFs
├── manage.py                  # CLI: listar sesiones, cleanup, clear
├── gunicorn.conf.py           # Config producción (2 workers sync, preload_app)
├── pyproject.toml             # Config de ruff / black / mypy
├── requirements.txt           # Dependencias directas, version fijada
├── requirements-lock.txt      # pip freeze completo — build reproducible
├── requirements-dev.txt       # ruff / black / mypy
├── src/
│   ├── agent.py               # Orquestador: ReAct vs RAG fallback
│   ├── agent_loop.py          # Bucle ReAct + generador SSE (max 6 iteraciones)
│   ├── guardrails.py          # Filtro regex pre-LLM
│   ├── llm.py                 # Cliente HuggingFace InferenceClient
│   ├── memory.py              # Historial + feedback en SQLite
│   ├── metrics.py             # Metricas en memoria (queries/hora, latencia, errores)
│   ├── pdf_export.py          # Generacion de PDF (diagnostico + historial de sesion)
│   ├── schemas.py             # Pydantic: ConsultaRequest, DiagnosticoResponse
│   ├── tools.py                # 4 herramientas del agente ReAct
│   ├── evaluation_full.py     # Evaluación completa con dataset anotado
│   └── rag/
│       ├── embeddings.py      # Singleton SentenceTransformer (e5-base, 768 dims)
│       ├── retriever.py       # FAISS + BM25 con Reciprocal Rank Fusion
│       ├── bm25_retriever.py  # BM25 lazy-loaded desde metadata.json
│       ├── reranker.py        # CrossEncoder reranker
│       ├── section_mapping.py # Página → capítulo por libro
│       └── semantic_fallback.py  # Fallback cuando rerank_score < threshold
├── frontend/                  # Build del chat UI (Vite + TypeScript + Tailwind)
│   ├── src/main.ts            # Toda la logica de UI, tipada, un solo modulo
│   ├── src/styles/*.css       # CSS organizado por seccion (10 archivos)
│   └── vite.config.ts         # Build -> ../static/dist (lo sirve Flask)
├── templates/
│   ├── index.html             # Markup del chat (328 lineas — CSS/JS van en frontend/)
│   ├── metrics.html           # Dashboard métricas con Chart.js
│   ├── evaluate.html          # Dashboard evaluación RAG
│   ├── live.html              # Monitor tiempo real
│   └── login.html             # Página de autenticación
├── static/dist/                # Bundle generado por Vite (gitignored, `make frontend-build`)
├── data/
│   ├── memory.db               # SQLite — sesiones, feedback (generado en runtime)
│   ├── eval_dataset.json      # 40 queries anotadas para evaluación (v1.3)
│   └── eval_full_results.json # Resultados de la última evaluación completa
├── tests/                     # 185 tests pytest
├── index/                     # Índice FAISS (generado por ingest.py, no incluido en repo)
├── libros/                    # PDFs fuente (no incluidos en el repo)
├── nginx/medi-ia.conf         # Config nginx para producción
├── Dockerfile                  # Multi-stage: build frontend (Node) -> runtime (Python)
├── docker-compose.yml          # Servicios: medi-ia + redis
└── .github/workflows/ci.yml    # CI: lint + tests (Python) y build + typecheck (frontend)
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
