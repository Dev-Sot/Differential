# MEDI-IA — Asistente Médico con IA

[![CI](https://github.com/Milan32555/medi-ia-medical-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Milan32555/medi-ia-medical-agent/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.13-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/flask-3.x-000000?logo=flask&logoColor=white)
![Tests](https://img.shields.io/badge/tests-120%2B-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

Agente de diagnóstico diferencial basado en libros médicos reales. Combina recuperación semántica con FAISS, reranking con cross-encoder multilingüe y un agente ReAct con Qwen2.5-7B via HuggingFace.

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
        ┌──────────────────────────────┐
        │   FAISS IndexFlatIP          │
        │   + CrossEncoder reranker    │
        │   mMARCO multilingüe (26)    │
        │   4 libros médicos indexados │
        └──────────────────────────────┘
```

---

## Características

| Feature | Descripción |
|---------|-------------|
| **Agente ReAct** | Qwen2.5-7B con 4 tools: `search_symptoms`, `assess_urgency`, `get_drug_info`, `get_section` |
| **RAG Pipeline** | FAISS `IndexFlatIP` (cosine) + cross-encoder mMARCO (26 idiomas) |
| **Streaming SSE** | Razonamiento token a token en tiempo real |
| **Trazabilidad RAG** | Scores FAISS y rerank visibles en la UI con barras de progreso |
| **Modo dual** | ReAct Agent (con `HF_TOKEN`) o RAG Template (sin token) |
| **Dashboard métricas** | Gráfico queries/hora, latencia avg/p95, uptime (Chart.js) |
| **Feedback** | Botones 👍👎 por respuesta, persistidos en SQLite |
| **Export PDF** | Por diagnóstico individual o sesión completa |
| **Historial** | Consultas anteriores en sidebar (localStorage) |
| **Dark mode** | Toggle luna/sol, persiste en localStorage |
| **Input de voz** | Web Speech API, resultados en tiempo real (Chrome) |
| **Autenticación** | Password opcional via `AUTH_PASSWORD` |
| **Cron cleanup** | Limpieza automática de sesiones inactivas (daemon thread) |
| **Docker** | Dockerfile + docker-compose + nginx (SSE-ready) |
| **120+ tests** | pytest: guardrails, tools, memory, api, metrics, feedback |

---

## Libros indexados

| Libro | Especialidad |
|-------|-------------|
| Harrison Principios de Medicina Interna 19ª ed. | Diagnóstico diferencial general |
| Oxford Handbook of Clinical Medicine 10th ed. | Referencia clínica rápida |
| Symptoms to Diagnosis | Razonamiento clínico basado en síntomas |
| The Top 100 Drugs Clinical | Farmacología y tratamientos |

---

## Stack técnico

| Capa | Tecnología |
|------|-----------|
| Backend | Flask 3.x + Gunicorn (2 workers sync) |
| Embeddings | `paraphrase-multilingual-MiniLM-L12-v2` (~400 MB) |
| Índice vectorial | FAISS `IndexFlatIP` (cosine via inner product) |
| Reranker | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` (~120 MB) |
| LLM | Qwen2.5-7B-Instruct via HuggingFace Inference API (remoto) |
| Persistencia | SQLite — sesiones, historial, feedback |
| Frontend | HTML5 + CSS3 + JS vanilla + Chart.js + Lucide Icons |
| PDF | fpdf2 (pure Python, sin dependencias nativas) |
| Tests | pytest 100+ aserciones |
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

# 4. Indexar los libros (primera vez, tarda ~5-10 min)
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
| `/metrics` | GET | — | Dashboard de métricas |
| `/login` | GET | — | Página de login (solo si AUTH_PASSWORD definido) |
| `/api/query` | POST | 10/min | Consulta RAG/ReAct — respuesta completa |
| `/api/stream` | POST | 10/min | SSE streaming del agente token a token |
| `/api/export/pdf` | POST | 5/min | Exportar diagnóstico como PDF |
| `/api/export/conversation` | GET | 5/min | Exportar sesión completa como PDF |
| `/api/feedback` | POST | 30/min | Registrar valoración 👍 (1) o 👎 (-1) |
| `/api/metrics` | GET | — | Métricas del sistema en JSON |
| `/api/health` | GET | — | Estado del índice, modelo y modo |
| `/api/reset` | POST | — | Limpiar historial de la sesión actual |
| `/api/reload` | POST | — | Recargar índice FAISS sin reiniciar servidor |

---

## Tests

```bash
make test                                    # Todos los tests
venv\Scripts\pytest.exe tests/ -v           # Con salida detallada

# Por módulo
pytest tests/test_guardrails.py -v          # 26 tests — lógica pura
pytest tests/test_tools.py -v              # 31 tests — mocks FAISS
pytest tests/test_memory.py -v             # 26 tests — SQLite
pytest tests/test_api.py -v               # 19 tests — endpoints Flask
pytest tests/test_metrics.py -v           # métricas en memoria
pytest tests/test_feedback.py -v          # feedback SQLite + endpoint
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
├── app.py                     # Flask app, endpoints, métricas, cron cleanup
├── ingest.py                  # Indexación de PDFs → FAISS
├── manage.py                  # CLI: listar sesiones, cleanup, clear
├── gunicorn.conf.py           # Config producción (2 workers sync, preload_app)
├── src/
│   ├── agent.py               # Orquestador: ReAct vs RAG fallback
│   ├── agent_loop.py          # Bucle ReAct + generador SSE
│   ├── guardrails.py          # Filtro regex pre-LLM
│   ├── llm.py                 # Cliente HuggingFace InferenceClient
│   ├── memory.py              # Historial + feedback en SQLite
│   ├── schemas.py             # Pydantic: ConsultaRequest, DiagnosticoResponse
│   ├── tools.py               # 4 herramientas del agente ReAct
│   └── rag/
│       ├── embeddings.py      # Singleton SentenceTransformer
│       ├── retriever.py       # FAISS search (MIN_SCORE=0.25)
│       ├── reranker.py        # CrossEncoder reranker
│       ├── section_mapping.py # Página → capítulo por libro
│       └── semantic_fallback.py  # Fallback cuando rerank_score < threshold
├── templates/
│   ├── index.html             # UI chat (dark mode, voz, historial, feedback)
│   ├── metrics.html           # Dashboard métricas con Chart.js
│   └── login.html             # Página de autenticación
├── tests/                     # 120+ tests pytest
├── index/                     # Índice FAISS (generado por ingest.py, no incluido)
├── data/                      # SQLite memory.db (generado en runtime)
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
