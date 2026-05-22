# MEDI-IA — Quick Wins Design Spec
**Fecha:** 2026-05-21  
**Estado:** Aprobado  
**Alcance:** 4 mejoras independientes sobre la base actual de MEDI-IA v4

---

## 1. Contexto

MEDI-IA es un asistente médico con pipeline RAG (FAISS + cross-encoder) y agente ReAct (Qwen2.5-7B via HuggingFace). El servidor es Flask. La memoria de conversación vive en RAM. Este spec cubre las 4 mejoras de "Quick Wins" priorizadas antes del trabajo de multi-agentes.

**Prioridad de implementación:** Streaming → PDF Export → Supabase → Rate Limiting

---

## 2. Mejora 1: Streaming SSE con razonamiento en vivo

### Objetivo
Eliminar el spinner de 20-30 segundos mostrando cada paso del agente ReAct (Thought, Tool call, Observation) y los tokens de la respuesta final en tiempo real.

### Decisiones tomadas
- **Transporte:** SSE via `fetch` + `ReadableStream` (no `EventSource` — requiere GET)
- **Modo:** Razonamiento en vivo + tokens de respuesta final
- **Endpoint existente `/api/query` se preserva** como fallback sin cambios

### Eventos SSE (formato `data: {json}\n\n`)

| type | campos adicionales | cuándo se emite |
|------|--------------------|-----------------|
| `thought` | `content`, `action` | Cada iteración del bucle ReAct |
| `tool_call` | `tool`, `input` | Antes de ejecutar cada tool |
| `observation` | `tool`, `content` | Resultado de cada tool (max 300 chars) |
| `final_start` | — | Señal de inicio de la respuesta final |
| `token` | `content` | Cada token del LLM (stream=True en HF) |
| `done` | `gravedad`, `gravedad_label`, `gravedad_color`, `gravedad_icon`, `condicion_principal`, `recomendacion`, `fuentes`, `confianza`, `modo`, `tools_used`, `respuesta` (texto completo), `trajectory` (top 3 pasos) | Al terminar |
| `error` | `message` | Si ocurre cualquier excepción |

### Archivos modificados

**`src/llm.py`**
- Agregar función `chat_stream(messages, max_tokens, temperature) -> Iterator[str]`
- Usa `InferenceClient.chat_completion(..., stream=True)` — ya soportado por `huggingface_hub`

**`src/agent_loop.py`**
- Agregar `stream_react(session_id, user_message) -> Iterator[dict]`
- `run_react()` existente no se toca
- El bucle ReAct hace `yield` de cada evento en el momento en lugar de acumular en `trajectory`
- Para la respuesta final usa `chat_stream()` y hace `yield {"type": "token", "content": chunk}` por cada token
- El evento `done` final incluye `respuesta` (texto completo acumulado de tokens) y `trajectory` (lista de los pasos emitidos)

**`src/agent.py`**
- Agregar `stream_rag_fallback(sintomas) -> Iterator[dict]` — envuelve `_run_rag_fallback()` en un generador que emite directamente el evento `done` (sin tokens individuales, el RAG no usa LLM streameable)

**`app.py`**
```python
@app.route("/api/stream", methods=["POST"])
@limiter.limit("20 per minute")
def stream_query():
    data = request.get_json()
    consulta = ConsultaRequest(message=data["message"])
    session_id = _get_session_id()

    def generate():
        try:
            if not is_medical_query(consulta.message):
                yield f"data: {json.dumps({'type': 'done', **refusal_result()})}\n\n"
                return
            # Con HF_TOKEN: agente ReAct con streaming de tokens
            # Sin HF_TOKEN: pipeline RAG envuelto en un generador que emite
            #               un único evento done (no hay tokens individuales)
            gen = stream_react(session_id, consulta.message) \
                  if HF_TOKEN else stream_rag_fallback(consulta.message)
            for event in gen:
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event["type"] == "done":
                    _save_query(session_id, consulta.message, event)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"}
    )
```

**`templates/index.html`**
- `sendMessage()` usa `fetch('/api/stream', {method:'POST',...})` con `response.body.getReader()`
- Buffer acumula chunks hasta `\n\n`, parsea cada evento JSON
- Handlers por tipo:
  - `thought` / `tool_call` / `observation` → puebla el panel de trajectory en tiempo real (ya existe en UI)
  - `token` → append al `card-body` en construcción
  - `done` → finaliza la card (gravedad pill, fuentes, botón PDF), habilita input
  - `error` → llama `addError()`

---

## 3. Mejora 2: Export PDF — Informe Clínico

### Objetivo
El usuario descarga un documento PDF de una página para llevar al médico real, con diagnóstico diferencial, razonamiento resumido y disclaimer legal.

### Contenido del PDF (formato Informe Clínico)

1. **Header verde** — logo MEDI-IA, fecha, ID de consulta, motor usado
2. **Barra de urgencia** — pill de gravedad + condición principal + barra de confianza
3. **Motivo de consulta** — síntomas tal como los describió el usuario
4. **Diagnóstico diferencial** — condición principal + condiciones relacionadas con su nivel de gravedad
5. **Razonamiento clínico** — top 3 pasos del trajectory (thoughts + tool calls, truncados a 150 chars)
6. **Fuentes bibliográficas** — chips con libro y página
7. **Recomendación** — en caja verde destacada
8. **Footer** — disclaimer legal + ID de consulta

### Implementación técnica

**Librería:** `weasyprint` — renderiza HTML+CSS a PDF en servidor

**`src/pdf_export.py`** (nuevo)
```python
def generate_pdf(data: dict) -> bytes:
    """Recibe el dict de respuesta del agente, retorna bytes del PDF."""
    html = _render_template(data)   # Jinja2 con el layout del informe
    return weasyprint.HTML(string=html).write_pdf()
```
- Template HTML embebido en el archivo (no archivo .html separado)
- Reutiliza el esquema de colores de la UI (emerald, urgency pills)
- ID de consulta: `uuid4()[:8].upper()`

**`app.py`** — nuevo endpoint:
```python
@app.route("/api/export-pdf", methods=["POST"])
@limiter.limit("10 per minute")
def export_pdf():
    data = request.get_json()
    pdf_bytes = generate_pdf(data)
    return Response(pdf_bytes, mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=medi-ia-{data.get('id','consulta')}.pdf"})
```

**`templates/index.html`** — botón PDF aparece en `card-foot` al recibir evento `type=done`:
```javascript
// En el handler de done:
const pdfBtn = `<button onclick="downloadPdf(${JSON.stringify(doneData)})">⬇ Informe PDF</button>`
```

---

## 4. Mejora 3: Persistencia con Supabase

### Objetivo
Reemplazar la memoria en RAM por Supabase (PostgreSQL) para que el historial de conversación sobreviva reinicios del servidor y se tenga analítica básica de consultas.

### Tablas Supabase

```sql
CREATE TABLE sessions (
  session_id    TEXT PRIMARY KEY,
  messages      JSONB    DEFAULT '[]',
  system_prompt TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE queries (
  id          SERIAL PRIMARY KEY,
  session_id  TEXT,
  symptoms    TEXT,
  gravedad    TEXT,
  confianza   FLOAT,
  modo        TEXT,
  tools_used  JSONB,
  created_at  TIMESTAMPTZ DEFAULT NOW()
);
```

### Archivos

**`src/db.py`** (nuevo) — singleton `get_db() -> Client` con patrón idéntico a `embeddings.py`

**`src/memory.py`** — interfaz pública sin cambios (`add_turn`, `get_history`, `set_system`, `clear_session`). Implementación interna: upsert/select a Supabase. **Fallback en RAM** si Supabase no está disponible (excepción → usa `defaultdict` original con log de warning).

**`app.py`** — `_save_query()` helper que inserta en tabla `queries` al recibir evento `done`.

### Variables de entorno nuevas
```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...
```

---

## 5. Mejora 4: Rate Limiting

### Implementación

**Librería:** `Flask-Limiter` con `storage_uri="memory://"` (sin Redis)

**Inicialización en `app.py`:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(get_remote_address, app=app, default_limits=["500 per day"])
```

**Límites por endpoint:**

| Endpoint | Límite |
|----------|--------|
| `POST /api/stream` | 20/minuto por IP |
| `POST /api/query` | 20/minuto por IP |
| `POST /api/export-pdf` | 10/minuto por IP |
| `POST /api/reset` | 30/minuto por IP |
| `GET /api/health` | Sin límite |

Respuesta automática `429 Too Many Requests` — la UI la captura con el `addError()` existente.

---

## 6. Variables de entorno finales (.env.example)

```bash
# ── LLM (HuggingFace) ─────────────────────────────────────
HF_TOKEN=               # Habilita agente ReAct. Sin esto: modo RAG template
HF_MODEL=Qwen/Qwen2.5-7B-Instruct

# ── Supabase ──────────────────────────────────────────────
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...     # anon key del proyecto Supabase

# ── Flask ─────────────────────────────────────────────────
SECRET_KEY=             # Obligatorio en producción
PORT=5000
FLASK_DEBUG=False

# ── Legacy (no usado actualmente) ─────────────────────────
CLAUDE_MODEL=claude-haiku-4-5-20251001
```

---

## 7. Resumen de cambios

| Archivo | Tipo | Cambio |
|---------|------|--------|
| `src/llm.py` | Modificado | Agregar `chat_stream()` con `stream=True` |
| `src/agent_loop.py` | Modificado | Agregar `stream_react()` generador |
| `src/memory.py` | Modificado | Reemplazar RAM por Supabase con fallback |
| `src/db.py` | Nuevo | Singleton cliente Supabase |
| `src/pdf_export.py` | Nuevo | `generate_pdf()` con weasyprint |
| `app.py` | Modificado | `/api/stream`, `/api/export-pdf`, Flask-Limiter, `_save_query()` |
| `templates/index.html` | Modificado | Streaming fetch, handlers por evento, botón PDF |
| `requirements.txt` | Modificado | + `supabase`, `flask-limiter`, `weasyprint` |
| `.env.example` | Modificado | + `SUPABASE_URL`, `SUPABASE_KEY` |

**Total:** 2 archivos nuevos · 7 modificados  
**Sin cambios:** todo el pipeline RAG, guardrails, tools, schemas, prompts, tests existentes, ingest.py

---

## 8. Lo que NO cubre este spec

- Autenticación de usuarios (Fase 4 del roadmap)
- Multi-agentes especializados (Fase 2 del roadmap)
- Voz / STT / TTS (Fase 3 del roadmap)
- Deploy / Docker / infraestructura productiva
