# Features Innovadores v1.0 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar 4 features a MEDI-IA — TTS, perfil clínico modal, visualización pipeline RAG animada y cuerpo humano SVG interactivo — para impresionar en presentación académica.

**Architecture:** Todo en `templates/index.html` (CSS + HTML + JS). Sin cambios en Python. Datos RAG ya disponibles en `data.rag_chunks`. Perfil en `sessionStorage`. TTS vía Web Speech API nativa. SVG inline para el cuerpo humano.

**Tech Stack:** HTML/CSS/JS vanilla, Lucide icons, Web Speech API (`SpeechSynthesis`), SVG inline. Sin dependencias nuevas.

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `templates/index.html` | Todas las tareas — CSS, HTML, JS |

---

## Task 1: TTS — Respuesta por Voz

**Files:**
- Modify: `templates/index.html`

### CSS

- [ ] **Step 1: Agregar CSS para botones TTS**

Busca el bloque `.theme-btn {` (alrededor de línea 1010) y agrega **después** de él:

```css
  /* ===== TTS ===== */
  .tts-global-btn {
    display: flex;
    align-items: center;
    padding: 6px 8px;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    cursor: pointer;
    color: var(--text-3);
    transition: all 0.15s;
  }
  .tts-global-btn:hover { background: var(--surface-2); color: var(--text-2); }
  .tts-global-btn.active {
    color: var(--em);
    border-color: var(--border-em);
    background: var(--em-dim);
    animation: tts-pulse 2s ease-in-out infinite;
  }
  @keyframes tts-pulse {
    0%,100% { box-shadow: 0 0 0 0 rgba(16,185,129,0); }
    50%      { box-shadow: 0 0 0 4px rgba(16,185,129,0.12); }
  }
  .tts-card-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 10.5px;
    padding: 4px 8px;
    background: var(--surface-2);
    border: 1px solid var(--border-md);
    border-radius: 6px;
    color: var(--text-2);
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    transition: all 0.15s;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .tts-card-btn:hover { background: var(--em-dim); border-color: var(--border-em); color: var(--em); }
  .tts-card-btn.speaking { color: var(--em); border-color: var(--border-em); background: var(--em-dim); }
```

### HTML — Topbar

- [ ] **Step 2: Agregar botón TTS global en el topbar**

Localiza en el HTML del topbar (busca `id="themeToggle"`). Reemplaza:

```html
      <button class="theme-btn" id="themeToggle" onclick="toggleTheme()" title="Cambiar tema">
        <i data-lucide="sun" id="themeIcon" style="width:15px;height:15px;stroke-width:2"></i>
      </button>
```

Por:

```html
      <button class="tts-global-btn" id="ttsGlobalBtn" onclick="toggleTTSGlobal()" title="Modo manos libres — leer respuestas automáticamente">
        <i data-lucide="volume-2" id="ttsGlobalIcon" style="width:15px;height:15px;stroke-width:2"></i>
      </button>
      <button class="theme-btn" id="themeToggle" onclick="toggleTheme()" title="Cambiar tema">
        <i data-lucide="sun" id="themeIcon" style="width:15px;height:15px;stroke-width:2"></i>
      </button>
```

### HTML — Card footer (en addAICard)

- [ ] **Step 3: Agregar botón TTS por respuesta en addAICard**

En la función `addAICard` (línea ~1552), localiza donde se declaran los IDs al inicio:

```js
  const exportBtnId  = 'expbtn_'   + Date.now();
  const copyBtnId    = 'copybtn_'  + Date.now();
  const detailsBtnId = 'detbtn_'   + Date.now();
  const panelId      = 'detpanel_' + Date.now();
  const feedbackId   = 'fb_'       + Date.now();
```

Reemplaza por:

```js
  const exportBtnId  = 'expbtn_'   + Date.now();
  const copyBtnId    = 'copybtn_'  + Date.now();
  const ttsBtnId     = 'ttsbtn_'   + Date.now();
  const detailsBtnId = 'detbtn_'   + Date.now();
  const panelId      = 'detpanel_' + Date.now();
  const feedbackId   = 'fb_'       + Date.now();
```

- [ ] **Step 4: Agregar botón TTS en el HTML del card footer**

En el template string de `addAICard`, localiza la línea del botón copiar dentro de `.card-foot`:

```js
        <button class="copy-btn" id="${copyBtnId}"><i data-lucide="copy" style="width:12px;height:12px"></i> Copiar</button>
```

Reemplaza por:

```js
        <button class="copy-btn" id="${copyBtnId}"><i data-lucide="copy" style="width:12px;height:12px"></i> Copiar</button>
        <button class="tts-card-btn" id="${ttsBtnId}" title="Escuchar respuesta"><i data-lucide="volume-2" style="width:12px;height:12px"></i> Escuchar</button>
```

### JS — Funciones TTS

- [ ] **Step 5: Agregar bloque JS de TTS**

Antes de la línea `lucide.createIcons();` al final del `<script>`, agregar:

```js
// ===== TTS =====
let _ttsEnabled = localStorage.getItem('medi-tts-enabled') === 'true';
let _currentUtterance = null;
let _ttsAvailable = false;

function initTTS() {
  if (!window.speechSynthesis) return;
  // Esperar a que las voces carguen
  const checkVoices = () => {
    const voices = speechSynthesis.getVoices();
    const esVoice = voices.find(v => v.lang.startsWith('es'));
    if (esVoice || voices.length > 0) {
      _ttsAvailable = true;
      _syncTTSGlobalBtn();
      if (!esVoice) console.warn('TTS: no hay voz en español, usando voz por defecto');
    }
  };
  speechSynthesis.onvoiceschanged = checkVoices;
  checkVoices();
}

function _getSpanishVoice() {
  const voices = speechSynthesis.getVoices();
  return voices.find(v => v.lang.startsWith('es')) || voices[0] || null;
}

function _syncTTSGlobalBtn() {
  const btn = document.getElementById('ttsGlobalBtn');
  if (!btn) return;
  if (!_ttsAvailable) { btn.style.display = 'none'; return; }
  btn.classList.toggle('active', _ttsEnabled);
  const icon = btn.querySelector('i');
  if (icon) {
    icon.setAttribute('data-lucide', _ttsEnabled ? 'volume-2' : 'volume-x');
    lucide.createIcons({ nodes: [icon] });
  }
}

function toggleTTSGlobal() {
  if (!_ttsAvailable) return;
  _ttsEnabled = !_ttsEnabled;
  localStorage.setItem('medi-tts-enabled', _ttsEnabled);
  _syncTTSGlobalBtn();
  if (!_ttsEnabled) stopSpeaking();
}

function stopSpeaking() {
  if (window.speechSynthesis) speechSynthesis.cancel();
  _currentUtterance = null;
  // Resetear todos los botones TTS de cards activas
  document.querySelectorAll('.tts-card-btn.speaking').forEach(btn => {
    btn.classList.remove('speaking');
    const icon = btn.querySelector('i');
    if (icon) { icon.setAttribute('data-lucide', 'volume-2'); lucide.createIcons({ nodes: [icon] }); }
  });
}

function _extractCleanText(data) {
  let text = (data.respuesta || '').replace(/\*\*/g, '').replace(/\*/g, '').replace(/#/g, '');
  const words = text.split(/\s+/);
  if (words.length > 500) {
    // Leer solo primer párrafo + recomendación si existe
    const firstPara = text.split('\n\n')[0] || text.substring(0, 600);
    const recomIdx = text.search(/recomendaci[oó]n|conclusi[oó]n/i);
    const recomText = recomIdx > -1 ? text.substring(recomIdx, recomIdx + 400) : '';
    text = firstPara + (recomText ? '. ' + recomText : '');
  }
  if (data.recomendacion) text += '. Recomendación: ' + data.recomendacion;
  return text.trim();
}

function speakResponse(data, cardBtnId) {
  if (!_ttsAvailable) return;
  stopSpeaking();

  const btn = cardBtnId ? document.getElementById(cardBtnId) : null;
  const text = _extractCleanText(data);
  if (!text) return;

  const utterance = new SpeechSynthesisUtterance(text);
  const voice = _getSpanishVoice();
  if (voice) utterance.voice = voice;
  utterance.lang = voice?.lang || 'es-ES';
  utterance.rate = 0.95;
  _currentUtterance = utterance;

  if (btn) {
    btn.classList.add('speaking');
    const icon = btn.querySelector('i');
    if (icon) { icon.setAttribute('data-lucide', 'volume-x'); lucide.createIcons({ nodes: [icon] }); }
  }

  utterance.onend = utterance.onerror = () => {
    _currentUtterance = null;
    if (btn) {
      btn.classList.remove('speaking');
      const icon = btn.querySelector('i');
      if (icon) { icon.setAttribute('data-lucide', 'volume-2'); lucide.createIcons({ nodes: [icon] }); }
    }
  };

  speechSynthesis.speak(utterance);
}

function toggleCardTTS(data, cardBtnId) {
  if (!_ttsAvailable) return;
  const btn = document.getElementById(cardBtnId);
  if (btn?.classList.contains('speaking')) {
    stopSpeaking();
  } else {
    speakResponse(data, cardBtnId);
  }
}
```

### JS — Wire up auto-speak y event listener

- [ ] **Step 6: Ocultar botón TTS si no hay soporte y wire up event listener en addAICard**

En `addAICard`, después de la línea:

```js
  document.getElementById(copyBtnId)?.addEventListener('click', function() { copyResponse(data, this); });
```

Agrega:

```js
  const ttsBtn = document.getElementById(ttsBtnId);
  if (ttsBtn) {
    if (!_ttsAvailable) {
      ttsBtn.style.display = 'none';
    } else {
      ttsBtn.addEventListener('click', () => toggleCardTTS(data, ttsBtnId));
    }
  }
```

- [ ] **Step 7: Auto-speak cuando TTS global está activo**

En `sendMessage()`, dentro del bloque `if (event.type === 'done')`:

```js
        } else if (event.type === 'done') {
          if (streamCardId) removeEl(streamCardId);
          else removeEl(typId);
          addAICard({ ...event, query: msg });
          if (event.gravedad === 'emergencia') emergencyBar.classList.add('show');
```

Reemplaza por:

```js
        } else if (event.type === 'done') {
          if (streamCardId) removeEl(streamCardId);
          else removeEl(typId);
          const cardData = { ...event, query: msg };
          addAICard(cardData);
          if (event.gravedad === 'emergencia') emergencyBar.classList.add('show');
          if (_ttsEnabled) {
            // Dar 300ms para que lucide renderice los botones
            setTimeout(() => {
              const lastTtsBtn = [...document.querySelectorAll('.tts-card-btn')].at(-1);
              speakResponse(cardData, lastTtsBtn?.id || null);
            }, 300);
          }
```

- [ ] **Step 8: Detener TTS al enviar nueva consulta**

En `sendMessage()`, después de `setLoading(true);`, agrega:

```js
  stopSpeaking();
```

- [ ] **Step 9: Inicializar TTS al final del script**

Busca al final del script la línea `initVoice();` y agrega `initTTS();` justo después:

```js
lucide.createIcons();
_syncThemeIcon(localStorage.getItem('medi-theme') || 'dark');
initVoice();
initTTS();
renderHistory();
loadHealthStatus();
```

- [ ] **Step 10: Verificar visualmente**

```bash
venv/Scripts/python.exe app.py
```

Abrir `http://localhost:5000` en Chrome. Verificar:
- Botón `volume-2` aparece en topbar junto al toggle de tema
- Al hacer clic activa el modo manos libres (ícono pulsa en verde)
- Cada card de respuesta tiene botón "Escuchar" en el footer
- Al hacer clic en "Escuchar" la respuesta se lee en español
- Hacer clic de nuevo detiene la lectura
- Activar modo manos libres → hacer consulta → respuesta se lee automáticamente

- [ ] **Step 11: Commit**

```bash
git add templates/index.html
git commit -m "feat: TTS respuesta por voz — toggle global hands-free + boton por card"
```

---

## Task 2: Perfil Clínico Modal

**Files:**
- Modify: `templates/index.html`

### CSS

- [ ] **Step 1: Agregar CSS del modal y chips**

Después del bloque `/* ===== TTS ===== */` del Task 1, agrega:

```css
  /* ===== PERFIL CLÍNICO ===== */
  .profile-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.65);
    backdrop-filter: blur(6px);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s;
  }
  .profile-overlay.show {
    opacity: 1;
    pointer-events: all;
  }
  .profile-modal {
    background: var(--surface);
    border: 1px solid var(--border-em);
    border-radius: 16px;
    padding: 28px 28px 24px;
    width: 100%;
    max-width: 480px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.04);
    transform: translateY(8px);
    transition: transform 0.2s;
  }
  .profile-overlay.show .profile-modal {
    transform: translateY(0);
  }
  .profile-modal h3 {
    font-size: 16px;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 4px;
  }
  .profile-modal .profile-subtitle {
    font-size: 12px;
    color: var(--text-3);
    margin-bottom: 20px;
  }
  .profile-field {
    margin-bottom: 16px;
  }
  .profile-label {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-3);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
  }
  .profile-input {
    width: 100%;
    padding: 8px 12px;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border-md);
    border-radius: 8px;
    color: var(--text);
    font-size: 13px;
    font-family: 'Inter', sans-serif;
    outline: none;
    transition: border-color 0.15s;
  }
  .profile-input:focus { border-color: var(--border-em); }
  .profile-chip-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 6px 8px;
    background: rgba(255,255,255,0.04);
    border: 1px solid var(--border-md);
    border-radius: 8px;
    min-height: 38px;
    cursor: text;
    transition: border-color 0.15s;
  }
  .profile-chip-wrap:focus-within { border-color: var(--border-em); }
  .profile-chip {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px 2px 10px;
    background: var(--em-dim);
    border: 1px solid var(--border-em);
    border-radius: 12px;
    font-size: 12px;
    color: var(--em);
    white-space: nowrap;
  }
  .profile-chip button {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--em);
    font-size: 13px;
    line-height: 1;
    padding: 0;
    opacity: 0.7;
  }
  .profile-chip button:hover { opacity: 1; }
  .profile-chip-input {
    flex: 1;
    min-width: 80px;
    background: none;
    border: none;
    color: var(--text);
    font-size: 13px;
    font-family: 'Inter', sans-serif;
    outline: none;
  }
  .profile-chip-hint {
    font-size: 10.5px;
    color: var(--text-4);
    margin-top: 4px;
  }
  .profile-toggle-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--border);
    border-radius: 8px;
  }
  .profile-toggle-label {
    font-size: 13px;
    color: var(--text-2);
  }
  .profile-toggle {
    position: relative;
    width: 36px;
    height: 20px;
    background: var(--border-strong);
    border-radius: 10px;
    cursor: pointer;
    transition: background 0.2s;
    border: none;
    flex-shrink: 0;
  }
  .profile-toggle.on { background: var(--em); }
  .profile-toggle::after {
    content: '';
    position: absolute;
    top: 2px;
    left: 2px;
    width: 16px;
    height: 16px;
    background: white;
    border-radius: 50%;
    transition: left 0.2s;
  }
  .profile-toggle.on::after { left: 18px; }
  .profile-actions {
    display: flex;
    gap: 8px;
    margin-top: 20px;
    justify-content: flex-end;
  }
  .profile-btn-skip {
    padding: 8px 16px;
    background: transparent;
    border: 1px solid var(--border-md);
    border-radius: 8px;
    color: var(--text-3);
    font-size: 13px;
    cursor: pointer;
    transition: all 0.15s;
  }
  .profile-btn-skip:hover { border-color: var(--border-strong); color: var(--text-2); }
  .profile-btn-save {
    padding: 8px 20px;
    background: var(--em);
    border: none;
    border-radius: 8px;
    color: white;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s;
  }
  .profile-btn-save:hover { opacity: 0.88; }

  /* Chip zonas en input bar */
  .zone-chips-bar {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    padding: 0 16px 8px;
    display: none;
  }
  .zone-chips-bar.visible { display: flex; }
  .zone-chip-tag {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 3px 8px 3px 10px;
    background: rgba(6,182,212,0.10);
    border: 1px solid rgba(6,182,212,0.25);
    border-radius: 12px;
    font-size: 11.5px;
    color: #22d3ee;
  }
  .zone-chip-tag button {
    background: none; border: none; cursor: pointer;
    color: #22d3ee; font-size: 13px; line-height: 1; padding: 0; opacity: 0.7;
  }
  .zone-chip-tag button:hover { opacity: 1; }
```

### HTML — Modal y botón sidebar

- [ ] **Step 2: Agregar modal HTML**

Antes de `<div class="sidebar-backdrop"` (busca esa cadena), agrega el HTML del modal:

```html
<!-- ===== MODAL PERFIL CLÍNICO ===== -->
<div class="profile-overlay" id="profileOverlay">
  <div class="profile-modal">
    <h3><i data-lucide="user-circle" style="width:16px;height:16px;display:inline;vertical-align:-2px;margin-right:6px;color:var(--em)"></i>Perfil clínico</h3>
    <p class="profile-subtitle">Información opcional que mejora la precisión del diagnóstico diferencial.</p>

    <div style="display:flex;gap:12px;margin-bottom:16px;">
      <div class="profile-field" style="flex:1">
        <div class="profile-label">Nombre</div>
        <input type="text" id="profileNombre" class="profile-input" placeholder="Tu nombre (opcional)">
      </div>
      <div class="profile-field" style="width:90px">
        <div class="profile-label">Edad</div>
        <input type="number" id="profileEdad" class="profile-input" placeholder="años" min="0" max="120">
      </div>
    </div>

    <div class="profile-field">
      <div class="profile-label">Alergias conocidas</div>
      <div class="profile-chip-wrap" id="profileAlergiaWrap" onclick="document.getElementById('profileAlergiaInput').focus()">
        <div id="profileAlergiaChips"></div>
        <input type="text" id="profileAlergiaInput" class="profile-chip-input" placeholder="Ej: penicilina">
      </div>
      <div class="profile-chip-hint">Escribe y presiona Enter para agregar</div>
    </div>

    <div class="profile-field">
      <div class="profile-label">Medicamentos actuales</div>
      <div class="profile-chip-wrap" id="profileMedWrap" onclick="document.getElementById('profileMedInput').focus()">
        <div id="profileMedChips"></div>
        <input type="text" id="profileMedInput" class="profile-chip-input" placeholder="Ej: atenolol 50mg">
      </div>
      <div class="profile-chip-hint">Escribe y presiona Enter para agregar</div>
    </div>

    <div class="profile-field">
      <div class="profile-label">Condiciones previas</div>
      <div class="profile-chip-wrap" id="profileCondWrap" onclick="document.getElementById('profileCondInput').focus()">
        <div id="profileCondChips"></div>
        <input type="text" id="profileCondInput" class="profile-chip-input" placeholder="Ej: hipertensión, diabetes">
      </div>
      <div class="profile-chip-hint">Escribe y presiona Enter para agregar</div>
    </div>

    <div class="profile-field">
      <div class="profile-toggle-row">
        <span class="profile-toggle-label">Embarazo actual o posible</span>
        <button class="profile-toggle" id="profileEmbarazadaToggle" onclick="this.classList.toggle('on')"></button>
      </div>
    </div>

    <div class="profile-actions">
      <button class="profile-btn-skip" onclick="closeProfileModal()">Saltar por ahora</button>
      <button class="profile-btn-save" onclick="saveProfile()">Guardar perfil</button>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Agregar botón "Mi perfil" en el sidebar footer**

Localiza el sidebar footer (busca `id="exportConvBtn"`). Reemplaza:

```html
  <div class="sidebar-footer">
    <button class="export-conv-btn" id="exportConvBtn" onclick="exportConversation(this)">
      <i data-lucide="file-text" style="width:13px;height:13px"></i> Exportar sesión
    </button>
    <button class="reset-btn" onclick="resetSession()">
      <i data-lucide="rotate-ccw" style="width:13px;height:13px"></i> Nueva consulta
    </button>
  </div>
```

Por:

```html
  <div class="sidebar-footer">
    <button class="export-conv-btn" id="exportConvBtn" onclick="exportConversation(this)">
      <i data-lucide="file-text" style="width:13px;height:13px"></i> Exportar sesión
    </button>
    <button class="sidebar-btn" onclick="openProfileModal()" style="justify-content:flex-start;gap:8px;">
      <i data-lucide="user-circle" style="width:14px;height:14px;stroke-width:2"></i> Mi perfil clínico
    </button>
    <button class="reset-btn" onclick="resetSession()">
      <i data-lucide="rotate-ccw" style="width:13px;height:13px"></i> Nueva consulta
    </button>
  </div>
```

### JS — Funciones del perfil

- [ ] **Step 4: Agregar bloque JS del perfil clínico**

Después del bloque `// ===== TTS =====`, agrega:

```js
// ===== PERFIL CLÍNICO =====
const _profileChips = { alergias: [], medicamentos: [], condiciones: [] };

function openProfileModal() {
  _loadProfileIntoModal();
  document.getElementById('profileOverlay').classList.add('show');
}

function closeProfileModal() {
  document.getElementById('profileOverlay').classList.remove('show');
}

function _loadProfileIntoModal() {
  const raw = sessionStorage.getItem('medi-ia-profile');
  const p = raw ? JSON.parse(raw) : {};
  document.getElementById('profileNombre').value = p.nombre || '';
  document.getElementById('profileEdad').value = p.edad || '';
  _profileChips.alergias = p.alergias || [];
  _profileChips.medicamentos = p.medicamentos || [];
  _profileChips.condiciones = p.condiciones || [];
  if (p.embarazada) document.getElementById('profileEmbarazadaToggle').classList.add('on');
  _renderChips('profileAlergiaChips', 'alergias');
  _renderChips('profileMedChips', 'medicamentos');
  _renderChips('profileCondChips', 'condiciones');
}

function _renderChips(containerId, key) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = _profileChips[key].map((v, i) =>
    `<span class="profile-chip">${esc(v)}<button onclick="_removeChip('${key}',${i},'${containerId}')" title="Quitar">×</button></span>`
  ).join('');
}

function _removeChip(key, idx, containerId) {
  _profileChips[key].splice(idx, 1);
  _renderChips(containerId, key);
}

function _setupChipInput(inputId, key, containerId) {
  const input = document.getElementById(inputId);
  if (!input) return;
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const val = input.value.trim().replace(/,$/, '');
      if (val && !_profileChips[key].includes(val)) {
        _profileChips[key].push(val);
        _renderChips(containerId, key);
      }
      input.value = '';
    }
  });
}

function saveProfile() {
  const profile = {
    nombre: document.getElementById('profileNombre').value.trim(),
    edad: parseInt(document.getElementById('profileEdad').value) || null,
    alergias: [..._profileChips.alergias],
    medicamentos: [..._profileChips.medicamentos],
    condiciones: [..._profileChips.condiciones],
    embarazada: document.getElementById('profileEmbarazadaToggle').classList.contains('on')
  };
  sessionStorage.setItem('medi-ia-profile', JSON.stringify(profile));
  closeProfileModal();
  showToast('Perfil guardado correctamente');
}

function buildProfilePrefix() {
  const raw = sessionStorage.getItem('medi-ia-profile');
  if (!raw) return '';
  const p = JSON.parse(raw);
  const parts = [];
  if (p.nombre && p.edad) parts.push(`${p.nombre}, ${p.edad} años`);
  else if (p.nombre) parts.push(p.nombre);
  else if (p.edad) parts.push(`${p.edad} años`);
  if (p.alergias?.length) parts.push(`Alergias: ${p.alergias.join(', ')}`);
  if (p.medicamentos?.length) parts.push(`Medicamentos: ${p.medicamentos.join(', ')}`);
  if (p.condiciones?.length) parts.push(`Condiciones: ${p.condiciones.join(', ')}`);
  if (p.embarazada) parts.push('Embarazada: sí');
  return parts.length ? `[Paciente: ${parts.join('. ')}]` : '';
}

function checkProfileOnLoad() {
  if (!sessionStorage.getItem('medi-ia-profile')) {
    // Mostrar modal tras 800ms para que la página cargue primero
    setTimeout(openProfileModal, 800);
  }
}
```

- [ ] **Step 5: Inicializar chip inputs y evento overlay**

Después de `checkProfileOnLoad`, agrega:

```js
function initProfileModal() {
  _setupChipInput('profileAlergiaInput', 'alergias', 'profileAlergiaChips');
  _setupChipInput('profileMedInput', 'medicamentos', 'profileMedChips');
  _setupChipInput('profileCondInput', 'condiciones', 'profileCondChips');
  // Cerrar al hacer clic en el overlay (fuera del modal)
  document.getElementById('profileOverlay')?.addEventListener('click', e => {
    if (e.target.id === 'profileOverlay') closeProfileModal();
  });
}
```

- [ ] **Step 6: Modificar sendMessage para inyectar perfil**

En `sendMessage()`, localiza:

```js
  const resp = await fetch('/api/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: msg })
  });
```

Reemplaza por:

```js
  const profilePrefix = buildProfilePrefix();
  const zonePrefix = buildZonePrefix(); // se define en Task 4; retorna '' hasta entonces
  const contextPrefix = [profilePrefix, zonePrefix].filter(Boolean).join(' ');
  const fullMsg = contextPrefix ? `${contextPrefix} ${msg}` : msg;
  const resp = await fetch('/api/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message: fullMsg })
  });
```

> Nota: `buildZonePrefix()` se define en Task 4. Para que no falle ahora, agrega un stub temporal después del bloque de perfil:
> ```js
> function buildZonePrefix() { return ''; } // stub — se reemplaza en Task 4
> ```

- [ ] **Step 7: Llamar initProfileModal y checkProfileOnLoad al final del script**

En el bloque de inicialización al final del script, agrega las dos llamadas:

```js
lucide.createIcons();
_syncThemeIcon(localStorage.getItem('medi-theme') || 'dark');
initVoice();
initTTS();
initProfileModal();
renderHistory();
loadHealthStatus();
checkProfileOnLoad();
```

- [ ] **Step 8: Verificar visualmente**

```bash
venv/Scripts/python.exe app.py
```

Abrir `http://localhost:5000` en modo incógnito (para limpiar sessionStorage). Verificar:
- Modal aparece automáticamente ~800ms después de cargar
- Campos de texto y chips funcionan (Enter agrega chip, × lo quita)
- Toggle embarazada funciona visualmente
- "Guardar perfil" muestra toast y cierra
- "Saltar por ahora" cierra sin guardar
- Botón "Mi perfil clínico" en sidebar reabre el modal
- Si el perfil tiene datos, al hacer una consulta el prefijo se incluye (verificar en Network tab → request payload)

- [ ] **Step 9: Commit**

```bash
git add templates/index.html
git commit -m "feat: perfil clinico modal — chips sessionStorage, inyeccion en query"
```

---

## Task 3: Visualización Pipeline RAG Animada

**Files:**
- Modify: `templates/index.html`

### CSS

- [ ] **Step 1: Agregar CSS del pipeline panel**

Después del bloque `/* ===== PERFIL CLÍNICO ===== */`, agrega:

```css
  /* ===== PIPELINE RAG VIZ ===== */
  .pipeline-btn {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 10.5px;
    padding: 4px 8px;
    background: var(--surface-2);
    border: 1px solid var(--border-md);
    border-radius: 6px;
    color: var(--text-2);
    cursor: pointer;
    font-family: 'Inter', sans-serif;
    transition: all 0.15s;
    white-space: nowrap;
    flex-shrink: 0;
  }
  .pipeline-btn:hover { background: rgba(59,130,246,0.08); border-color: rgba(59,130,246,0.2); color: var(--blue); }
  .pipeline-btn.open { color: var(--blue); border-color: rgba(59,130,246,0.2); background: rgba(59,130,246,0.08); }

  .pipeline-panel {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.4s ease;
    border-top: 0px solid var(--border);
  }
  .pipeline-panel.open {
    max-height: 1200px;
    border-top: 1px solid var(--border);
  }
  .pipeline-inner {
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .pipeline-step {
    opacity: 0;
    transform: translateY(6px);
    transition: opacity 0.3s ease, transform 0.3s ease;
  }
  .pipeline-step.visible {
    opacity: 1;
    transform: translateY(0);
  }
  .pipeline-step-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-3);
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .pipeline-step-badge {
    display: inline-flex;
    align-items: center;
    padding: 1px 7px;
    background: rgba(59,130,246,0.10);
    color: var(--blue);
    border-radius: 8px;
    font-size: 9.5px;
    font-family: 'JetBrains Mono', monospace;
    text-transform: none;
    letter-spacing: 0;
  }
  .pipeline-chunks-grid {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .pipeline-chunk-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 12px;
    transition: border-color 0.3s, opacity 0.4s;
  }
  .pipeline-chunk-card.discarded {
    opacity: 0.35;
  }
  .pipeline-chunk-card.kept {
    border-color: var(--border-em);
  }
  .pipeline-chunk-hdr {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 5px;
    flex-wrap: wrap;
  }
  .pipeline-rank {
    font-size: 9.5px;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-4);
    min-width: 20px;
  }
  .pipeline-book {
    font-size: 11px;
    font-weight: 500;
    color: var(--text-2);
    flex: 1;
  }
  .pipeline-page {
    font-size: 10px;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-3);
  }
  .pipeline-score-row {
    display: flex;
    align-items: center;
    gap: 6px;
    margin-bottom: 3px;
  }
  .pipeline-score-label {
    font-size: 9.5px;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-4);
    min-width: 36px;
  }
  .pipeline-bar {
    flex: 1;
    height: 4px;
    background: rgba(255,255,255,0.06);
    border-radius: 2px;
    overflow: hidden;
  }
  .pipeline-bar-fill {
    height: 100%;
    border-radius: 2px;
    width: 0%;
    transition: width 0.7s ease;
  }
  .pipeline-bar-fill.faiss { background: var(--blue); }
  .pipeline-bar-fill.rerank-pos { background: var(--em); }
  .pipeline-bar-fill.rerank-neg { background: var(--red); }
  .pipeline-score-num {
    font-size: 9.5px;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-3);
    min-width: 40px;
    text-align: right;
  }
  .pipeline-preview {
    font-size: 11.5px;
    color: var(--text-3);
    line-height: 1.5;
    margin-top: 4px;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .pipeline-preview.discarded-text { text-decoration: line-through; color: var(--text-4); }
  .pipeline-kept-badge {
    font-size: 9px;
    padding: 1px 6px;
    background: var(--em-dim);
    color: var(--em);
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
  }
  .pipeline-discarded-badge {
    font-size: 9px;
    padding: 1px 6px;
    background: rgba(239,68,68,0.08);
    color: var(--red);
    border-radius: 8px;
    font-family: 'JetBrains Mono', monospace;
  }
```

### JS — buildRagPipelineHtml y toggleRagPipeline

- [ ] **Step 2: Agregar función buildRagPipelineHtml**

Después del bloque `// ===== PERFIL CLÍNICO =====`, agrega:

```js
// ===== PIPELINE RAG VIZ =====
function buildRagPipelineHtml(chunks, panelId) {
  if (!chunks || !chunks.length) return '';

  const RERANK_THRESHOLD = -3.0;
  // Ordenar por rerank_score descendente para paso 2
  const reranked = [...chunks].sort((a, b) => (b.rerank_score || 0) - (a.rerank_score || 0));

  const renderChunkCard = (c, phase) => {
    const faissW = Math.round(Math.min(100, (c.faiss_score || 0) * 100));
    const rrScore = c.rerank_score || 0;
    // Para la barra de rerank: normalizar entre -10 y 10 → 0-100%
    const rrNorm = Math.round(Math.min(100, Math.max(0, ((rrScore + 10) / 20) * 100)));
    const rrClass = rrScore >= 0 ? 'rerank-pos' : 'rerank-neg';
    const bookShort = (c.book || '').split(' ').slice(0, 3).join(' ');
    const isKept = rrScore > RERANK_THRESHOLD;

    if (phase === 'retrieval') {
      return `<div class="pipeline-chunk-card" data-pipeline-card="${c.rank}">
        <div class="pipeline-chunk-hdr">
          <span class="pipeline-rank">#${c.rank}</span>
          <span class="pipeline-book"><i data-lucide="book-open" style="width:11px;height:11px;display:inline;margin-right:3px;vertical-align:-1px"></i>${esc(bookShort)}</span>
          <span class="pipeline-page">p.${c.page}</span>
        </div>
        <div class="pipeline-score-row">
          <span class="pipeline-score-label">FAISS</span>
          <div class="pipeline-bar"><div class="pipeline-bar-fill faiss" data-target="${faissW}"></div></div>
          <span class="pipeline-score-num">${(c.faiss_score||0).toFixed(3)}</span>
        </div>
        <div class="pipeline-preview">${esc(c.text_preview || '')}…</div>
      </div>`;
    }

    if (phase === 'rerank') {
      return `<div class="pipeline-chunk-card ${isKept ? '' : 'discarded'}" data-pipeline-card="${c.rank}">
        <div class="pipeline-chunk-hdr">
          <span class="pipeline-rank">#${c.rank}</span>
          <span class="pipeline-book"><i data-lucide="book-open" style="width:11px;height:11px;display:inline;margin-right:3px;vertical-align:-1px"></i>${esc(bookShort)}</span>
          <span class="pipeline-page">p.${c.page}</span>
          ${isKept ? '<span class="pipeline-kept-badge">✓ relevante</span>' : '<span class="pipeline-discarded-badge">descartado</span>'}
        </div>
        <div class="pipeline-score-row">
          <span class="pipeline-score-label">Rerank</span>
          <div class="pipeline-bar"><div class="pipeline-bar-fill ${rrClass}" data-target="${rrNorm}"></div></div>
          <span class="pipeline-score-num">${rrScore.toFixed(2)}</span>
        </div>
        <div class="pipeline-preview ${isKept ? '' : 'discarded-text'}">${esc(c.text_preview || '')}…</div>
      </div>`;
    }

    if (phase === 'final') {
      return `<div class="pipeline-chunk-card ${isKept ? 'kept' : 'discarded'}">
        <div class="pipeline-chunk-hdr">
          <span class="pipeline-rank">#${c.rank}</span>
          <span class="pipeline-book"><i data-lucide="book-open" style="width:11px;height:11px;display:inline;margin-right:3px;vertical-align:-1px"></i>${esc(bookShort)}</span>
          <span class="pipeline-page">p.${c.page}</span>
          ${isKept ? '<span class="pipeline-kept-badge">→ enviado al LLM</span>' : '<span class="pipeline-discarded-badge">no incluido</span>'}
        </div>
        <div class="pipeline-preview ${isKept ? '' : 'discarded-text'}">${esc(c.text_preview || '')}…</div>
      </div>`;
    }
    return '';
  };

  return `<div class="pipeline-inner" id="${panelId}_inner">
    <div class="pipeline-step" id="${panelId}_s1">
      <div class="pipeline-step-title">
        <span>1. Recuperación</span>
        <span class="pipeline-step-badge">BM25 + FAISS · ${chunks.length} chunks</span>
      </div>
      <div class="pipeline-chunks-grid">
        ${chunks.map(c => renderChunkCard(c, 'retrieval')).join('')}
      </div>
    </div>
    <div class="pipeline-step" id="${panelId}_s2">
      <div class="pipeline-step-title">
        <span>2. Reranker</span>
        <span class="pipeline-step-badge">Cross-Encoder mMARCO</span>
      </div>
      <div class="pipeline-chunks-grid">
        ${reranked.map(c => renderChunkCard(c, 'rerank')).join('')}
      </div>
    </div>
    <div class="pipeline-step" id="${panelId}_s3">
      <div class="pipeline-step-title">
        <span>3. Contexto enviado al LLM</span>
        <span class="pipeline-step-badge">${reranked.filter(c => (c.rerank_score||0) > RERANK_THRESHOLD).length} fragmentos</span>
      </div>
      <div class="pipeline-chunks-grid">
        ${reranked.map(c => renderChunkCard(c, 'final')).join('')}
      </div>
    </div>
  </div>`;
}

function toggleRagPipeline(panelId, btnEl) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const isOpen = panel.classList.toggle('open');
  btnEl.classList.toggle('open', isOpen);
  btnEl.querySelector('span.arrow').textContent = isOpen ? '▲' : '▼';

  if (isOpen) {
    lucide.createIcons({ nodes: [panel] });
    // Animar los 3 pasos con delay escalonado
    const steps = ['_s1', '_s2', '_s3'];
    steps.forEach((suffix, i) => {
      setTimeout(() => {
        const step = document.getElementById(panelId + suffix);
        if (step) step.classList.add('visible');
        // Animar barras dentro del paso
        step?.querySelectorAll('.pipeline-bar-fill[data-target]').forEach(bar => {
          setTimeout(() => { bar.style.width = bar.dataset.target + '%'; }, 50);
        });
      }, i * 220);
    });
  } else {
    // Resetear al colapsar
    ['_s1','_s2','_s3'].forEach(s => {
      const step = document.getElementById(panelId + s);
      if (step) {
        step.classList.remove('visible');
        step.querySelectorAll('.pipeline-bar-fill').forEach(b => { b.style.width = '0%'; });
      }
    });
  }
}
```

### HTML — Botón y panel en addAICard

- [ ] **Step 3: Agregar variables de ID para pipeline en addAICard**

En `addAICard`, donde se declaran los IDs, reemplaza:

```js
  const exportBtnId  = 'expbtn_'   + Date.now();
  const copyBtnId    = 'copybtn_'  + Date.now();
  const ttsBtnId     = 'ttsbtn_'   + Date.now();
  const detailsBtnId = 'detbtn_'   + Date.now();
  const panelId      = 'detpanel_' + Date.now();
  const feedbackId   = 'fb_'       + Date.now();
```

Por:

```js
  const ts           = Date.now();
  const exportBtnId  = 'expbtn_'      + ts;
  const copyBtnId    = 'copybtn_'     + ts;
  const ttsBtnId     = 'ttsbtn_'      + ts;
  const detailsBtnId = 'detbtn_'      + ts;
  const panelId      = 'detpanel_'    + ts;
  const pipelineBtnId = 'pipebtn_'   + ts;
  const pipelinePanelId = 'pipepanel_' + ts;
  const feedbackId   = 'fb_'          + ts;
```

- [ ] **Step 4: Agregar botón pipeline en el card footer**

En el template string del card footer, después del botón TTS:

```js
        <button class="tts-card-btn" id="${ttsBtnId}" title="Escuchar respuesta"><i data-lucide="volume-2" style="width:12px;height:12px"></i> Escuchar</button>
```

Agrega:

```js
        <button class="tts-card-btn" id="${ttsBtnId}" title="Escuchar respuesta"><i data-lucide="volume-2" style="width:12px;height:12px"></i> Escuchar</button>
        ${chunks.length ? `<button class="pipeline-btn" id="${pipelineBtnId}"><i data-lucide="git-branch" style="width:12px;height:12px"></i> Ver pipeline <span class="arrow">▼</span></button>` : ''}
```

- [ ] **Step 5: Agregar panel pipeline en el HTML de la card**

En el template string, después de:

```js
      ${hasDetails
        ? `<div class="details-panel" id="${panelId}">
            ${chunksSec}${toolsSec}${srcsSec}${modeSec}${trajSec}
           </div>`
        : ''}
```

Agrega:

```js
      ${chunks.length
        ? `<div class="pipeline-panel" id="${pipelinePanelId}">
            ${buildRagPipelineHtml(chunks, pipelinePanelId)}
           </div>`
        : ''}
```

- [ ] **Step 6: Agregar event listener del botón pipeline en addAICard**

Después de la línea del event listener de detalles:

```js
  document.getElementById(detailsBtnId)?.addEventListener('click', function() { toggleDetails(panelId, this); });
```

Agrega:

```js
  document.getElementById(pipelineBtnId)?.addEventListener('click', function() { toggleRagPipeline(pipelinePanelId, this); });
```

- [ ] **Step 7: Verificar visualmente**

```bash
venv/Scripts/python.exe app.py
```

Hacer una consulta médica. Verificar:
- Botón "Ver pipeline ▼" aparece en el footer de la card
- Al hacer clic, el panel se expande con animación
- Los 3 pasos aparecen en secuencia con delay
- Las barras de score se animan de 0 a su valor
- Chunks con rerank score < -3.0 se atenúan/tachan
- Chunks relevantes tienen badge verde "→ enviado al LLM"
- Hacer clic de nuevo colapsa el panel

- [ ] **Step 8: Commit**

```bash
git add templates/index.html
git commit -m "feat: visualizacion pipeline RAG animada — 3 pasos con scores y barras"
```

---

## Task 4: Cuerpo Humano SVG Interactivo

**Files:**
- Modify: `templates/index.html`

### CSS

- [ ] **Step 1: Agregar CSS del drawer y SVG**

Después del bloque `/* ===== PIPELINE RAG VIZ ===== */`, agrega:

```css
  /* ===== BODY MAP DRAWER ===== */
  .body-drawer-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.5);
    z-index: 900;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.25s;
  }
  .body-drawer-overlay.show { opacity: 1; pointer-events: all; }

  .body-drawer {
    position: fixed;
    top: 0;
    right: 0;
    width: 320px;
    height: 100%;
    background: var(--surface);
    border-left: 1px solid var(--border-md);
    z-index: 901;
    display: flex;
    flex-direction: column;
    transform: translateX(100%);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: -8px 0 32px rgba(0,0,0,0.4);
  }
  .body-drawer.open { transform: translateX(0); }

  .body-drawer-header {
    padding: 16px 16px 12px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }
  .body-drawer-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text);
  }
  .body-drawer-close {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-3);
    padding: 4px;
    border-radius: 6px;
    transition: all 0.15s;
  }
  .body-drawer-close:hover { background: var(--surface-2); color: var(--text-2); }

  .body-view-toggle {
    display: flex;
    gap: 6px;
    padding: 10px 16px;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }
  .body-view-btn {
    flex: 1;
    padding: 5px 10px;
    background: transparent;
    border: 1px solid var(--border-md);
    border-radius: 7px;
    color: var(--text-3);
    font-size: 11.5px;
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    transition: all 0.15s;
  }
  .body-view-btn.active {
    background: var(--em-dim);
    border-color: var(--border-em);
    color: var(--em);
    font-weight: 500;
  }

  .body-svg-wrap {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 12px;
    overflow: hidden;
  }
  .body-svg-container {
    position: relative;
    width: 100%;
    max-width: 180px;
  }
  .body-svg-container svg {
    width: 100%;
    height: auto;
    display: block;
  }
  .body-zone {
    fill: rgba(255,255,255,0.06);
    stroke: rgba(255,255,255,0.18);
    stroke-width: 1;
    cursor: pointer;
    transition: fill 0.18s, stroke 0.18s, filter 0.18s;
  }
  .body-zone:hover {
    fill: rgba(16,185,129,0.18);
    stroke: rgba(16,185,129,0.5);
  }
  .body-zone.selected {
    fill: rgba(16,185,129,0.35);
    stroke: var(--em);
    stroke-width: 1.5;
    filter: drop-shadow(0 0 5px rgba(16,185,129,0.55));
  }

  .body-marked-section {
    padding: 10px 16px;
    border-top: 1px solid var(--border);
    flex-shrink: 0;
    min-height: 60px;
  }
  .body-marked-label {
    font-size: 10.5px;
    font-weight: 600;
    color: var(--text-3);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
  }
  .body-marked-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
    min-height: 24px;
  }
  .body-zone-chip {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px 2px 10px;
    background: rgba(6,182,212,0.10);
    border: 1px solid rgba(6,182,212,0.25);
    border-radius: 12px;
    font-size: 11px;
    color: #22d3ee;
  }
  .body-zone-chip button {
    background: none; border: none; cursor: pointer;
    color: #22d3ee; font-size: 13px; line-height: 1; padding: 0; opacity: 0.7;
  }
  .body-zone-chip button:hover { opacity: 1; }
  .body-no-zones {
    font-size: 11.5px;
    color: var(--text-4);
    font-style: italic;
  }

  /* Botón "Marcar zona" en input bar */
  .zone-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    cursor: pointer;
    color: var(--text-3);
    flex-shrink: 0;
    transition: all 0.15s;
  }
  .zone-btn:hover { background: var(--surface-2); color: var(--text-2); border-color: var(--border); }
  .zone-btn.has-zones {
    color: #22d3ee;
    border-color: rgba(6,182,212,0.3);
    background: rgba(6,182,212,0.08);
  }

  /* Chips de zonas debajo del textarea */
  .zone-chips-bar {
    display: none;
    gap: 6px;
    flex-wrap: wrap;
    padding: 0 14px 8px;
  }
  .zone-chips-bar.visible { display: flex; }

  @media (max-width: 600px) {
    .body-drawer { width: 100%; }
  }
```

### HTML — Drawer y botón en input bar

- [ ] **Step 2: Agregar HTML del drawer**

Después del modal de perfil (busca `</div><!-- fin modal perfil -->`; si no existe, busca el bloque del modal y agrega después de su `</div>` final), agrega:

```html
<!-- ===== BODY MAP DRAWER ===== -->
<div class="body-drawer-overlay" id="bodyDrawerOverlay" onclick="closeBodyDrawer()"></div>
<div class="body-drawer" id="bodyDrawer">
  <div class="body-drawer-header">
    <span class="body-drawer-title"><i data-lucide="map-pin" style="width:14px;height:14px;display:inline;margin-right:5px;vertical-align:-2px;color:var(--em)"></i>Marcar zona de dolor</span>
    <button class="body-drawer-close" onclick="closeBodyDrawer()">
      <i data-lucide="x" style="width:16px;height:16px;stroke-width:2"></i>
    </button>
  </div>
  <div class="body-view-toggle">
    <button class="body-view-btn active" id="btnViewFront" onclick="setBodyView('front')">Frontal</button>
    <button class="body-view-btn" id="btnViewBack" onclick="setBodyView('back')">Dorsal</button>
  </div>
  <div class="body-svg-wrap">
    <div class="body-svg-container">
      <!-- Vista Frontal -->
      <svg id="bodySvgFront" viewBox="0 0 160 320" xmlns="http://www.w3.org/2000/svg">
        <ellipse data-zone="cabeza" data-label="Cabeza" cx="80" cy="28" rx="22" ry="24" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="cuello" data-label="Cuello" x="68" y="52" width="24" height="16" rx="4" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="pecho" data-label="Pecho" x="44" y="68" width="72" height="52" rx="8" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="abdomen" data-label="Abdomen" x="48" y="122" width="64" height="44" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="pelvis" data-label="Pelvis" x="48" y="168" width="64" height="32" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <ellipse data-zone="hombro-der" data-label="Hombro derecho" cx="36" cy="76" rx="13" ry="13" class="body-zone" onclick="toggleBodyZone(this)"/>
        <ellipse data-zone="hombro-izq" data-label="Hombro izquierdo" cx="124" cy="76" rx="13" ry="13" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="brazo-der" data-label="Brazo derecho" x="18" y="89" width="22" height="48" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="brazo-izq" data-label="Brazo izquierdo" x="120" y="89" width="22" height="48" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="antebrazo-der" data-label="Antebrazo derecho" x="16" y="140" width="20" height="44" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="antebrazo-izq" data-label="Antebrazo izquierdo" x="124" y="140" width="20" height="44" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="muslo-der" data-label="Muslo derecho" x="50" y="202" width="28" height="52" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="muslo-izq" data-label="Muslo izquierdo" x="82" y="202" width="28" height="52" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="pierna-der" data-label="Pierna derecha" x="50" y="258" width="26" height="50" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="pierna-izq" data-label="Pierna izquierda" x="84" y="258" width="26" height="50" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
      </svg>
      <!-- Vista Dorsal -->
      <svg id="bodySvgBack" viewBox="0 0 160 320" xmlns="http://www.w3.org/2000/svg" style="display:none">
        <ellipse data-zone="cabeza-post" data-label="Cabeza (posterior)" cx="80" cy="28" rx="22" ry="24" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="cuello-post" data-label="Cuello (posterior)" x="68" y="52" width="24" height="16" rx="4" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="espalda-alta" data-label="Espalda alta" x="44" y="68" width="72" height="44" rx="8" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="espalda-baja" data-label="Espalda baja" x="48" y="114" width="64" height="52" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="gluteos" data-label="Glúteos" x="48" y="168" width="64" height="32" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="muslo-post-der" data-label="Muslo post. derecho" x="50" y="202" width="28" height="52" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="muslo-post-izq" data-label="Muslo post. izquierdo" x="82" y="202" width="28" height="52" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="pierna-post-der" data-label="Pierna post. derecha" x="50" y="258" width="26" height="50" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
        <rect data-zone="pierna-post-izq" data-label="Pierna post. izquierda" x="84" y="258" width="26" height="50" rx="6" class="body-zone" onclick="toggleBodyZone(this)"/>
      </svg>
    </div>
  </div>
  <div class="body-marked-section">
    <div class="body-marked-label">Zonas marcadas</div>
    <div class="body-marked-chips" id="bodyMarkedChips">
      <span class="body-no-zones">Ninguna zona seleccionada</span>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Agregar botón "Marcar zona" en el input bar**

Localiza el input-wrap HTML (busca `id="micBtn"`). Reemplaza:

```html
      <button class="mic-btn" id="micBtn" onclick="toggleVoice()" title="Dictar síntomas por voz">
        <i data-lucide="mic" id="micIcon" style="width:17px;height:17px;stroke-width:2"></i>
      </button>
```

Por:

```html
      <button class="zone-btn" id="zoneBtn" onclick="openBodyDrawer()" title="Marcar zona de dolor en el cuerpo">
        <i data-lucide="map-pin" style="width:16px;height:16px;stroke-width:2"></i>
      </button>
      <button class="mic-btn" id="micBtn" onclick="toggleVoice()" title="Dictar síntomas por voz">
        <i data-lucide="mic" id="micIcon" style="width:17px;height:17px;stroke-width:2"></i>
      </button>
```

- [ ] **Step 4: Agregar barra de chips de zona debajo del input-wrap**

Localiza en el input-bar HTML (busca `class="input-hint"`). Reemplaza:

```html
    <div class="input-hint">
      <span>No reemplaza la consulta médica profesional</span>
      <span>Enter para enviar · Shift+Enter para nueva línea</span>
    </div>
```

Por:

```html
    <div class="zone-chips-bar" id="zoneChipsBar"></div>
    <div class="input-hint">
      <span>No reemplaza la consulta médica profesional</span>
      <span>Enter para enviar · Shift+Enter para nueva línea</span>
    </div>
```

### JS — Funciones del body map

- [ ] **Step 5: Reemplazar stub buildZonePrefix y agregar bloque JS del body map**

Localiza el stub `function buildZonePrefix() { return ''; }` del Task 2 y reemplázalo con el bloque completo:

```js
// ===== BODY MAP =====
const _selectedZones = new Map(); // zone-id → label

function openBodyDrawer() {
  document.getElementById('bodyDrawer').classList.add('open');
  document.getElementById('bodyDrawerOverlay').classList.add('show');
  lucide.createIcons({ nodes: [document.getElementById('bodyDrawer')] });
  // Restaurar estado visual de zonas ya marcadas
  _selectedZones.forEach((label, zone) => {
    document.querySelector(`[data-zone="${zone}"]`)?.classList.add('selected');
  });
}

function closeBodyDrawer() {
  document.getElementById('bodyDrawer').classList.remove('open');
  document.getElementById('bodyDrawerOverlay').classList.remove('show');
}

function setBodyView(view) {
  document.getElementById('bodySvgFront').style.display = view === 'front' ? 'block' : 'none';
  document.getElementById('bodySvgBack').style.display  = view === 'back'  ? 'block' : 'none';
  document.getElementById('btnViewFront').classList.toggle('active', view === 'front');
  document.getElementById('btnViewBack').classList.toggle('active', view === 'back');
}

function toggleBodyZone(el) {
  const zone  = el.dataset.zone;
  const label = el.dataset.label;
  if (_selectedZones.has(zone)) {
    _selectedZones.delete(zone);
    el.classList.remove('selected');
  } else {
    _selectedZones.set(zone, label);
    el.classList.add('selected');
  }
  _renderBodyChips();
  _renderZoneChipsBar();
}

function _removeZone(zone) {
  _selectedZones.delete(zone);
  document.querySelector(`[data-zone="${zone}"]`)?.classList.remove('selected');
  _renderBodyChips();
  _renderZoneChipsBar();
}

function _renderBodyChips() {
  const container = document.getElementById('bodyMarkedChips');
  if (!container) return;
  if (_selectedZones.size === 0) {
    container.innerHTML = '<span class="body-no-zones">Ninguna zona seleccionada</span>';
    return;
  }
  container.innerHTML = [..._selectedZones.entries()].map(([zone, label]) =>
    `<span class="body-zone-chip">${esc(label)}<button onclick="_removeZone('${zone}')" title="Quitar">×</button></span>`
  ).join('');
}

function _renderZoneChipsBar() {
  const bar = document.getElementById('zoneChipsBar');
  const zoneBtn = document.getElementById('zoneBtn');
  if (!bar) return;
  if (_selectedZones.size === 0) {
    bar.classList.remove('visible');
    bar.innerHTML = '';
    zoneBtn?.classList.remove('has-zones');
    return;
  }
  bar.classList.add('visible');
  zoneBtn?.classList.add('has-zones');
  bar.innerHTML = [..._selectedZones.entries()].map(([zone, label]) =>
    `<span class="zone-chip-tag">${esc(label)}<button onclick="_removeZone('${zone}')" title="Quitar">×</button></span>`
  ).join('');
}

function buildZonePrefix() {
  if (_selectedZones.size === 0) return '';
  const labels = [..._selectedZones.values()].join(', ');
  return `[Zonas afectadas: ${labels}.]`;
}
```

- [ ] **Step 6: Verificar visualmente**

```bash
venv/Scripts/python.exe app.py
```

Abrir `http://localhost:5000`. Verificar:
- Botón `map-pin` aparece en el input bar junto al micrófono
- Hacer clic abre el drawer desde la derecha con animación
- Las zonas del SVG frontal se iluminan al hover (glow verde sutil)
- Hacer clic en "Pecho" → se ilumina en verde esmeralda, aparece chip en "Zonas marcadas"
- Cambiar a vista "Dorsal" → SVG cambia con transición
- Marcar "Espalda baja" en dorsal → chip aparece también
- Chips de zonas marcadas aparecen debajo del textarea en la pantalla principal
- Botón `map-pin` cambia a color cyan cuando hay zonas marcadas
- Hacer clic × en un chip lo desmarca (tanto en drawer como en bar)
- Hacer una consulta → en Network tab, el mensaje incluye `[Zonas afectadas: ...]`
- Cerrar drawer haciendo clic en el overlay oscuro

- [ ] **Step 7: Commit**

```bash
git add templates/index.html
git commit -m "feat: cuerpo humano SVG interactivo — drawer frontal+dorsal, zonas en contexto"
```

---

## Resumen de commits esperados

```
feat: TTS respuesta por voz — toggle global hands-free + boton por card
feat: perfil clinico modal — chips sessionStorage, inyeccion en query
feat: visualizacion pipeline RAG animada — 3 pasos con scores y barras
feat: cuerpo humano SVG interactivo — drawer frontal+dorsal, zonas en contexto
```
