# MEDI-IA — Asistente Medico con RAG

Agente de diagnostico diferencial basado en libros medicos reales.
Pipeline: FAISS retriever → cross-encoder reranker → ReAct agent (Qwen2.5-7B via HuggingFace).

## Comandos del proyecto

```bash
# Requiere venv activado. El Makefile apunta a venv/Scripts/ (paths Windows)
make install    # pip install -r requirements.txt dentro del venv
make ingest     # Procesar PDFs y construir indice FAISS (tarda varios minutos)
make run        # Flask en localhost:5000 (debug=False)
make test       # pytest tests/ -v
make health     # GET /api/health (requiere servidor activo)
make reload     # POST /api/reload — recarga el indice FAISS sin reiniciar server
```

Para correr sin Makefile:
```bash
venv/Scripts/python.exe app.py          # Windows
venv/Scripts/pytest.exe tests/ -v       # tests
venv/Scripts/python.exe ingest.py       # ingesta de PDFs
```

## Variables de entorno (.env)

```
HF_TOKEN=          # HuggingFace token — HABILITA el agente ReAct (Qwen2.5-7B)
HF_MODEL=          # Default: Qwen/Qwen2.5-7B-Instruct
PORT=5000
FLASK_DEBUG=False
SECRET_KEY=        # Si no se pone, se genera random en cada arranque (invalida sesiones)
```

> ANTHROPIC_API_KEY aparece en .env.example pero NO se usa en ningún archivo Python.
> El LLM real es Qwen2.5-7B via HuggingFace InferenceClient (src/llm.py).

## Arquitectura de alto nivel

### Dos modos de ejecucion (src/agent.py:31-32)

```
HF_TOKEN presente  →  ReAct Agent (Qwen2.5-7B) + 4 tools + memoria multi-turn
HF_TOKEN ausente   →  RAG Template: solo FAISS+reranker, sin LLM, respuesta hardcodeada
```

El switch esta en `src/agent.py:run()`. Sin token el sistema funciona pero las respuestas
son fragmentos crudos del libro, no diagnostico diferencial.

### Pipeline RAG completo

```
Consulta usuario
  → Guardrails (src/guardrails.py) — filtra consultas no-medicas con regex
  → [Si ReAct] src/agent_loop.py:run_react()
      → Bucle max 6 iteraciones: Thought → Action → Observation
      → Tools disponibles: search_symptoms, assess_urgency, get_drug_info, get_section
      → LLM: Qwen2.5-7B via huggingface_hub.InferenceClient
  → [Si RAG] src/agent.py:_run_rag_fallback()
      → retrieve top-10 (FAISS IndexFlatIP cosine)
      → rerank top-5 (cross-encoder ms-marco-MiniLM-L-6-v2)
      → enrich_chunks (agrega nombre de seccion)
      → needs_fallback? (threshold: rerank_score < -9.0)
```

### Modelos de ML en uso

| Modelo | Uso | Tamaño |
|--------|-----|--------|
| paraphrase-multilingual-MiniLM-L12-v2 | Embeddings para FAISS (ingesta + query) | ~400MB |
| cross-encoder/ms-marco-MiniLM-L-6-v2 | Reranker — modelo INGLES sobre texto español/ingles | ~80MB |
| Qwen/Qwen2.5-7B-Instruct | LLM ReAct — llamado via HuggingFace Inference API | remoto |

Ambos sentence-transformers se cargan como singletons (globals en embeddings.py y reranker.py).
Se inicializan lazy al primer request — el primer query tarda 10-30s mientras se cargan.

### Memoria de sesion (src/memory.py)

- RAM pura: `defaultdict(list)` — se pierde al reiniciar el servidor
- Maximo 10 turnos por sesion (preserva system prompt)
- La sesion HTTP usa Flask session cookie — `SECRET_KEY` aleatorio invalida sesiones al reiniciar
- No hay persistencia de sesiones en disco

### Indice FAISS (index/)

- `index/books.index` — IndexFlatIP con vectores normalizados (cosine via inner product)
- `index/metadata.json` — lista de dicts con `{book, page, text}`
- Si el indice no existe, el servidor arranca bien pero explota al primer query
- `make reload` llama `POST /api/reload` que resetea `_index = None` y re-llama `_load()`

## Estructura src/

```
src/
├── agent.py          Orquestador: decide ReAct vs RAG, exporta run() y get_health()
├── agent_loop.py     Bucle ReAct: parse Thought/Action/Input/Observation del LLM
├── guardrails.py     Filtro regex pre-LLM (keywords medicos vs no-medicos)
├── llm.py            Cliente HuggingFace InferenceClient (singleton _client)
├── memory.py         Historial en RAM por session_id
├── schemas.py        Pydantic: ConsultaRequest, DiagnosticoResponse, ErrorResponse
├── tools.py          4 tools del agente + execute_tool() dispatcher
└── rag/
    ├── embeddings.py      Singleton SentenceTransformer (encode queries)
    ├── retriever.py       FAISS search, filtra score < 0.25
    ├── reranker.py        CrossEncoder singleton, umbral -9.0 en needs_fallback
    ├── section_mapping.py Mapeo pagina→capitulo (estatico, hardcoded por libro)
    └── semantic_fallback.py Fallback cuando top chunk.rerank_score < -9.0
```

## Libros indexados (deben estar en libros/ como PDFs)

- Harrison Principios De Medicina Interna 19 1
- Oxford Handbook of Clinical Medicine 10th Edition
- Symptoms to diagnosis  ← OJO: nombre exacto tiene espacio al final
- The Top 100 Drugs Clinical

El nombre exacto del libro viene del nombre del PDF sin extension. Si cambia el nombre
del archivo, hay que actualizar `section_mapping.py` Y el BOOK_MAP en `tools.py:82`.

## Invariantes criticos

1. **Guardrails primero**: `is_medical_query()` se llama antes del LLM en `agent.py:28`.
   Si una consulta medica valida se rechaza, revisar los regex en `guardrails.py:7`.

2. **Separador `|||`** en tools `assess_urgency` y `get_section`:
   El LLM debe generar `Input: sintomas|||contexto` / `Input: harrison|||tema`.
   Si el LLM no usa el separador, `execute_tool` lo maneja: usa todo el input como primer param.

3. **Score thresholds calibrados para el modelo English ms-marco sobre texto español**:
   - FAISS MIN_SCORE = 0.25 (cosine similarity normalizado)
   - Reranker RERANK_THRESHOLD = -9.0 (ms-marco devuelve scores muy negativos para texto no-ingles)
   No cambiar estos valores sin revaluar con queries reales.

4. **Chunk size = 400 chars / overlap = 80** en ingest.py. Si cambias esto, debes re-ingestar
   todos los PDFs — el indice existente se invalida.

5. **MAX_ITERATIONS = 6** en agent_loop.py. Si el LLM no produce "Final Answer:" en 6 ciclos,
   se hace un ultimo call forzado con todo el contexto acumulado.

## Lo que NO se debe hacer

- **No usar `anthropic` SDK** — el paquete esta en requirements.txt como legacy pero no hay
  codigo que lo importe. Agregar llamadas a Claude romperia el flujo esperado del LLM.
- **No modificar el nombre exacto de los keys en SECTION_MAPS** en section_mapping.py sin
  actualizar tambien BOOK_MAP en tools.py. Son dos fuentes de verdad del mismo dato.
- **No borrar `index/books.index` sin re-ingestar** — el servidor arrancara pero crasheara
  en el primer query con FileNotFoundError.
- **No usar `session.permanent = True`** sin configurar `PERMANENT_SESSION_LIFETIME` —
  las sesiones de Flask son cookies de sesion por defecto (expiran al cerrar navegador).
- **No mockear el retriever en tests** sin el indice real presente — los tests de TestRetriever
  hacen skip automatico si el indice no existe (`pytest.skip`), esto es intencional.
- **No hardcodear session_id = "default"** en produccion — multiples usuarios compartiran
  la misma memoria de conversacion.

## Agregar un libro nuevo

1. Copiar PDF a `libros/` con nombre limpio (sin caracteres especiales)
2. Agregar mapeo de secciones a `src/rag/section_mapping.py:SECTION_MAPS`
3. Actualizar `BOOK_MAP` en `src/tools.py:82` si quieres que `get_section` lo use por keyword
4. Ejecutar `make ingest` (re-indexa TODOS los libros desde cero)
5. Si server activo: `make reload`
