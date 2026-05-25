# UI Redesign Dark Glassmorphism — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transformar la UI de MEDI-IA a dark glassmorphism sobrio con acento emerald, sidebar compacto y welcome screen rediseñada.

**Architecture:** Solo CSS + JS mínimo (cambio de default del tema). Cuatro templates se modifican; ningún archivo Python se toca. El sistema de variables CSS (`--var`) ya existente se aprovecha: basta con invertir cuál es el `:root` (dark) y cuál es el override (`[data-theme="light"]`).

**Tech Stack:** HTML/CSS inline en templates Jinja2, Lucide icons, Inter font. Sin dependencias nuevas.

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `templates/index.html` | Tareas 1-5: variables, componentes CSS, sidebar, topbar, welcome |
| `templates/login.html` | Tarea 6: tokens dark |
| `templates/metrics.html` | Tarea 6: tokens dark |
| `templates/evaluate.html` | Tarea 6: tokens dark |

---

## Task 1: CSS variables dark-first + JS theme default en index.html

**Files:**
- Modify: `templates/index.html` (bloque `:root` líneas 11-37, bloque `[data-theme="dark"]` líneas 929-993, `initTheme()` línea 2082, `_syncThemeIcon` llamada línea 2143)

- [ ] **Step 1: Reemplazar bloque `:root` con tokens dark**

En `templates/index.html`, reemplazar el bloque completo:

```css
  :root {
    --bg: #f0f4f8;
    --surface: #ffffff;
    --surface-2: #f8fafc;
    --border: #e2e8f0;
    --border-strong: #cbd5e1;
    --emerald: #10b981;
    --emerald-dark: #059669;
    --emerald-light: #d1fae5;
    --emerald-glow: rgba(16, 185, 129, 0.12);
    --blue: #3b82f6;
    --blue-light: #dbeafe;
    --amber: #f59e0b;
    --amber-light: #fef3c7;
    --red: #ef4444;
    --red-light: #fee2e2;
    --purple: #8b5cf6;
    --purple-light: #ede9fe;
    --text: #0f172a;
    --text-2: #475569;
    --text-3: #94a3b8;
    --text-4: #cbd5e1;
    --sidebar-w: 260px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.07), 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
    --shadow-lg: 0 10px 30px rgba(0,0,0,0.1), 0 4px 8px rgba(0,0,0,0.06);
  }
```

Por:

```css
  :root {
    --bg:        #090e1a;
    --surface:   #0f1629;
    --surface-2: #111d35;
    --surface-3: #162140;
    --border:    rgba(255,255,255,0.06);
    --border-md: rgba(255,255,255,0.09);
    --border-strong: rgba(255,255,255,0.12);
    --border-em: rgba(16,185,129,0.20);
    --emerald:   #10b981;
    --em:        #10b981;
    --emerald-dark: #059669;
    --em-dim:    rgba(16,185,129,0.12);
    --em-glow:   rgba(16,185,129,0.18);
    --emerald-light: rgba(16,185,129,0.12);
    --emerald-glow: rgba(16,185,129,0.18);
    --blue:      #3b82f6;
    --blue-light: rgba(59,130,246,0.12);
    --amber:     #f59e0b;
    --amber-light: rgba(245,158,11,0.12);
    --red:       #ef4444;
    --red-light: rgba(239,68,68,0.12);
    --purple:    #8b5cf6;
    --purple-light: rgba(139,92,246,0.12);
    --text:      #f1f5f9;
    --text-2:    #94a3b8;
    --text-3:    #475569;
    --text-4:    #2d4060;
    --sidebar-w: 200px;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.4);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.45);
    --shadow-lg: 0 10px 30px rgba(0,0,0,0.55);
  }
```

- [ ] **Step 2: Reemplazar bloque `[data-theme="dark"]` con `[data-theme="light"]`**

Reemplazar el bloque completo que empieza con `[data-theme="dark"] {` y termina con `[data-theme="dark"] .followup-chip:hover { background: rgba(16,185,129,0.12); }` por:

```css
  /* ========= LIGHT MODE OVERRIDE ========= */
  [data-theme="light"] {
    --bg:        #f0f4f8;
    --surface:   #ffffff;
    --surface-2: #f8fafc;
    --surface-3: #f1f5f9;
    --border:    #e2e8f0;
    --border-md: #cbd5e1;
    --border-strong: #cbd5e1;
    --border-em: rgba(16,185,129,0.3);
    --em-dim:    #d1fae5;
    --em-glow:   rgba(16,185,129,0.12);
    --emerald-light: #d1fae5;
    --blue-light: #dbeafe;
    --amber-light: #fef3c7;
    --red-light:  #fee2e2;
    --purple-light: #ede9fe;
    --text:      #0f172a;
    --text-2:    #475569;
    --text-3:    #94a3b8;
    --text-4:    #cbd5e1;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.07), 0 1px 2px rgba(0,0,0,0.04);
    --shadow-md: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
    --shadow-lg: 0 10px 30px rgba(0,0,0,0.1), 0 4px 8px rgba(0,0,0,0.06);
  }

  [data-theme="light"] .rec-box {
    background: linear-gradient(135deg, #f0fdf4, #eff6ff);
  }
  [data-theme="light"] .traj-thought { background: #eff6ff; }
  [data-theme="light"] .traj-obs     { background: #f0fdf4; }
  [data-theme="light"] .tools-strip  { background: #fafcff; }
  [data-theme="light"] .src-chip {
    background: #fef9ec;
    color: #92400e;
    border-color: rgba(245,158,11,0.25);
  }
  [data-theme="light"] .tool-badge {
    background: #dbeafe;
    color: #3b82f6;
    border-color: rgba(59,130,246,0.2);
  }
  [data-theme="light"] .mini-badge {
    background: #ede9fe;
    color: #8b5cf6;
  }
  [data-theme="light"] .emergency-bar {
    background: #ede9fe;
    border-color: #8b5cf6;
  }
  [data-theme="light"] .card-emergency {
    box-shadow: 0 4px 24px rgba(139,92,246,0.14), var(--shadow-md) !important;
  }
  [data-theme="light"] .card-emergency .card-header {
    background: linear-gradient(135deg, rgba(139,92,246,0.07), rgba(239,68,68,0.04));
  }
  [data-theme="light"] .export-btn:hover {
    background: #dbeafe;
    border-color: #3b82f6;
    color: #3b82f6;
  }
  [data-theme="light"] .hist-item:hover { background: #f8fafc; }
  [data-theme="light"] .followup-chip { background: #ffffff; border-color: #cbd5e1; }
  [data-theme="light"] .followup-chip:hover { background: #d1fae5; }
  [data-theme="light"] .copy-btn:hover { background: #d1fae5; border-color: #10b981; color: #059669; }
  [data-theme="light"] .rag-chunk { background: #ffffff; }
  [data-theme="light"] .card-foot { background: #f8fafc; }
  [data-theme="light"] .card-header { background: #f8fafc; }
```

- [ ] **Step 3: Cambiar default del tema en `initTheme()`**

Reemplazar:
```js
  const saved = localStorage.getItem('medi-theme') || 'light';
```
Por:
```js
  const saved = localStorage.getItem('medi-theme') || 'dark';
```

- [ ] **Step 4: Cambiar default en llamada a `_syncThemeIcon`**

Reemplazar:
```js
_syncThemeIcon(localStorage.getItem('medi-theme') || 'light');
```
Por:
```js
_syncThemeIcon(localStorage.getItem('medi-theme') || 'dark');
```

- [ ] **Step 5: Verificar visualmente**

```bash
venv/Scripts/python.exe app.py
```
Abrir `http://localhost:5000`. La página debe cargar en dark por defecto. El toggle luna/sol debe funcionar. No debe haber flash blanco al cargar.

- [ ] **Step 6: Commit**

```bash
git add templates/index.html
git commit -m "feat: dark mode como default, tokens CSS dark-first en index.html"
```

---

## Task 2: Hardcoded light colors → dark en component CSS de index.html

**Files:**
- Modify: `templates/index.html` (varias reglas CSS con colores hardcodeados)

- [ ] **Step 1: Rec box — quitar gradiente light**

Reemplazar:
```css
    background: linear-gradient(135deg, #f0fdf4, #eff6ff);
```
Por:
```css
    background: rgba(16,185,129,0.04);
```

- [ ] **Step 2: Tools strip — quitar fondo hardcodeado**

Reemplazar:
```css
    background: #fafcff;
```
(la que está dentro de `.tools-strip`) Por:
```css
    background: rgba(255,255,255,0.02);
```

- [ ] **Step 3: Traj-thought y traj-obs — fondos dark**

Reemplazar:
```css
  .traj-thought {
    background: #eff6ff;
    border-left: 3px solid var(--blue);
    color: var(--text-2);
  }

  .traj-obs {
    background: #f0fdf4;
    border-left: 3px solid var(--emerald);
    color: var(--text-2);
  }
```
Por:
```css
  .traj-thought {
    background: rgba(59,130,246,0.08);
    border-left: 3px solid var(--blue);
    color: var(--text-2);
  }

  .traj-obs {
    background: rgba(16,185,129,0.08);
    border-left: 3px solid var(--emerald);
    color: var(--text-2);
  }
```

- [ ] **Step 4: Src-chip — colores dark**

Reemplazar:
```css
  .src-chip {
    font-size: 10.5px;
    padding: 3px 8px;
    background: #fef9ec;
    color: #92400e;
    border: 1px solid rgba(245,158,11,0.25);
    border-radius: 10px;
  }
```
Por:
```css
  .src-chip {
    font-size: 10.5px;
    padding: 3px 8px;
    background: rgba(245,158,11,0.08);
    color: #fbbf24;
    border: 1px solid rgba(245,158,11,0.2);
    border-radius: 10px;
  }
```

- [ ] **Step 5: AI card — glass shadow + card-header rgba**

Reemplazar:
```css
  .ai-card {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: var(--shadow-md);
  }

  .card-header {
    padding: 14px 18px;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    border-bottom: 1px solid var(--border);
    background: var(--surface-2);
  }
```
Por:
```css
  .ai-card {
    flex: 1;
    background: var(--surface);
    border: 1px solid var(--border-md);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.04);
  }

  .card-header {
    padding: 14px 18px;
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    border-bottom: 1px solid var(--border);
    background: rgba(255,255,255,0.02);
  }
```

- [ ] **Step 6: Confidence fill — quitar gradiente azul-verde**

Reemplazar:
```css
    background: linear-gradient(90deg, var(--emerald), var(--blue));
```
(la que está dentro de `.conf-fill`) Por:
```css
    background: var(--emerald);
```

- [ ] **Step 7: Card foot — fondo plano dark**

Reemplazar:
```css
  .card-foot {
    padding: 10px 18px;
    display: flex;
    align-items: center;
    gap: 8px;
    background: var(--surface-2);
    border-top: 1px solid var(--border);
  }
```
Por:
```css
  .card-foot {
    padding: 10px 18px;
    display: flex;
    align-items: center;
    gap: 8px;
    background: rgba(255,255,255,0.01);
    border-top: 1px solid var(--border);
  }
```

- [ ] **Step 8: Severity pills — rgba dark**

Reemplazar:
```css
  .sev-pill.leve { background: var(--emerald-light); color: var(--emerald-dark); border: 1px solid rgba(16,185,129,0.3); }
  .sev-pill.moderada { background: var(--amber-light); color: #92400e; border: 1px solid rgba(245,158,11,0.3); }
  .sev-pill.grave { background: var(--red-light); color: #991b1b; border: 1px solid rgba(239,68,68,0.3); }
  .sev-pill.emergencia {
    background: var(--purple-light);
    color: #5b21b6;
    border: 1px solid rgba(139,92,246,0.4);
    animation: pulse-sev 1.5s infinite;
  }
```
Por:
```css
  .sev-pill.leve     { background: var(--em-dim);                    color: var(--em);   border: 1px solid rgba(16,185,129,0.25); }
  .sev-pill.moderada { background: rgba(245,158,11,0.10);            color: #f59e0b;     border: 1px solid rgba(245,158,11,0.25); }
  .sev-pill.grave    { background: rgba(239,68,68,0.10);             color: #ef4444;     border: 1px solid rgba(239,68,68,0.25); }
  .sev-pill.emergencia {
    background: rgba(139,92,246,0.12);
    color: #a78bfa;
    border: 1px solid rgba(139,92,246,0.35);
    animation: pulse-sev 1.5s infinite;
  }
```

- [ ] **Step 9: Verificar visualmente**

```bash
venv/Scripts/python.exe app.py
```
Abrir `http://localhost:5000`. Hacer una consulta de prueba. Verificar:
- Card respuesta con fondo oscuro, sin gradiente en rec-box
- Severity pills con colores rgba correctos
- Confidence bar color sólido verde
- Fragments traj-thought y traj-obs con fondos rgba

- [ ] **Step 10: Commit**

```bash
git add templates/index.html
git commit -m "feat: hardcoded light colors → dark en cards, traj, src-chip, conf-fill"
```

---

## Task 3: Sidebar CSS + HTML en index.html

**Files:**
- Modify: `templates/index.html` (CSS sidebar líneas ~53-256, HTML sidebar líneas ~1204-1277)

- [ ] **Step 1: Logo icon — quitar gradiente, aplicar glass emerald**

Reemplazar:
```css
  .logo-icon {
    width: 38px;
    height: 38px;
    background: linear-gradient(135deg, var(--emerald), var(--blue));
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 18px;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(16,185,129,0.3);
  }
```
Por:
```css
  .logo-icon {
    width: 32px;
    height: 32px;
    background: var(--em-dim);
    border: 1px solid var(--border-em);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 0 14px var(--em-glow);
  }
```

- [ ] **Step 2: Sidebar-btn active — emerald glass**

Reemplazar:
```css
  .sidebar-btn.active { background: var(--emerald-light); color: var(--emerald-dark); font-weight: 500; }
```
Por:
```css
  .sidebar-btn.active { background: var(--em-dim); border: 1px solid var(--border-em); color: var(--em); font-weight: 500; }
```

- [ ] **Step 3: Status panel — fondo dark sutil**

Reemplazar:
```css
  .status-panel {
    margin: 0 14px;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 14px;
  }
```
Por:
```css
  .status-panel {
    margin: 0 14px;
    background: rgba(255,255,255,0.02);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 14px;
  }
```

- [ ] **Step 4: Quitar CSS de .tool-list y .tool-item**

Reemplazar:
```css
  .tool-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 0 14px;
  }

  .tool-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 7px 10px;
    background: var(--surface-2);
    border-radius: 7px;
    border: 1px solid var(--border);
    font-size: 11.5px;
    color: var(--text-2);
  }

  .tool-item svg.lucide { opacity: 0.6; }
```
Por:
```css
  /* tool-list eliminado — aparece en panel de detalles de la card */
```

- [ ] **Step 5: Actualizar color del ícono del logo en HTML**

Reemplazar en el HTML:
```html
    <div class="logo-icon"><i data-lucide="stethoscope" style="width:20px;height:20px;color:white;stroke-width:1.75"></i></div>
```
Por:
```html
    <div class="logo-icon"><i data-lucide="stethoscope" style="width:16px;height:16px;color:var(--em);stroke-width:2"></i></div>
```

- [ ] **Step 6: Quitar sección "Herramientas activas" del HTML**

Reemplazar:
```html
  <div class="sidebar-section" style="margin-top:4px">
    <div class="sidebar-label">Herramientas activas</div>
    <div class="tool-list">
      <div class="tool-item"><i data-lucide="search" style="width:13px;height:13px;stroke-width:2"></i> search_symptoms</div>
      <div class="tool-item"><i data-lucide="alert-triangle" style="width:13px;height:13px;stroke-width:2"></i> assess_urgency</div>
      <div class="tool-item"><i data-lucide="pill" style="width:13px;height:13px;stroke-width:2"></i> get_drug_info</div>
      <div class="tool-item"><i data-lucide="book-open" style="width:13px;height:13px;stroke-width:2"></i> get_section</div>
    </div>
  </div>
```
Por:
```html
  <!-- herramientas visibles en panel de detalles de cada card -->
```

- [ ] **Step 7: Verificar visualmente**

```bash
venv/Scripts/python.exe app.py
```
Abrir `http://localhost:5000`. Verificar:
- Sidebar 200px, logo icon con glow verde sin gradiente
- Nav item activo con borde y fondo emerald glass
- Sección herramientas eliminada del sidebar

- [ ] **Step 8: Commit**

```bash
git add templates/index.html
git commit -m "feat: sidebar CSS glass + quitar seccion herramientas"
```

---

## Task 4: Topbar CSS + HTML en index.html

**Files:**
- Modify: `templates/index.html` (CSS topbar, HTML topbar)

- [ ] **Step 1: Topbar — reducir a 52px y simplificar**

Reemplazar:
```css
  .topbar {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 24px;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }
```
Por:
```css
  .topbar {
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    padding: 0 20px;
    height: 52px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }
```

- [ ] **Step 2: Agregar CSS para .topbar-chip**

Agregar después del bloque `.meta-chip { ... }` existente (aproximadamente línea 310):

Reemplazar:
```css
  .meta-chip .icon { font-size: 12px; }
```
Por:
```css
  .meta-chip .icon { font-size: 12px; }

  .topbar-chip {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 4px 11px;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border-md);
    border-radius: 20px;
    font-size: 11px;
    color: var(--text-3);
  }

  .topbar-live {
    width: 5px; height: 5px;
    background: var(--em);
    border-radius: 50%;
    box-shadow: 0 0 5px var(--em);
    flex-shrink: 0;
  }
```

- [ ] **Step 3: Actualizar HTML del topbar**

Reemplazar el bloque del topbar completo:
```html
  <!-- Topbar -->
  <div class="topbar">
    <div class="topbar-title">
      <button class="hamburger-btn" onclick="toggleSidebar()" aria-label="Menú">
        <i data-lucide="menu" style="width:18px;height:18px;stroke-width:2"></i>
      </button>
      <i data-lucide="stethoscope" style="width:17px;height:17px;color:var(--emerald);stroke-width:2"></i>
      <span>MEDI-IA</span>
      <span class="breadcrumb">&nbsp;/ Evaluación de síntomas</span>
    </div>
    <div class="topbar-meta">
      <button class="theme-btn" id="themeToggle" onclick="toggleTheme()" title="Cambiar tema">
        <i data-lucide="moon" id="themeIcon" style="width:15px;height:15px;stroke-width:2"></i>
      </button>
      <button onclick="doLogout()" style="display:flex;align-items:center;gap:5px;padding:5px 13px;border:1px solid var(--border-strong);border-radius:8px;background:transparent;color:var(--text-3);font-size:12px;font-family:'Inter',sans-serif;cursor:pointer;transition:all 0.15s;" onmouseover="this.style.color='var(--red)';this.style.borderColor='var(--red)'" onmouseout="this.style.color='var(--text-3)';this.style.borderColor='var(--border-strong)'">
        <i data-lucide="log-out" style="width:13px;height:13px"></i> Salir
      </button>
    </div>
  </div>
```
Por:
```html
  <!-- Topbar -->
  <div class="topbar">
    <div class="topbar-title">
      <button class="hamburger-btn" onclick="toggleSidebar()" aria-label="Menú">
        <i data-lucide="menu" style="width:18px;height:18px;stroke-width:2"></i>
      </button>
      <i data-lucide="stethoscope" style="width:15px;height:15px;color:var(--em);stroke-width:2"></i>
      <span>MEDI-IA</span>
      <span class="breadcrumb">&nbsp;/ Evaluación de síntomas</span>
    </div>
    <div class="topbar-meta">
      <div class="topbar-chip">
        <span class="topbar-live"></span>
        RAG · <span id="topbarLibros">14</span> libros
      </div>
      <button class="theme-btn" id="themeToggle" onclick="toggleTheme()" title="Cambiar tema">
        <i data-lucide="sun" id="themeIcon" style="width:15px;height:15px;stroke-width:2"></i>
      </button>
      {% if auth_enabled %}
      <button onclick="doLogout()" style="display:flex;align-items:center;gap:5px;padding:5px 13px;border:1px solid var(--border-md);border-radius:8px;background:transparent;color:var(--text-3);font-size:12px;font-family:'Inter',sans-serif;cursor:pointer;transition:all 0.15s;" onmouseover="this.style.color='var(--red)';this.style.borderColor='var(--red)'" onmouseout="this.style.color='var(--text-3)';this.style.borderColor='var(--border-md)'">
        <i data-lucide="log-out" style="width:13px;height:13px"></i> Salir
      </button>
      {% endif %}
    </div>
  </div>
```

> Nota: `auth_enabled` ya se pasa como variable Jinja2 desde `app.py` — verificar con `grep -n "auth_enabled" app.py`. Si no existe, usar el patrón existente del botón Salir sin condicional.

- [ ] **Step 4: Actualizar `loadHealthStatus` para llenar `#topbarLibros`**

En la función `loadHealthStatus()`, después de la línea que setea `sidebarModo`, agregar:

Reemplazar:
```js
    // Modo
    const modo = document.getElementById('sidebarModo');
    if (modo) modo.textContent = h.hf_activo ? 'ReAct' : 'RAG';

    // Motor
    const motor = document.getElementById('sidebarMotor');
    if (motor) motor.textContent = h.hf_activo ? 'Qwen 2.5-7B' : 'RAG Template';
```
Por:
```js
    // Modo
    const modo = document.getElementById('sidebarModo');
    if (modo) modo.textContent = h.hf_activo ? 'ReAct' : 'RAG';

    // Motor
    const motor = document.getElementById('sidebarMotor');
    if (motor) motor.textContent = h.hf_activo ? 'Qwen 2.5-7B' : 'RAG Template';

    // Topbar chip
    const topbarLibros = document.getElementById('topbarLibros');
    if (topbarLibros && h.libros?.length) topbarLibros.textContent = h.libros.length;
```

- [ ] **Step 5: Verificar si `auth_enabled` existe en app.py**

```bash
grep -n "auth_enabled" app.py
```

Si no aparece, revertir el condicional Jinja2 del Step 3 y dejar el botón Salir sin `{% if %}`.

- [ ] **Step 6: Verificar visualmente**

```bash
venv/Scripts/python.exe app.py
```
Abrir `http://localhost:5000`. Verificar:
- Topbar 52px, chip "RAG · N libros" visible con live dot
- Botón Salir solo aparece si AUTH_PASSWORD está definida (o siempre si se revirtió el condicional)

- [ ] **Step 7: Commit**

```bash
git add templates/index.html
git commit -m "feat: topbar 52px, chip RAG libros, icono emerald"
```

---

## Task 5: Welcome screen CSS + HTML + JS en index.html

**Files:**
- Modify: `templates/index.html` (CSS welcome, HTML welcome, JS `loadHealthStatus`)

- [ ] **Step 1: Welcome logo — glass border + glow**

Reemplazar:
```css
  .welcome-logo {
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, var(--emerald-light), var(--blue-light));
    border: 2px solid var(--emerald);
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 36px;
    box-shadow: var(--shadow-md);
    animation: welcome-pulse 3s ease-in-out infinite;
  }
```
Por:
```css
  .welcome-logo {
    width: 64px;
    height: 64px;
    background: var(--em-dim);
    border: 1.5px solid var(--border-em);
    border-radius: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 0 32px var(--em-glow), 0 0 0 8px rgba(16,185,129,0.04);
    animation: welcome-pulse 3s ease-in-out infinite;
  }
```

- [ ] **Step 2: Agregar CSS para `.tech-badge`**

Agregar después del bloque `.welcome p { ... }`:

Reemplazar:
```css
  .chips-grid {
```
Por:
```css
  .tech-badge {
    display: flex;
    align-items: center;
    gap: 6px;
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--border-md);
    border-radius: 20px;
    padding: 5px 14px;
    font-size: 10.5px;
    color: var(--text-3);
  }

  .tech-badge .live-dot {
    width: 5px; height: 5px;
    background: var(--em);
    border-radius: 50%;
    box-shadow: 0 0 4px var(--em);
    flex-shrink: 0;
  }

  .chips-grid {
```

- [ ] **Step 3: Ex-chip hover — emerald**

Reemplazar:
```css
  .ex-chip:hover {
    background: var(--emerald-light);
    border-color: var(--emerald);
    color: var(--emerald-dark);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
  }
```
Por:
```css
  .ex-chip:hover {
    background: var(--em-dim);
    border-color: var(--border-em);
    color: var(--em);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md);
  }
```

- [ ] **Step 4: Actualizar HTML del welcome state**

Reemplazar el bloque completo del welcome:
```html
    <div class="welcome" id="welcomeState">
      <div class="welcome-logo"><i data-lucide="stethoscope" style="width:38px;height:38px;stroke-width:1.25;color:var(--emerald)"></i></div>
      <h2>¿Cómo te sientes hoy?</h2>
      <p>Describe tus síntomas con el mayor detalle posible. El agente analizará tu consulta con la base de conocimiento médico y te entregará un diagnóstico diferencial.</p>
      <div id="welcomeStats" style="display:flex;gap:8px;flex-wrap:wrap;justify-content:center;min-height:26px;"></div>
      <div class="chips-grid">
        <button class="ex-chip" onclick="fillEx(this)"><i data-lucide="thermometer" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Fiebre y dolor muscular</button>
        <button class="ex-chip" onclick="fillEx(this)"><i data-lucide="heart" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Dolor en el pecho y brazo</button>
        <button class="ex-chip" onclick="fillEx(this)"><i data-lucide="wind" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Tos con flema y dificultad respiratoria</button>
        <button class="ex-chip" onclick="fillEx(this)"><i data-lucide="droplets" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Ardor al orinar y micción frecuente</button>
        <button class="ex-chip" onclick="fillEx(this)"><i data-lucide="brain" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Dolor de cabeza intenso con náuseas</button>
        <button class="ex-chip" onclick="fillEx(this)"><i data-lucide="eye" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Picazón en los ojos y estornudos</button>
      </div>
    </div>
```
Por:
```html
    <div class="welcome" id="welcomeState">
      <div class="welcome-logo"><i data-lucide="stethoscope" style="width:30px;height:30px;stroke-width:1.5;color:var(--em)"></i></div>
      <h2>¿Cómo te sientes hoy?</h2>
      <p>Describe tus síntomas con detalle. El agente analiza tu consulta contra 14 libros médicos y entrega un diagnóstico diferencial fundamentado.</p>
      <div class="tech-badge" id="welcomeTechBadge">
        <span class="live-dot"></span>
        <span id="welcomeBadgeText">136K chunks · e5-base · BM25+RRF · Recall@1 97.1%</span>
      </div>
      <div class="chips-grid">
        <button class="ex-chip" onclick="fillEx(this)"><i data-lucide="thermometer" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Fiebre y dolor muscular</button>
        <button class="ex-chip" onclick="fillEx(this)"><i data-lucide="heart" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Dolor en el pecho y brazo</button>
        <button class="ex-chip" onclick="fillEx(this)"><i data-lucide="wind" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Tos con flema y dificultad respiratoria</button>
        <button class="ex-chip" onclick="fillEx(this)"><i data-lucide="droplets" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Ardor al orinar y micción frecuente</button>
        <button class="ex-chip" onclick="fillEx(this)"><i data-lucide="brain" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Dolor de cabeza intenso con náuseas</button>
        <button class="ex-chip" onclick="fillEx(this)"><i data-lucide="eye" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Picazón en los ojos y estornudos</button>
      </div>
    </div>
```

- [ ] **Step 5: Actualizar JS `loadHealthStatus` para llenar el badge**

Reemplazar el bloque `const ws = document.getElementById('welcomeStats')` completo:
```js
    const ws = document.getElementById('welcomeStats');
    if (ws) {
      const modeLabel = h.hf_activo ? 'ReAct + LLM' : 'RAG Template';
      const chunksLabel = h.chunks_indexados ? h.chunks_indexados.toLocaleString() + ' fragmentos' : '—';
      const librosLabel = h.libros?.length ? h.libros.length + ' libros' : '—';
      ws.innerHTML = `
        <span class="meta-chip"><i data-lucide="database" style="width:11px;height:11px"></i> ${chunksLabel}</span>
        <span class="meta-chip"><i data-lucide="${h.hf_activo ? 'cpu' : 'layers'}" style="width:11px;height:11px"></i> ${modeLabel}</span>
        <span class="meta-chip"><i data-lucide="book-open" style="width:11px;height:11px"></i> ${librosLabel}</span>`;
      lucide.createIcons({ nodes: [ws] });
    }
```
Por:
```js
    const badgeText = document.getElementById('welcomeBadgeText');
    if (badgeText) {
      const chunks = h.chunks_indexados ? h.chunks_indexados.toLocaleString() + ' chunks' : '136K chunks';
      const libros = h.libros?.length ? h.libros.length + ' libros' : '14 libros';
      const modo   = h.hf_activo ? 'ReAct' : 'RAG';
      badgeText.textContent = `${chunks} · e5-base · BM25+RRF · ${libros} · ${modo}`;
    }
```

- [ ] **Step 6: Verificar visualmente**

```bash
venv/Scripts/python.exe app.py
```
Abrir `http://localhost:5000`. Verificar:
- Welcome logo 64px con glow verde, sin gradiente
- Badge técnico muestra datos reales del servidor
- Chips hover color emerald correcto

- [ ] **Step 7: Commit**

```bash
git add templates/index.html
git commit -m "feat: welcome screen rediseñada — logo glass, tech badge, chips emerald"
```

---

## Task 6: Dark tokens en login.html, metrics.html, evaluate.html

**Files:**
- Modify: `templates/login.html`
- Modify: `templates/metrics.html`
- Modify: `templates/evaluate.html`

### login.html

- [ ] **Step 1: Reemplazar variables `:root` de login.html**

Reemplazar:
```css
  :root {
    --bg: #f0f4f8;
    --surface: #ffffff;
    --border: #e2e8f0;
    --border-strong: #cbd5e1;
    --emerald: #10b981;
    --emerald-dark: #059669;
    --emerald-light: #d1fae5;
    --red: #ef4444;
    --red-light: #fee2e2;
    --text: #0f172a;
    --text-2: #475569;
    --text-3: #94a3b8;
    --shadow-md: 0 4px 12px rgba(0,0,0,0.08), 0 2px 4px rgba(0,0,0,0.04);
    --shadow-lg: 0 10px 30px rgba(0,0,0,0.1), 0 4px 8px rgba(0,0,0,0.06);
  }
```
Por:
```css
  :root {
    --bg:        #090e1a;
    --surface:   #0f1629;
    --border:    rgba(255,255,255,0.09);
    --border-strong: rgba(255,255,255,0.12);
    --border-em: rgba(16,185,129,0.20);
    --emerald:   #10b981;
    --em:        #10b981;
    --emerald-dark: #059669;
    --em-dim:    rgba(16,185,129,0.12);
    --em-glow:   rgba(16,185,129,0.18);
    --emerald-light: rgba(16,185,129,0.12);
    --red:       #ef4444;
    --red-light: rgba(239,68,68,0.12);
    --text:      #f1f5f9;
    --text-2:    #94a3b8;
    --text-3:    #475569;
    --shadow-md: 0 4px 12px rgba(0,0,0,0.45);
    --shadow-lg: 0 10px 30px rgba(0,0,0,0.55);
  }
```

- [ ] **Step 2: Quitar gradiente del logo-icon en login.html**

Reemplazar:
```css
    background: linear-gradient(135deg, var(--emerald), #3b82f6);
```
(la de `.logo-icon` en login.html) Por:
```css
    background: var(--em-dim);
    border: 1px solid var(--border-em);
    box-shadow: 0 0 14px var(--em-glow);
```

- [ ] **Step 3: Input dark en login.html**

Reemplazar:
```css
    background: #f8fafc;
```
(la de `input[type="password"]`) Por:
```css
    background: rgba(255,255,255,0.04);
```

### metrics.html

- [ ] **Step 4: Reemplazar variables `:root` de metrics.html**

Reemplazar:
```css
    --bg: #f0f4f8; --surface: #ffffff; --surface-2: #f8fafc;
    --border: #e2e8f0; --border-strong: #cbd5e1;
    --emerald: #10b981; --emerald-dark: #059669; --emerald-light: #d1fae5;
    --blue: #3b82f6; --blue-light: #dbeafe;
    --amber: #f59e0b; --amber-light: #fef3c7;
    --red: #ef4444; --red-light: #fee2e2;
    --purple: #8b5cf6; --purple-light: #ede9fe;
    --text: #0f172a; --text-2: #475569; --text-3: #94a3b8; --text-4: #cbd5e1;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.07); --shadow-md: 0 4px 12px rgba(0,0,0,0.08);
```
Por:
```css
    --bg:        #090e1a; --surface:   #0f1629; --surface-2: #111d35;
    --border:    rgba(255,255,255,0.06); --border-strong: rgba(255,255,255,0.12);
    --emerald:   #10b981; --em: #10b981; --emerald-dark: #059669; --emerald-light: rgba(16,185,129,0.12);
    --blue:      #3b82f6; --blue-light: rgba(59,130,246,0.12);
    --amber:     #f59e0b; --amber-light: rgba(245,158,11,0.12);
    --red:       #ef4444; --red-light: rgba(239,68,68,0.12);
    --purple:    #8b5cf6; --purple-light: rgba(139,92,246,0.12);
    --text:      #f1f5f9; --text-2: #94a3b8; --text-3: #475569; --text-4: #2d4060;
    --shadow-sm: 0 1px 3px rgba(0,0,0,0.4); --shadow-md: 0 4px 12px rgba(0,0,0,0.45);
```

### evaluate.html

- [ ] **Step 5: Reemplazar variables `:root` de evaluate.html**

Reemplazar:
```css
    --bg:#f0f4f8; --surface:#ffffff; --surface-2:#f8fafc;
    --border:#e2e8f0; --border-strong:#cbd5e1;
    --emerald:#10b981; --emerald-dark:#059669; --emerald-light:#d1fae5;
    --blue:#3b82f6; --blue-light:#dbeafe;
    --amber:#f59e0b; --amber-light:#fef3c7;
    --red:#ef4444; --red-light:#fee2e2;
    --purple:#8b5cf6; --purple-light:#ede9fe;
    --text:#0f172a; --text-2:#475569; --text-3:#94a3b8; --text-4:#cbd5e1;
    --shadow-sm:0 1px 3px rgba(0,0,0,0.07); --shadow-md:0 4px 12px rgba(0,0,0,0.08);
```
Por:
```css
    --bg:#090e1a; --surface:#0f1629; --surface-2:#111d35;
    --border:rgba(255,255,255,0.06); --border-strong:rgba(255,255,255,0.12);
    --emerald:#10b981; --em:#10b981; --emerald-dark:#059669; --emerald-light:rgba(16,185,129,0.12);
    --blue:#3b82f6; --blue-light:rgba(59,130,246,0.12);
    --amber:#f59e0b; --amber-light:rgba(245,158,11,0.12);
    --red:#ef4444; --red-light:rgba(239,68,68,0.12);
    --purple:#8b5cf6; --purple-light:rgba(139,92,246,0.12);
    --text:#f1f5f9; --text-2:#94a3b8; --text-3:#475569; --text-4:#2d4060;
    --shadow-sm:0 1px 3px rgba(0,0,0,0.4); --shadow-md:0 4px 12px rgba(0,0,0,0.45);
```

- [ ] **Step 6: Verificar las 3 páginas**

```bash
venv/Scripts/python.exe app.py
```
Abrir:
- `http://localhost:5000/login` → card oscura, logo sin gradiente, input dark
- `http://localhost:5000/metrics` → fondo oscuro, cards dark
- `http://localhost:5000/evaluate` → fondo oscuro, cards dark

- [ ] **Step 7: Commit final**

```bash
git add templates/login.html templates/metrics.html templates/evaluate.html
git commit -m "feat: dark tokens en login, metrics y evaluate templates"
```

---

## Resumen de commits esperados

```
feat: dark mode como default, tokens CSS dark-first en index.html
feat: hardcoded light colors → dark en cards, traj, src-chip, conf-fill
feat: sidebar CSS glass + quitar seccion herramientas
feat: topbar 52px, chip RAG libros, icono emerald
feat: welcome screen rediseñada — logo glass, tech badge, chips emerald
feat: dark tokens en login, metrics y evaluate templates
```
