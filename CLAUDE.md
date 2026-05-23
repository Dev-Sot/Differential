# MEDI-IA — Asistente Medico con RAG

Agente de diagnostico diferencial basado en libros medicos reales.
Pipeline: FAISS retriever → cross-encoder reranker multilingue → ReAct agent (Qwen2.5-7B via HuggingFace).

## Comandos del proyecto

```bash
# Requiere venv activado. El Makefile apunta a venv/Scripts/ (paths Windows)
make install        # pip install -r requirements.txt dentro del venv
make ingest         # Procesar PDFs y construir indice FAISS (tarda varios minutos)
make run            # Flask en localhost:5000 (debug=False)
make test           # pytest tests/ -v
make health         # GET /api/health (requiere servidor activo)
make reload         # POST /api/reload — recarga el indice FAISS sin reiniciar server

# Sesiones SQLite
make sessions       # Listar sesiones con turns y last_seen
make cleanup        # Eliminar sesiones inactivas >30 dias (DAYS=N para cambiar)

# Docker
make docker-build   # docker build -t medi-ia .
make docker-run     # docker compose up -d
make docker-stop    # docker compose down
make docker-ingest  # python ingest.py dentro del contenedor
```

Para correr sin Makefile:
```bash
venv/Scripts/python.exe app.py              # Windows
venv/Scripts/pytest.exe tests/ -v          # tests
venv/Scripts/python.exe ingest.py          # ingesta de PDFs
venv/Scripts/python.exe manage.py sessions # listar sesiones
venv/Scripts/python.exe manage.py cleanup --days 30
venv/Scripts/python.exe manage.py clear <session_id>
```

## Variables de entorno (.env)

```
HF_TOKEN=           # HuggingFace token — HABILITA el agente ReAct (Qwen2.5-7B)
HF_MODEL=           # Default: Qwen/Qwen2.5-7B-Instruct
SECRET_KEY=         # DEBE definirse en produccion — random invalida sesiones al reiniciar
AUTH_PASSWORD=      # Si se define, protege toda la app con password. Vacio = sin auth
RERANKER_MODEL=     # Default: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1
RERANK_THRESHOLD=   # Default: -3.0 (chunks relevantes > 0, irrelevantes < -3)
MEMORY_DB_PATH=     # Default: data/memory.db (relativo a la raiz del proyecto)
PORT=5000
FLASK_DEBUG=False
```

> El LLM es Qwen2.5-7B via HuggingFace InferenceClient (src/llm.py).
> ANTHROPIC_API_KEY fue removido de requirements.txt — no se usa en ningún archivo Python.

## Arquitectura de alto nivel

### Dos modos de ejecucion (src/agent.py)

```
HF_TOKEN presente  →  ReAct Agent (Qwen2.5-7B) + 4 tools + memoria multi-turn
HF_TOKEN ausente   →  RAG Template: solo FAISS+reranker, sin LLM, respuesta hardcodeada
```

El switch esta en `src/agent.py:run()`. Sin token el sistema funciona pero las respuestas
son fragmentos crudos del libro, no diagnostico diferencial.

### Pipeline completo

```
Consulta usuario
  → require_auth (app.py) — redirige a /login si AUTH_PASSWORD esta definida
  → Guardrails (src/guardrails.py) — filtra consultas no-medicas con regex
  → [Si ReAct] src/agent_loop.py:run_react() / stream_react()
      → Bucle max 6 iteraciones: Thought → Action → Observation
      → Tools: search_symptoms, assess_urgency, get_drug_info, get_section
      → LLM: Qwen2.5-7B via huggingface_hub.InferenceClient
  → [Si RAG] src/agent.py:_run_rag_fallback()
      → retrieve top-10 (FAISS IndexFlatIP cosine)
      → rerank top-5 (mmarco-mMiniLMv2-L12-H384-v1, multilingue 26 idiomas)
      → enrich_chunks (agrega nombre de seccion)
      → needs_fallback? (threshold: rerank_score < -3.0, configurable via RERANK_THRESHOLD)
```

### Endpoints

| Endpoint | Metodo | Descripcion |
|----------|--------|-------------|
| `/` | GET | UI chat |
| `/login` | GET | Pagina de login (solo si AUTH_PASSWORD definida) |
| `/auth/login` | POST | Autenticar — 5/min rate limit |
| `/auth/logout` | POST | Cerrar sesion |
| `/api/query` | POST | Consulta RAG/ReAct — 10/min |
| `/api/stream` | POST | SSE streaming del agente — 10/min |
| `/api/export/pdf` | POST | Exportar diagnostico como PDF — 5/min |
| `/api/health` | GET | Estado del sistema (indice, modelo, chunks) |
| `/api/reset` | POST | Limpiar historial de conversacion |
| `/api/reload` | POST | Recargar indice FAISS sin reiniciar |

### Modelos de ML en uso

| Modelo | Uso | Tamaño |
|--------|-----|--------|
| paraphrase-multilingual-MiniLM-L12-v2 | Embeddings para FAISS (ingesta + query) | ~400MB |
| cross-encoder/mmarco-mMiniLMv2-L12-H384-v1 | Reranker multilingue (mMARCO, 26 idiomas) | ~120MB |
| Qwen/Qwen2.5-7B-Instruct | LLM ReAct — llamado via HuggingFace Inference API | remoto |

Ambos sentence-transformers se cargan como singletons (globals en embeddings.py y reranker.py).
Se inicializan lazy al primer request — el primer query tarda 10-30s mientras se cargan.

### Memoria de sesion (src/memory.py)

- SQLite en `data/memory.db` — persiste reinicios del servidor
- Maximo 10 turnos por sesion (preserva system prompt siempre)
- Tabla `sessions` registra `last_seen` UTC para poder hacer cleanup
- `cleanup_old_sessions(days)` elimina sesiones inactivas — llamar via `manage.py cleanup`
- La sesion HTTP usa Flask session cookie — `SECRET_KEY` aleatorio invalida sesiones al reiniciar
- Configurable via `MEMORY_DB_PATH` para deploy personalizado

### Indice FAISS (index/)

- `index/books.index` — IndexFlatIP con vectores normalizados (cosine via inner product)
- `index/metadata.json` — lista de dicts con `{book, page, text}`
- Si el indice no existe, el servidor arranca y devuelve 503 al primer query (no crashea)
- `make reload` llama `POST /api/reload` que resetea `_index = None` y re-llama `_load()`

### Logging (app.py)

Cada request genera un `rid` de 8 chars. Formato en stdout (Docker-friendly):

```
2026-05-23T14:32:01 INFO  rid=a3f7b2c1 POST /api/stream 200 12ms
2026-05-23T14:32:04 INFO  rid=a3f7b2c1 stream_ms=3241 session=4e8d21a0 iters=4
2026-05-23T14:32:10 INFO  rid=b9d4e1f2 inference_ms=1870 session=4e8d21a0 mode=RAG Template
2026-05-23T14:33:05 WARN  rid=c1a2b3d4 auth_fail ip=192.168.1.10
```

## Estructura src/

```
src/
├── agent.py          Orquestador: decide ReAct vs RAG, exporta run() y get_health()
├── agent_loop.py     Bucle ReAct + stream_react() generador SSE de eventos tipados
├── guardrails.py     Filtro regex pre-LLM (keywords medicos vs no-medicos)
├── llm.py            Cliente HuggingFace InferenceClient (singleton _client) + chat_stream()
├── memory.py         Historial SQLite por session_id con cleanup de sesiones antiguas
├── schemas.py        Pydantic: ConsultaRequest, DiagnosticoResponse, ErrorResponse
├── tools.py          4 tools del agente + execute_tool() dispatcher
└── rag/
    ├── embeddings.py      Singleton SentenceTransformer (encode queries)
    ├── retriever.py       FAISS search, filtra score < 0.25
    ├── reranker.py        CrossEncoder singleton, modelo configurable via RERANKER_MODEL
    ├── section_mapping.py Mapeo pagina→capitulo (estatico, hardcoded por libro)
    └── semantic_fallback.py Fallback cuando top chunk.rerank_score < RERANK_THRESHOLD (-3.0)
```

## Tests (100 tests)

```bash
make test   # corre todos

# Por archivo
venv/Scripts/pytest.exe tests/test_guardrails.py -v   # 26 tests — logica pura, rapido
venv/Scripts/pytest.exe tests/test_tools.py -v        # 31 tests — mocks FAISS
venv/Scripts/pytest.exe tests/test_memory.py -v       # 26 tests — SQLite con tmp_path
venv/Scripts/pytest.exe tests/test_api.py -v          # 19 tests — endpoints Flask
```

`test_retriever.py` hace skip automatico si el indice no existe (`pytest.skip`). Es intencional.

## Deploy con Docker

```bash
# 1. Construir imagen
make docker-build

# 2. Crear .env con las variables necesarias (especialmente SECRET_KEY y HF_TOKEN)
cp .env.example .env

# 3. Levantar (requiere indice FAISS pre-construido en ./index/)
make docker-run

# Si el indice no existe, construirlo dentro del contenedor:
make docker-ingest

# Ver logs
docker compose logs -f

# Bajar
make docker-stop
```

Para nginx como reverse proxy, usar `nginx/medi-ia.conf` — tiene `proxy_buffering off`
para el endpoint SSE `/api/stream`.

## Libros indexados (deben estar en libros/ como PDFs)

- Harrison Principios De Medicina Interna 19 1
- Oxford Handbook of Clinical Medicine 10th Edition
- Symptoms to diagnosis  ← OJO: nombre exacto tiene espacio al final
- The Top 100 Drugs Clinical

El nombre exacto del libro viene del nombre del PDF sin extension. Si cambia el nombre
del archivo, hay que actualizar `section_mapping.py` Y el BOOK_MAP en `tools.py`.

## Invariantes criticos

1. **Guardrails primero**: `is_medical_query()` se llama antes del LLM en `/api/query` y `/api/stream`.
   Si una consulta medica valida se rechaza, revisar los regex en `guardrails.py`.

2. **Separador `|||`** en tools `assess_urgency` y `get_section`:
   El LLM debe generar `Input: sintomas|||contexto` / `Input: harrison|||tema`.
   Si el LLM no usa el separador, `execute_tool` lo maneja: usa todo el input como primer param.

3. **Score thresholds del pipeline RAG**:
   - FAISS MIN_SCORE = 0.25 (cosine similarity normalizado) — hardcoded en retriever.py
   - RERANK_THRESHOLD = -3.0 default (configurable via env)
   Chunks relevantes suelen marcar > 0; < -3 indica baja relevancia. Ajustar con
   queries reales: bajar hacia -6 si hay demasiados fallbacks, subir hacia 0 si hay falsos positivos.

4. **Chunk size = 400 chars / overlap = 80** en ingest.py. Si cambias esto, debes re-ingestar
   todos los PDFs — el indice existente se invalida.

5. **MAX_ITERATIONS = 6** en agent_loop.py. Si el LLM no produce "Final Answer:" en 6 ciclos,
   se hace un ultimo call forzado con todo el contexto acumulado.

6. **Tabla `sessions` en sync con `turns`**: `clear_session()` borra de ambas tablas.
   Si borras manualmente de `turns` sin borrar de `sessions`, el cleanup no funcionara correctamente.

## Lo que NO se debe hacer

- **No modificar el nombre exacto de los keys en SECTION_MAPS** en section_mapping.py sin
  actualizar tambien BOOK_MAP en tools.py. Son dos fuentes de verdad del mismo dato.
- **No borrar `index/books.index` sin re-ingestar** — el servidor devolvera 503 en el primer query.
- **No usar `session.permanent = True`** sin configurar `PERMANENT_SESSION_LIFETIME`.
- **No mockear el retriever en tests** sin el indice real presente — los tests de TestRetriever
  hacen skip automatico si el indice no existe (`pytest.skip`), esto es intencional.
- **No hardcodear session_id = "default"** en produccion — multiples usuarios compartiran
  la misma memoria de conversacion.
- **No borrar de `turns` directamente en SQL** sin borrar tambien de `sessions` — usa `clear_session()`.

## Agregar un libro nuevo

1. Copiar PDF a `libros/` con nombre limpio (sin caracteres especiales)
2. Agregar mapeo de secciones a `src/rag/section_mapping.py:SECTION_MAPS`
3. Actualizar `BOOK_MAP` en `src/tools.py` si quieres que `get_section` lo use por keyword
4. Ejecutar `make ingest` (re-indexa TODOS los libros desde cero)
5. Si server activo: `make reload`
