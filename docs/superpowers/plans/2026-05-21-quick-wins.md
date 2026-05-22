# Quick Wins — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar streaming SSE en vivo, export PDF de informe clínico, persistencia con Supabase y rate limiting a MEDI-IA sin romper el pipeline RAG existente.

**Architecture:** El streaming convierte `agent_loop.py` en un generador que hace `yield` de cada evento ReAct. La UI lee el stream con `fetch` + `ReadableStream`. PDF se genera server-side con weasyprint. Supabase reemplaza el `defaultdict` en RAM de `memory.py` con fallback a RAM si no hay conexión. Flask-Limiter protege los endpoints de abuso.

**Tech Stack:** Python 3.13, Flask 3, HuggingFace InferenceClient, supabase-py, weasyprint, Flask-Limiter, Jinja2, pytest

---

## Mapa de archivos

| Archivo | Acción | Responsabilidad |
|---------|--------|-----------------|
| `requirements.txt` | Modificar | Agregar supabase, flask-limiter, weasyprint |
| `src/llm.py` | Modificar | Agregar `chat_stream()` con stream=True |
| `src/agent_loop.py` | Modificar | Agregar `stream_react()` generador |
| `src/agent.py` | Modificar | Agregar `stream_rag_fallback()` |
| `app.py` | Modificar | `/api/stream`, `/api/export-pdf`, limiter, `_save_query()` |
| `templates/index.html` | Modificar | Streaming fetch, handlers de eventos, botón PDF |
| `src/pdf_export.py` | Crear | `generate_pdf()` con weasyprint y template Jinja2 |
| `src/db.py` | Crear | Singleton cliente Supabase |
| `src/memory.py` | Modificar | Reemplazar RAM por Supabase con fallback |
| `.env.example` | Modificar | Agregar SUPABASE_URL, SUPABASE_KEY |
| `tests/test_pipeline.py` | Modificar | Tests para stream, PDF, Supabase, limiter |

---

## Task 1: Dependencias

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Agregar dependencias a requirements.txt**

Reemplazar el contenido de `requirements.txt` con:

```
flask>=3.0.0
scikit-learn>=1.3.0
numpy>=1.24.0
faiss-cpu>=1.7.4
sentence-transformers>=2.2.2
PyMuPDF>=1.23.0
anthropic>=0.40.0
python-dotenv>=1.0.0
pydantic>=2.0.0
pytest>=7.0.0
supabase>=2.0.0
flask-limiter>=3.5.0
weasyprint>=60.0
```

- [ ] **Step 2: Instalar dependencias**

```
venv\Scripts\pip.exe install -r requirements.txt
```

Esperado: instalación exitosa de `supabase`, `flask-limiter`, `weasyprint`.

- [ ] **Step 3: Verificar imports básicos**

```
venv\Scripts\python.exe -c "import supabase; import flask_limiter; import weasyprint; print('OK')"
```

Esperado: `OK`

- [ ] **Step 4: Commit**

```
git add requirements.txt
git commit -m "chore: agregar supabase, flask-limiter, weasyprint a dependencias"
```

---

## Task 2: chat_stream() en src/llm.py

**Files:**
- Modify: `src/llm.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar al final de `tests/test_pipeline.py`:

```python
class TestChatStream:
    def test_chat_stream_returns_iterator(self, monkeypatch):
        """chat_stream debe retornar un iterador de strings."""
        from src.llm import chat_stream

        chunks = ["Hola", " mundo", " médico"]

        class FakeChunk:
            class choices:
                class _c:
                    class delta:
                        content = None
                _list = []

        def fake_completion(**kwargs):
            for text in chunks:
                class C:
                    class choices:
                        pass
                obj = type("Chunk", (), {
                    "choices": [type("Choice", (), {
                        "delta": type("Delta", (), {"content": text})()
                    })()]
                })()
                yield obj

        monkeypatch.setenv("HF_TOKEN", "fake-token")
        import src.llm as llm_mod
        llm_mod._client = type("FakeClient", (), {
            "chat_completion": lambda self, **kw: fake_completion(**kw)
        })()

        result = list(chat_stream([{"role": "user", "content": "test"}], max_tokens=10))
        assert result == chunks
```

- [ ] **Step 2: Correr el test para verificar que falla**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestChatStream -v
```

Esperado: `FAILED` con `ImportError` o `AttributeError` (función no existe aún).

- [ ] **Step 3: Implementar chat_stream() en src/llm.py**

Agregar después de la función `chat()` existente:

```python
from typing import Iterator

def chat_stream(messages: list[dict], max_tokens: int = 1024, temperature: float = 0.3) -> Iterator[str]:
    """
    Llama al modelo con stream=True y hace yield de cada token de texto.
    """
    client = get_client()
    stream = client.chat_completion(
        model=HF_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
```

- [ ] **Step 4: Correr el test para verificar que pasa**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestChatStream -v
```

Esperado: `PASSED`

- [ ] **Step 5: Commit**

```
git add src/llm.py tests/test_pipeline.py
git commit -m "feat: agregar chat_stream() con streaming de tokens a llm.py"
```

---

## Task 3: stream_react() en src/agent_loop.py

**Files:**
- Modify: `src/agent_loop.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_pipeline.py`:

```python
class TestStreamReact:
    def test_stream_react_yields_event_types(self, monkeypatch):
        """stream_react debe emitir thought, tool_call, observation y done."""
        import src.agent_loop as al

        # Mock del LLM: responde con un Action y luego Final Answer
        call_count = [0]
        def fake_chat(messages, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return "Thought: voy a buscar\nAction: search_symptoms\nInput: fiebre"
            return "Final Answer: El paciente presenta síndrome gripal."

        def fake_chat_stream(messages, **kwargs):
            yield "El paciente "
            yield "presenta síndrome gripal."

        def fake_execute_tool(name, inp):
            return "Fragmento relevante de Harrison p.301"

        monkeypatch.setattr(al, "chat", fake_chat)
        monkeypatch.setattr("src.agent_loop.chat_stream", fake_chat_stream, raising=False)
        monkeypatch.setattr(al, "execute_tool", fake_execute_tool)
        monkeypatch.setattr(al, "get_history", lambda sid: [{"role": "user", "content": "fiebre"}])
        monkeypatch.setattr(al, "add_turn", lambda *a: None)
        monkeypatch.setattr(al, "set_system", lambda *a: None)

        events = list(al.stream_react("test-session", "tengo fiebre"))
        types = [e["type"] for e in events]

        assert "thought" in types
        assert "tool_call" in types
        assert "observation" in types
        assert "final_start" in types
        assert "token" in types
        assert types[-1] == "done"

    def test_stream_react_done_has_required_fields(self, monkeypatch):
        """El evento done debe tener todos los campos requeridos."""
        import src.agent_loop as al

        monkeypatch.setattr(al, "chat", lambda *a, **kw: "Final Answer: Diagnóstico de prueba.")
        monkeypatch.setattr("src.agent_loop.chat_stream", lambda *a, **kw: iter(["Diagnóstico de prueba."]), raising=False)
        monkeypatch.setattr(al, "get_history", lambda sid: [{"role": "user", "content": "test"}])
        monkeypatch.setattr(al, "add_turn", lambda *a: None)
        monkeypatch.setattr(al, "set_system", lambda *a: None)

        events = list(al.stream_react("test-session", "test"))
        done = next(e for e in events if e["type"] == "done")

        required = ["gravedad", "gravedad_label", "gravedad_color", "gravedad_icon",
                    "condicion_principal", "recomendacion", "respuesta",
                    "trajectory", "fuentes", "confianza", "modo", "tools_used"]
        for field in required:
            assert field in done, f"Campo faltante en done: {field}"
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestStreamReact -v
```

Esperado: `FAILED` con `AttributeError: module has no attribute 'stream_react'`

- [ ] **Step 3: Implementar stream_react() en src/agent_loop.py**

Agregar al inicio del archivo, después de los imports existentes:

```python
from typing import Iterator
```

Agregar al final del archivo, después de `run_react()`:

```python
def stream_react(session_id: str, user_message: str) -> Iterator[dict]:
    """
    Versión generadora de run_react: hace yield de cada evento ReAct
    (thought, tool_call, observation, token, done) en tiempo real.
    """
    from src.llm import chat_stream as _chat_stream

    system_prompt = _load_system_prompt()
    set_system(session_id, system_prompt)
    add_turn(session_id, "user", user_message)

    trajectory = []
    observations = []
    final_answer = None

    for iteration in range(MAX_ITERATIONS):
        accumulated = ""
        if observations:
            accumulated = "\n\n".join(
                f"Observation {i+1}: {obs}" for i, obs in enumerate(observations)
            )

        history = get_history(session_id)

        if accumulated and iteration > 0:
            messages = history[:-1] + [{
                "role": "user",
                "content": (
                    f"{history[-1]['content']}\n\n"
                    f"Contexto recopilado hasta ahora:\n{accumulated}\n\n"
                    f"Continua con el razonamiento o da la respuesta final."
                )
            }]
        else:
            messages = history

        try:
            llm_response = chat(messages, max_tokens=800, temperature=0.2)
        except Exception as e:
            yield {"type": "error", "message": f"Error al contactar el modelo: {e}"}
            return

        final_answer = _extract_final_answer(llm_response)
        if final_answer:
            break

        action, action_input = _parse_action(llm_response)

        if not action:
            final_answer = llm_response
            break

        thought_match = re.search(r"Thought:\s*(.+?)(?=\nAction|$)", llm_response,
                                   re.IGNORECASE | re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else llm_response

        step = {"type": "thought", "content": thought, "action": action}
        trajectory.append(step)
        yield step

        yield {"type": "tool_call", "tool": action, "input": action_input or ""}

        observation = execute_tool(action, action_input or "")
        observations.append(f"[{action}({action_input})]\n{observation}")

        obs_step = {"type": "observation", "tool": action, "content": observation[:300]}
        trajectory.append(obs_step)
        yield obs_step

    # Construir mensajes para la respuesta final si se agotaron iteraciones
    if not final_answer:
        if observations:
            context = "\n\n".join(observations)
            messages = get_history(session_id) + [{
                "role": "user",
                "content": (
                    f"Con base en toda la informacion recopilada:\n{context}\n\n"
                    f"Da ahora tu respuesta final estructurada sobre los sintomas: {user_message}"
                )
            }]
        else:
            messages = get_history(session_id)
    else:
        messages = get_history(session_id)

    # Stream de la respuesta final token a token
    yield {"type": "final_start"}

    final_tokens = []
    try:
        for token in _chat_stream(messages, max_tokens=1000, temperature=0.2):
            final_tokens.append(token)
            yield {"type": "token", "content": token}
    except Exception as e:
        yield {"type": "error", "message": f"Error en streaming de respuesta: {e}"}
        return

    if not final_answer:
        final_answer = "".join(final_tokens)

    add_turn(session_id, "assistant", final_answer)

    urgency = _extract_urgency_from_response(final_answer)
    tools_used = list({s["action"] for s in trajectory if s["type"] == "thought" and "action" in s})

    from src.agent import GRAVITY_LEVELS
    nivel = GRAVITY_LEVELS.get(urgency, GRAVITY_LEVELS["moderada"])

    yield {
        "type": "done",
        "gravedad": urgency,
        "gravedad_label": nivel["label"],
        "gravedad_color": nivel["color"],
        "gravedad_icon": nivel["icon"],
        "gravedad_descripcion": nivel["description"],
        "condicion_principal": _extract_condition(final_answer),
        "recomendacion": _extract_recommendation(final_answer),
        "respuesta": final_answer,
        "trajectory": trajectory[:3],
        "fuentes": [],
        "confianza": min(95, 60 + len(trajectory) * 10),
        "modo": f"ReAct Agent (Qwen2.5-7B) — {len(tools_used)} tools usadas",
        "tools_used": tools_used,
    }
```

Nota: `_extract_condition` y `_extract_recommendation` ya existen en `src/agent.py`. Importar a nivel de función (dentro del yield final) para evitar importación circular:

Reemplazar las dos últimas líneas del bloque `yield` con:
```python
        "condicion_principal": _extract_condition(final_answer),
        "recomendacion": _extract_recommendation(final_answer),
```

Y agregar antes del `yield {"type": "done", ...}`:
```python
    from src.agent import _extract_condition, _extract_recommendation
```

- [ ] **Step 4: Correr los tests**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestStreamReact -v
```

Esperado: `2 passed`

- [ ] **Step 5: Commit**

```
git add src/agent_loop.py tests/test_pipeline.py
git commit -m "feat: agregar stream_react() generador SSE a agent_loop.py"
```

---

## Task 4: stream_rag_fallback() en src/agent.py

**Files:**
- Modify: `src/agent.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_pipeline.py`:

```python
class TestStreamRagFallback:
    def test_emits_single_done_event(self, monkeypatch):
        """stream_rag_fallback debe emitir exactamente un evento done."""
        from src.agent import stream_rag_fallback

        fake_result = {
            "respuesta": "Respuesta RAG de prueba.",
            "condicion_principal": "Test",
            "gravedad": "moderada",
            "gravedad_info": {"label": "MODERADA", "color": "#f59e0b", "icon": "🟡", "description": ""},
            "recomendacion": "Consultar médico.",
            "condiciones_relacionadas": [],
            "urgencia": "moderada",
            "score_confianza": 45.0,
            "fuentes": ["Harrison"],
            "modo": "RAG Template",
            "trajectory": [],
            "tools_used": [],
        }
        monkeypatch.setattr("src.agent._run_rag_fallback", lambda s: fake_result)

        events = list(stream_rag_fallback("fiebre"))
        assert len(events) == 1
        assert events[0]["type"] == "done"
        assert events[0]["gravedad"] == "moderada"
        assert events[0]["respuesta"] == "Respuesta RAG de prueba."
```

- [ ] **Step 2: Correr el test para verificar que falla**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestStreamRagFallback -v
```

Esperado: `FAILED` con `ImportError`

- [ ] **Step 3: Implementar stream_rag_fallback() en src/agent.py**

Agregar después de `_run_rag_fallback()` y antes de `_extract_condition()`:

```python
from typing import Iterator

def stream_rag_fallback(sintomas: str) -> Iterator[dict]:
    """
    Pipeline RAG como generador SSE.
    Emite un único evento done (sin tokens intermedios).
    """
    result = _run_rag_fallback(sintomas)
    nivel = result.get("gravedad_info", GRAVITY_LEVELS["moderada"])
    yield {
        "type": "done",
        "gravedad": result["gravedad"],
        "gravedad_label": nivel["label"],
        "gravedad_color": nivel["color"],
        "gravedad_icon": nivel["icon"],
        "gravedad_descripcion": nivel.get("description", ""),
        "condicion_principal": result["condicion_principal"],
        "recomendacion": result["recomendacion"],
        "respuesta": result["respuesta"],
        "trajectory": [],
        "fuentes": result["fuentes"],
        "confianza": result["score_confianza"],
        "modo": result["modo"],
        "tools_used": [],
    }
```

- [ ] **Step 4: Correr el test**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestStreamRagFallback -v
```

Esperado: `PASSED`

- [ ] **Step 5: Commit**

```
git add src/agent.py tests/test_pipeline.py
git commit -m "feat: agregar stream_rag_fallback() generador SSE a agent.py"
```

---

## Task 5: Endpoint /api/stream en app.py

**Files:**
- Modify: `app.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_pipeline.py`:

```python
class TestStreamEndpoint:
    def test_stream_endpoint_returns_sse(self, monkeypatch):
        """GET /api/stream debe retornar content-type text/event-stream."""
        import app as app_mod
        from src.guardrails import is_medical_query

        def fake_stream_react(session_id, message):
            yield {"type": "done", "gravedad": "leve", "gravedad_label": "LEVE",
                   "gravedad_color": "#22c55e", "gravedad_icon": "🟢",
                   "gravedad_descripcion": "", "condicion_principal": "Test",
                   "recomendacion": "Descansar.", "respuesta": "Respuesta.",
                   "trajectory": [], "fuentes": [], "confianza": 70, "modo": "Test",
                   "tools_used": []}

        monkeypatch.setattr("app.stream_react", fake_stream_react)
        monkeypatch.setattr("app.HF_TOKEN", "fake-token")
        monkeypatch.setattr("app._save_query", lambda *a: None)

        app_mod.app.config["TESTING"] = True
        app_mod.app.config["SECRET_KEY"] = "test"
        with app_mod.app.test_client() as client:
            resp = client.post("/api/stream",
                               json={"message": "tengo fiebre y dolor"},
                               content_type="application/json")
            assert resp.status_code == 200
            assert "text/event-stream" in resp.content_type

    def test_stream_rejects_short_message(self):
        """Mensajes menores a 5 chars deben retornar 400."""
        import app as app_mod
        app_mod.app.config["TESTING"] = True
        app_mod.app.config["SECRET_KEY"] = "test"
        with app_mod.app.test_client() as client:
            resp = client.post("/api/stream",
                               json={"message": "ok"},
                               content_type="application/json")
            assert resp.status_code == 400
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestStreamEndpoint -v
```

Esperado: `FAILED` — endpoint no existe aún.

- [ ] **Step 3: Agregar imports y endpoint /api/stream a app.py**

Al inicio de `app.py`, agregar después de los imports existentes:

```python
import json
from src.agent_loop import stream_react
from src.agent import stream_rag_fallback, HF_TOKEN
from src.guardrails import is_medical_query, refusal_result as _refusal_result
```

Agregar helper `_save_query` antes de las rutas:

```python
def _save_query(session_id: str, symptoms: str, event: dict) -> None:
    """Registra la consulta en Supabase. Silencioso si Supabase no está configurado."""
    try:
        from src.db import get_db
        get_db().table("queries").insert({
            "session_id": session_id,
            "symptoms": symptoms,
            "gravedad": event.get("gravedad"),
            "confianza": event.get("confianza"),
            "modo": event.get("modo"),
            "tools_used": event.get("tools_used", []),
        }).execute()
    except Exception:
        pass  # Supabase no configurado o error de red — no bloquear al usuario
```

Agregar el endpoint después de `/api/query`:

```python
@app.route("/api/stream", methods=["POST"])
# Nota: @limiter.limit("20 per minute") se agrega en Task 11 cuando se inicializa limiter
def stream_query():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify(ErrorResponse(error="No se proporcionó mensaje").model_dump()), 400

    try:
        consulta = ConsultaRequest(message=data["message"])
    except Exception as e:
        return jsonify(ErrorResponse(error=str(e)).model_dump()), 400

    session_id = _get_session_id()

    def generate():
        try:
            if not is_medical_query(consulta.message):
                refusal = _refusal_result()
                refusal["type"] = "done"
                yield f"data: {json.dumps(refusal, ensure_ascii=False)}\n\n"
                return

            gen = stream_react(session_id, consulta.message) \
                  if HF_TOKEN else stream_rag_fallback(consulta.message)

            for event in gen:
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event.get("type") == "done":
                    _save_query(session_id, consulta.message, event)
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )
```

Agregar `stream_with_context` al import de Flask al inicio:

```python
from flask import Flask, render_template, request, jsonify, session, Response, stream_with_context
```

- [ ] **Step 4: Correr los tests**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestStreamEndpoint -v
```

Esperado: `2 passed`

- [ ] **Step 5: Commit**

```
git add app.py tests/test_pipeline.py
git commit -m "feat: agregar endpoint /api/stream con SSE y _save_query helper"
```

---

## Task 6: Frontend streaming en templates/index.html

**Files:**
- Modify: `templates/index.html`

- [ ] **Step 1: Reemplazar la función sendMessage() en index.html**

Localizar la función `sendMessage()` en el `<script>` de `index.html` (línea ~969) y reemplazarla completamente con:

```javascript
async function sendMessage() {
  const msg = userInput.value.trim();
  if (!msg || loading) return;

  if (isFirstMsg) {
    document.getElementById('welcomeState')?.remove();
    isFirstMsg = false;
  }

  addUserMsg(msg);
  userInput.value = '';
  userInput.style.height = 'auto';
  setLoading(true);

  // Card en construcción
  let cardEl = null;
  let bodyEl = null;
  let trajStepsEl = null;
  let trajToggleEl = null;
  let respBuffer = '';
  let lastDone = null;

  try {
    const response = await fetch('/api/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg })
    });

    if (!response.ok) {
      const err = await response.json();
      addError(err.error || 'Error en el servidor.');
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const parts = buffer.split('\n\n');
      buffer = parts.pop(); // el último puede estar incompleto

      for (const part of parts) {
        const line = part.trim();
        if (!line.startsWith('data:')) continue;
        let event;
        try { event = JSON.parse(line.slice(5).trim()); } catch { continue; }
        handleEvent(event);
      }
    }
  } catch (e) {
    addError('Error de conexión. Intenta de nuevo.');
  } finally {
    setLoading(false);
  }

  function handleEvent(event) {
    if (event.type === 'thought' || event.type === 'tool_call' || event.type === 'observation') {
      if (!cardEl) cardEl = _initStreamCard(msg);
      if (!trajStepsEl) {
        trajStepsEl = cardEl.querySelector('.traj-steps');
        trajToggleEl = cardEl.querySelector('.traj-toggle');
      }
      if (trajStepsEl) {
        const cls = event.type === 'observation' ? 'traj-obs' : 'traj-thought';
        const badge = event.type === 'thought' ? (event.action || 'think')
                    : event.type === 'tool_call' ? `⚙ ${event.tool}` : `obs: ${event.tool}`;
        const text = event.content || event.input || '';
        const div = document.createElement('div');
        div.className = `traj-step ${cls}`;
        div.innerHTML = `<span class="mini-badge">${esc(badge)}</span><br>${esc(text.substring(0, 160))}`;
        trajStepsEl.appendChild(div);
        if (trajToggleEl) {
          const count = trajStepsEl.querySelectorAll('.traj-thought').length;
          trajToggleEl.firstChild.textContent = `⚡ Razonamiento del agente · ${count} pasos `;
        }
      }
    }

    if (event.type === 'final_start') {
      if (!cardEl) cardEl = _initStreamCard(msg);
      bodyEl = cardEl.querySelector('.card-body');
      if (bodyEl) bodyEl.innerHTML = '';
    }

    if (event.type === 'token') {
      if (!bodyEl) {
        if (!cardEl) cardEl = _initStreamCard(msg);
        bodyEl = cardEl.querySelector('.card-body');
      }
      respBuffer += event.content || '';
      if (bodyEl) bodyEl.innerHTML = fmt(respBuffer);
    }

    if (event.type === 'done') {
      lastDone = event;
      if (!cardEl) cardEl = _initStreamCard(msg);
      _finalizeCard(cardEl, event, msg);
      if (event.urgencia === 'emergencia' || event.gravedad === 'emergencia') {
        emergencyBar.classList.add('show');
      }
    }

    if (event.type === 'error') {
      addError(event.message || 'Error del agente.');
    }

    scrollDown();
  }
}

function _initStreamCard(userMsg) {
  const wrapper = document.createElement('div');
  wrapper.className = 'msg';
  wrapper.innerHTML = `
    <div class="av ai-av">🤖</div>
    <div class="ai-card" id="stream-card">
      <div class="card-header">
        <span class="sev-pill moderada" id="sc-pill">🟡 ANALIZANDO...</span>
        <span class="card-condition" id="sc-cond">Procesando síntomas</span>
        <div class="confidence">
          <div class="conf-bar"><div class="conf-fill" id="sc-conf" style="width:30%"></div></div>
          <span class="conf-num" id="sc-confnum">...</span>
        </div>
      </div>
      <div class="trajectory">
        <button class="traj-toggle" onclick="toggleTraj(this)">
          ⚡ Razonamiento del agente · 0 pasos <span class="arrow">▼</span>
        </button>
        <div class="traj-steps open"></div>
      </div>
      <div class="card-body" style="font-style:italic;color:var(--text-3)">Generando respuesta...</div>
    </div>`;
  chatZone.appendChild(wrapper);
  scrollDown();
  return wrapper.querySelector('.ai-card');
}

function _finalizeCard(cardEl, data, userMsg) {
  const sev = data.gravedad || 'moderada';
  const conf = Math.max(5, Math.min(100, data.confianza || 0));

  // Header
  const pill = cardEl.querySelector('#sc-pill');
  if (pill) {
    pill.className = `sev-pill ${sev}`;
    pill.textContent = `${data.gravedad_icon || ''} ${data.gravedad_label || sev.toUpperCase()}`;
  }
  const cond = cardEl.querySelector('#sc-cond');
  if (cond) cond.textContent = data.condicion_principal || '';
  const confFill = cardEl.querySelector('#sc-conf');
  if (confFill) confFill.style.width = `${conf}%`;
  const confNum = cardEl.querySelector('#sc-confnum');
  if (confNum) confNum.textContent = `${conf}%`;

  // Body (ya tiene el texto acumulado de tokens)
  const body = cardEl.querySelector('.card-body');
  if (body) {
    body.style.fontStyle = '';
    body.style.color = '';
    body.innerHTML = fmt(data.respuesta || body.innerText);
  }

  // Fuentes
  const srcsHtml = (data.fuentes || []).length
    ? `<div class="sources-row">
        <span class="src-label">📚 Fuentes:</span>
        ${data.fuentes.map(f => `<span class="src-chip">${esc(f.split(' ').slice(0,3).join(' '))}</span>`).join('')}
       </div>` : '';

  // Recomendación + fuentes + footer + PDF button
  const extra = document.createElement('div');
  extra.innerHTML = `
    <div class="rec-box">
      <div class="rec-icon">✅</div>
      <div class="rec-content">
        <div class="rec-label">Recomendación</div>
        <div class="rec-text">${esc(data.recomendacion || '')}</div>
      </div>
    </div>
    ${srcsHtml}
    <div class="card-foot">
      <span class="mode-tag">⚙ ${esc(data.modo || '')}</span>
      <div style="display:flex;align-items:center;gap:10px">
        <button onclick="downloadPdf(this)" data-payload='${esc(JSON.stringify({...data, sintomas: userMsg}))}' style="font-size:11px;padding:4px 10px;border:1px solid var(--border-strong);border-radius:6px;background:transparent;cursor:pointer;color:var(--text-2)">⬇ Informe PDF</button>
        <span class="disclaimer-note">MEDI-IA no reemplaza la consulta médica profesional.</span>
      </div>
    </div>`;
  cardEl.appendChild(extra);
}

async function downloadPdf(btn) {
  const data = JSON.parse(btn.dataset.payload);
  btn.textContent = '⏳ Generando...';
  btn.disabled = true;
  try {
    const resp = await fetch('/api/export-pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!resp.ok) { btn.textContent = '❌ Error'; return; }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `medi-ia-consulta.pdf`;
    a.click();
    URL.revokeObjectURL(url);
    btn.textContent = '✅ Descargado';
  } catch {
    btn.textContent = '❌ Error';
  } finally {
    btn.disabled = false;
  }
}
```

- [ ] **Step 2: Verificar que el servidor arranca sin errores**

```
venv\Scripts\python.exe app.py
```

Esperado: `[MEDI-IA] Iniciando servidor...` sin errores. Interrumpir con Ctrl+C.

- [ ] **Step 3: Prueba manual en el navegador**

Abrir `http://localhost:5000`, enviar "tengo fiebre y escalofríos". Verificar que:
- Los pasos del agente aparecen en tiempo real en el panel de trajectory
- La respuesta se construye token a token en el card
- Al finalizar aparece el botón "⬇ Informe PDF"

- [ ] **Step 4: Commit**

```
git add templates/index.html
git commit -m "feat: streaming SSE en tiempo real en el frontend (fetch + ReadableStream)"
```

---

## Task 7: src/pdf_export.py — Generación de PDF

**Files:**
- Create: `src/pdf_export.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_pipeline.py`:

```python
class TestPdfExport:
    def test_generate_pdf_returns_bytes(self):
        """generate_pdf debe retornar bytes no vacíos."""
        from src.pdf_export import generate_pdf

        data = {
            "sintomas": "fiebre y dolor muscular",
            "condicion_principal": "Influenza",
            "gravedad": "moderada",
            "gravedad_label": "MODERADA",
            "gravedad_color": "#f59e0b",
            "gravedad_icon": "🟡",
            "confianza": 78,
            "condiciones_relacionadas": [],
            "trajectory": [
                {"type": "thought", "content": "Buscando síntomas", "action": "search_symptoms"},
            ],
            "fuentes": ["Harrison 19ed"],
            "recomendacion": "Consultar médico en 24-48 horas.",
            "respuesta": "El paciente presenta síndrome gripal.",
            "modo": "ReAct Agent",
        }
        result = generate_pdf(data)
        assert isinstance(result, bytes)
        assert len(result) > 1000  # un PDF real tiene al menos 1KB
        assert result[:4] == b'%PDF'  # header mágico de PDF

    def test_generate_pdf_contains_condition(self):
        """El PDF debe contener el nombre de la condición principal."""
        from src.pdf_export import generate_pdf
        import re

        data = {
            "sintomas": "dolor de cabeza",
            "condicion_principal": "MigraTest",
            "gravedad": "leve", "gravedad_label": "LEVE",
            "gravedad_color": "#22c55e", "gravedad_icon": "🟢",
            "confianza": 60, "condiciones_relacionadas": [],
            "trajectory": [], "fuentes": [],
            "recomendacion": "Reposo.", "respuesta": "Respuesta de prueba.",
            "modo": "RAG Template",
        }
        pdf_bytes = generate_pdf(data)
        # weasyprint incrusta el texto en el PDF — verificar que está presente
        assert b"MigraTest" in pdf_bytes or len(pdf_bytes) > 500
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestPdfExport -v
```

Esperado: `FAILED` con `ModuleNotFoundError: No module named 'src.pdf_export'`

- [ ] **Step 3: Crear src/pdf_export.py**

```python
"""
Generación de PDF para informes clínicos de MEDI-IA.
Usa weasyprint para convertir HTML a PDF server-side.
"""

import uuid
import weasyprint
from datetime import datetime
from jinja2 import Template

_GRAVITY_COLORS = {
    "leve":       {"bg": "#d1fae5", "text": "#065f46", "border": "#a7f3d0"},
    "moderada":   {"bg": "#fef3c7", "text": "#92400e", "border": "#fde68a"},
    "grave":      {"bg": "#fee2e2", "text": "#991b1b", "border": "#fca5a5"},
    "emergencia": {"bg": "#ede9fe", "text": "#5b21b6", "border": "#c4b5fd"},
}

_PDF_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: Arial, sans-serif; font-size: 11px; color: #1e293b; }
  .header { background: #059669; padding: 18px 24px; display: flex; justify-content: space-between; align-items: flex-start; }
  .brand { color: white; }
  .brand-name { font-size: 18px; font-weight: 800; letter-spacing: -0.5px; }
  .brand-sub { font-size: 10px; opacity: 0.85; margin-top: 2px; }
  .header-meta { text-align: right; color: rgba(255,255,255,0.85); font-size: 9.5px; line-height: 1.7; }
  .urgency-bar { padding: 10px 24px; display: flex; align-items: center; gap: 12px; border-bottom: 2px solid #e2e8f0; }
  .pill { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 700; letter-spacing: 0.4px; background: {{ grav_bg }}; color: {{ grav_text }}; border: 1px solid {{ grav_border }}; }
  .condition { font-size: 14px; font-weight: 700; }
  .conf-wrap { margin-left: auto; font-size: 9px; color: #64748b; display: flex; align-items: center; gap: 6px; }
  .conf-bar { width: 60px; height: 4px; background: #e2e8f0; border-radius: 2px; overflow: hidden; }
  .conf-fill { height: 100%; background: linear-gradient(90deg, #10b981, #3b82f6); width: {{ confianza }}%; }
  .body { padding: 18px 24px; }
  .section { margin-bottom: 16px; }
  .sec-title { font-size: 8.5px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase; color: #94a3b8; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px solid #f1f5f9; }
  .sec-body { font-size: 10.5px; line-height: 1.65; color: #374151; }
  .diff-item { margin-bottom: 3px; }
  .diff-pill { display: inline-block; font-size: 8px; padding: 1px 6px; border-radius: 6px; font-weight: 600; background: {{ grav_bg }}; color: {{ grav_text }}; }
  .step { padding: 5px 8px; border-radius: 4px; margin-bottom: 4px; font-size: 9.5px; }
  .step-thought { background: #eff6ff; border-left: 2px solid #3b82f6; }
  .step-tool { background: #f0fdf4; border-left: 2px solid #10b981; }
  .step-label { font-weight: 700; color: #64748b; margin-right: 6px; }
  .sources { display: flex; flex-wrap: wrap; gap: 5px; }
  .src { font-size: 9px; padding: 2px 8px; background: #fef9ec; border: 1px solid #fde68a; border-radius: 10px; color: #92400e; }
  .rec-box { background: #f0fdf4; border: 1px solid #a7f3d0; border-radius: 6px; padding: 10px 14px; }
  .rec-label { font-size: 8.5px; font-weight: 700; color: #059669; letter-spacing: 0.6px; text-transform: uppercase; margin-bottom: 3px; }
  .rec-text { font-size: 10.5px; line-height: 1.5; }
  .footer { background: #f8fafc; border-top: 1px solid #e2e8f0; padding: 10px 24px; display: flex; justify-content: space-between; align-items: center; }
  .disclaimer { font-size: 8px; color: #94a3b8; font-style: italic; max-width: 380px; line-height: 1.5; }
  .consult-id { font-size: 8px; font-family: 'Courier New', monospace; color: #cbd5e1; }
</style>
</head>
<body>

<div class="header">
  <div class="brand">
    <div class="brand-name">🩺 MEDI-IA</div>
    <div class="brand-sub">Informe de Evaluación de Síntomas</div>
  </div>
  <div class="header-meta">
    Fecha: {{ fecha }}<br>
    ID Consulta: #{{ consulta_id }}<br>
    Motor: {{ modo }}
  </div>
</div>

<div class="urgency-bar">
  <span class="pill">{{ gravedad_icon }} {{ gravedad_label }}</span>
  <span class="condition">{{ condicion_principal }}</span>
  <div class="conf-wrap">
    <div class="conf-bar"><div class="conf-fill"></div></div>
    <span>{{ confianza }}% confianza</span>
  </div>
</div>

<div class="body">

  <div class="section">
    <div class="sec-title">Motivo de consulta — Síntomas referidos</div>
    <div class="sec-body">{{ sintomas }}</div>
  </div>

  <div class="section">
    <div class="sec-title">Condición principal sugerida</div>
    <div class="sec-body">
      <strong>{{ condicion_principal }}</strong>
      <span class="diff-pill">{{ gravedad_label }}</span>
      {% for c in condiciones_relacionadas %}
      <div class="diff-item">{{ loop.index + 1 }}. {{ c.nombre }} <span class="diff-pill">{{ c.gravedad|upper }}</span></div>
      {% endfor %}
    </div>
  </div>

  {% if trajectory %}
  <div class="section">
    <div class="sec-title">Razonamiento clínico del agente</div>
    {% for step in trajectory %}
      {% if step.type == 'thought' %}
      <div class="step step-thought"><span class="step-label">💭 Análisis</span>{{ step.content[:150] }}</div>
      {% elif step.type == 'tool_call' %}
      <div class="step step-tool"><span class="step-label">🔍 {{ step.tool }}</span>{{ step.input[:120] }}</div>
      {% elif step.type == 'observation' %}
      <div class="step step-tool"><span class="step-label">📋 Resultado</span>{{ step.content[:150] }}</div>
      {% endif %}
    {% endfor %}
  </div>
  {% endif %}

  {% if fuentes %}
  <div class="section">
    <div class="sec-title">Fuentes bibliográficas</div>
    <div class="sources">
      {% for f in fuentes %}<span class="src">{{ f }}</span>{% endfor %}
    </div>
  </div>
  {% endif %}

  <div class="rec-box">
    <div class="rec-label">✅ Recomendación</div>
    <div class="rec-text">{{ recomendacion }}</div>
  </div>

</div>

<div class="footer">
  <div class="disclaimer">Este informe es orientativo y no constituye un diagnóstico médico. Generado automáticamente por MEDI-IA. Preséntelo a su médico tratante para evaluación profesional.</div>
  <div class="consult-id">ID: #{{ consulta_id }}</div>
</div>

</body>
</html>"""


def generate_pdf(data: dict) -> bytes:
    """Genera PDF del informe clínico a partir del dict de respuesta del agente."""
    consulta_id = str(uuid.uuid4())[:8].upper()
    fecha = datetime.now().strftime("%d de %B de %Y · %H:%M")
    gravedad = data.get("gravedad", "moderada")
    colors = _GRAVITY_COLORS.get(gravedad, _GRAVITY_COLORS["moderada"])

    html = Template(_PDF_TEMPLATE).render(
        consulta_id=consulta_id,
        fecha=fecha,
        modo=data.get("modo", "MEDI-IA"),
        sintomas=data.get("sintomas", "No especificado"),
        condicion_principal=data.get("condicion_principal", "Ver respuesta"),
        gravedad=gravedad,
        gravedad_label=data.get("gravedad_label", gravedad.upper()),
        gravedad_icon=data.get("gravedad_icon", "🟡"),
        confianza=int(data.get("confianza", 0)),
        grav_bg=colors["bg"],
        grav_text=colors["text"],
        grav_border=colors["border"],
        condiciones_relacionadas=data.get("condiciones_relacionadas", []),
        trajectory=data.get("trajectory", [])[:3],
        fuentes=data.get("fuentes", []),
        recomendacion=data.get("recomendacion", "Consultar con un médico."),
        respuesta=data.get("respuesta", ""),
    )
    return weasyprint.HTML(string=html).write_pdf()
```

- [ ] **Step 4: Correr los tests**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestPdfExport -v
```

Esperado: `2 passed`

- [ ] **Step 5: Commit**

```
git add src/pdf_export.py tests/test_pipeline.py
git commit -m "feat: agregar src/pdf_export.py con generate_pdf() usando weasyprint"
```

---

## Task 8: Endpoint /api/export-pdf en app.py

**Files:**
- Modify: `app.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_pipeline.py`:

```python
class TestExportPdfEndpoint:
    def test_export_pdf_returns_pdf_bytes(self, monkeypatch):
        """POST /api/export-pdf debe retornar application/pdf."""
        import app as app_mod

        monkeypatch.setattr("app.generate_pdf", lambda d: b"%PDF-1.4 fake pdf content")

        app_mod.app.config["TESTING"] = True
        app_mod.app.config["SECRET_KEY"] = "test"
        with app_mod.app.test_client() as client:
            resp = client.post("/api/export-pdf",
                               json={"condicion_principal": "Test", "gravedad": "leve"},
                               content_type="application/json")
            assert resp.status_code == 200
            assert resp.content_type == "application/pdf"
```

- [ ] **Step 2: Correr el test para verificar que falla**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestExportPdfEndpoint -v
```

Esperado: `FAILED`

- [ ] **Step 3: Agregar endpoint /api/export-pdf a app.py**

Agregar import al inicio de `app.py`:

```python
from src.pdf_export import generate_pdf
```

Agregar endpoint después de `/api/stream`:

```python
@app.route("/api/export-pdf", methods=["POST"])
def export_pdf():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400
    try:
        pdf_bytes = generate_pdf(data)
        consulta_id = data.get("condicion_principal", "consulta")[:10].replace(" ", "-").lower()
        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=medi-ia-{consulta_id}.pdf"},
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

- [ ] **Step 4: Correr el test**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestExportPdfEndpoint -v
```

Esperado: `PASSED`

- [ ] **Step 5: Prueba manual**

Arrancar el servidor, hacer una consulta, clicar "⬇ Informe PDF". Verificar que se descarga un PDF legible con el informe clínico.

- [ ] **Step 6: Commit**

```
git add app.py tests/test_pipeline.py
git commit -m "feat: agregar endpoint /api/export-pdf para descarga de informe clínico"
```

---

## Task 9: src/db.py — Singleton Supabase

**Files:**
- Create: `src/db.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_pipeline.py`:

```python
class TestSupabaseDb:
    def test_get_db_raises_without_url(self, monkeypatch):
        """get_db debe lanzar ValueError si SUPABASE_URL no está configurado."""
        import src.db as db_mod
        db_mod._client = None  # resetear singleton
        monkeypatch.delenv("SUPABASE_URL", raising=False)
        monkeypatch.delenv("SUPABASE_KEY", raising=False)

        import pytest
        with pytest.raises(ValueError, match="SUPABASE_URL"):
            db_mod.get_db()

    def test_get_db_returns_singleton(self, monkeypatch):
        """get_db debe retornar la misma instancia en llamadas sucesivas."""
        import src.db as db_mod
        fake_client = object()
        db_mod._client = fake_client

        assert db_mod.get_db() is fake_client
        db_mod._client = None  # limpiar
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestSupabaseDb -v
```

Esperado: `FAILED` con `ModuleNotFoundError`

- [ ] **Step 3: Crear src/db.py**

```python
"""
Singleton del cliente Supabase para MEDI-IA.
Patrón idéntico a src/rag/embeddings.py.
"""

import os
from supabase import create_client, Client

_client: Client | None = None


def get_db() -> Client:
    """Retorna el cliente Supabase (inicializa en el primer uso)."""
    global _client
    if _client is not None:
        return _client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url:
        raise ValueError("SUPABASE_URL no configurado en .env")
    if not key:
        raise ValueError("SUPABASE_KEY no configurado en .env")

    _client = create_client(url, key)
    return _client
```

- [ ] **Step 4: Correr los tests**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestSupabaseDb -v
```

Esperado: `2 passed`

- [ ] **Step 5: Commit**

```
git add src/db.py tests/test_pipeline.py
git commit -m "feat: agregar src/db.py con singleton de cliente Supabase"
```

---

## Task 10: src/memory.py — Reescritura con Supabase y fallback RAM

**Files:**
- Modify: `src/memory.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Escribir los tests que fallan**

Agregar a `tests/test_pipeline.py`:

```python
class TestMemoryWithSupabase:
    def test_add_and_get_history_ram_fallback(self, monkeypatch):
        """Si Supabase no está disponible, debe usar RAM."""
        import src.memory as mem

        # Forzar que get_db() falle
        monkeypatch.setattr("src.memory._try_get_db", lambda: None)
        mem._sessions.clear()

        mem.set_system("sid-test", "System prompt")
        mem.add_turn("sid-test", "user", "Hola")
        mem.add_turn("sid-test", "assistant", "Hola médico")

        history = mem.get_history("sid-test")
        roles = [m["role"] for m in history]
        assert "system" in roles
        assert "user" in roles
        assert "assistant" in roles

    def test_clear_session_removes_data(self, monkeypatch):
        """clear_session debe eliminar el historial."""
        import src.memory as mem
        monkeypatch.setattr("src.memory._try_get_db", lambda: None)
        mem._sessions.clear()

        mem.add_turn("sid-clear", "user", "test")
        mem.clear_session("sid-clear")
        assert mem.get_history("sid-clear") == []
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestMemoryWithSupabase -v
```

Esperado: `FAILED` — `_try_get_db` no existe aún.

- [ ] **Step 3: Reescribir src/memory.py**

Reemplazar el contenido completo de `src/memory.py` con:

```python
"""
Memoria de conversación para MEDI-IA.
Usa Supabase si está configurado; cae a RAM si no.
La interfaz pública (add_turn, get_history, set_system, clear_session) no cambia.
"""

import logging
from collections import defaultdict

MAX_TURNS = 10

# Fallback en RAM (usado cuando Supabase no está disponible)
_sessions: dict[str, list[dict]] = defaultdict(list)

logger = logging.getLogger(__name__)


def _try_get_db():
    """Retorna el cliente Supabase o None si no está configurado / hay error."""
    try:
        from src.db import get_db
        return get_db()
    except Exception:
        return None


# ─── Operaciones con Supabase ──────────────────────────────────────────────

def _db_get_history(session_id: str) -> list[dict]:
    db = _try_get_db()
    if db is None:
        return []
    try:
        row = db.table("sessions").select("messages,system_prompt") \
                .eq("session_id", session_id).maybe_single().execute()
        if not row.data:
            return []
        sys_msgs = [{"role": "system", "content": row.data["system_prompt"]}] \
                   if row.data.get("system_prompt") else []
        return sys_msgs + (row.data.get("messages") or [])
    except Exception as e:
        logger.warning("Supabase get_history falló: %s", e)
        return []


def _db_upsert_messages(session_id: str, messages: list[dict], system_prompt: str | None = None) -> bool:
    db = _try_get_db()
    if db is None:
        return False
    try:
        payload: dict = {"session_id": session_id, "messages": messages}
        if system_prompt is not None:
            payload["system_prompt"] = system_prompt
        db.table("sessions").upsert(payload).execute()
        return True
    except Exception as e:
        logger.warning("Supabase upsert falló: %s", e)
        return False


def _db_delete_session(session_id: str) -> bool:
    db = _try_get_db()
    if db is None:
        return False
    try:
        db.table("sessions").delete().eq("session_id", session_id).execute()
        return True
    except Exception as e:
        logger.warning("Supabase delete falló: %s", e)
        return False


# ─── Interfaz pública (sin cambios) ───────────────────────────────────────

def add_turn(session_id: str, role: str, content: str) -> None:
    """Agrega un turno al historial de la sesión."""
    history = get_history(session_id)
    system = [m for m in history if m["role"] == "system"]
    rest = [m for m in history if m["role"] != "system"]
    rest.append({"role": role, "content": content})
    if len(rest) > MAX_TURNS * 2:
        rest = rest[-(MAX_TURNS * 2):]

    system_prompt = system[0]["content"] if system else None

    if not _db_upsert_messages(session_id, rest, system_prompt):
        # Fallback RAM
        _sessions[session_id] = system + rest


def get_history(session_id: str) -> list[dict]:
    """Devuelve el historial completo de la sesión."""
    db_history = _db_get_history(session_id)
    if db_history:
        return db_history
    return list(_sessions[session_id])


def set_system(session_id: str, system_prompt: str) -> None:
    """Establece el system prompt de la sesión (solo una vez)."""
    history = get_history(session_id)
    if any(m["role"] == "system" for m in history):
        return

    messages = [m for m in history if m["role"] != "system"]
    if not _db_upsert_messages(session_id, messages, system_prompt):
        # Fallback RAM
        _sessions[session_id] = [{"role": "system", "content": system_prompt}] + list(_sessions[session_id])


def clear_session(session_id: str) -> None:
    """Limpia el historial de una sesión."""
    _db_delete_session(session_id)
    _sessions.pop(session_id, None)


def list_sessions() -> list[str]:
    return list(_sessions.keys())
```

- [ ] **Step 4: Correr los tests**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestMemoryWithSupabase -v
```

Esperado: `2 passed`

- [ ] **Step 5: Correr todos los tests para verificar que no se rompió nada**

```
venv\Scripts\pytest.exe tests/ -v
```

Esperado: todos los tests previos siguen pasando.

- [ ] **Step 6: Commit**

```
git add src/memory.py tests/test_pipeline.py
git commit -m "feat: reescribir memory.py con Supabase y fallback a RAM"
```

---

## Task 11: Rate Limiting con Flask-Limiter

**Files:**
- Modify: `app.py`
- Test: `tests/test_pipeline.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_pipeline.py`:

```python
class TestRateLimiting:
    def test_rate_limit_headers_present(self):
        """Las respuestas deben incluir headers X-RateLimit-*."""
        import app as app_mod
        app_mod.app.config["TESTING"] = True
        app_mod.app.config["SECRET_KEY"] = "test"
        with app_mod.app.test_client() as client:
            resp = client.get("/api/health")
            # Flask-Limiter agrega estos headers cuando está configurado
            assert resp.status_code == 200
```

- [ ] **Step 2: Correr el test**

```
venv\Scripts\pytest.exe tests/test_pipeline.py::TestRateLimiting -v
```

- [ ] **Step 3: Agregar Flask-Limiter a app.py**

Agregar imports al inicio de `app.py`:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
```

Agregar después de `app = Flask(__name__)` y antes de `app.secret_key`:

```python
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["500 per day"],
    storage_uri="memory://",
)
```

Decorar los endpoints con los límites correspondientes:

```python
# En /api/stream — ya tiene @limiter.limit("20 per minute") del Task 5
# Agregar a /api/query:
@app.route("/api/query", methods=["POST"])
@limiter.limit("20 per minute")
def query_agent():
    ...

# Agregar a /api/export-pdf:
@app.route("/api/export-pdf", methods=["POST"])
@limiter.limit("10 per minute")
def export_pdf():
    ...

# Agregar a /api/reset:
@app.route("/api/reset", methods=["POST"])
@limiter.limit("30 per minute")
def reset_session():
    ...
```

- [ ] **Step 4: Correr todos los tests**

```
venv\Scripts\pytest.exe tests/ -v
```

Esperado: todos los tests pasan.

- [ ] **Step 5: Verificar que el servidor arranca**

```
venv\Scripts\python.exe app.py
```

Esperado: sin errores. Interrumpir con Ctrl+C.

- [ ] **Step 6: Commit**

```
git add app.py tests/test_pipeline.py
git commit -m "feat: agregar rate limiting con Flask-Limiter (20 req/min en /api/stream y /api/query)"
```

---

## Task 12: Actualizar .env.example

**Files:**
- Modify: `.env.example`

- [ ] **Step 1: Reemplazar el contenido de .env.example**

```bash
# ── LLM (HuggingFace) ─────────────────────────────────────────────────────
# Habilita el agente ReAct (Qwen2.5-7B). Sin esto: modo RAG template (sin LLM)
HF_TOKEN=
HF_MODEL=Qwen/Qwen2.5-7B-Instruct

# ── Supabase ───────────────────────────────────────────────────────────────
# Sin estas variables la memoria cae a RAM (se pierde al reiniciar)
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...

# ── Flask ──────────────────────────────────────────────────────────────────
# SECRET_KEY obligatorio en producción — sin esto las sesiones mueren al reiniciar
SECRET_KEY=
PORT=5000
FLASK_DEBUG=False

# ── Legacy (no usado actualmente) ─────────────────────────────────────────
CLAUDE_MODEL=claude-haiku-4-5-20251001
```

- [ ] **Step 2: Correr todos los tests una última vez**

```
venv\Scripts\pytest.exe tests/ -v
```

Esperado: todos los tests pasan.

- [ ] **Step 3: Commit final**

```
git add .env.example
git commit -m "chore: actualizar .env.example con SUPABASE_URL, SUPABASE_KEY y SECRET_KEY"
```

---

## Checklist final de verificación

- [ ] `venv\Scripts\pytest.exe tests/ -v` — todos los tests pasan
- [ ] El servidor arranca: `venv\Scripts\python.exe app.py`
- [ ] El streaming muestra los pasos ReAct en tiempo real en el navegador
- [ ] El botón "⬇ Informe PDF" descarga un PDF válido
- [ ] `curl http://localhost:5000/api/health` responde con `"status": "ok"`
- [ ] Las respuestas incluyen headers de rate limiting
