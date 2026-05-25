# MEDI-IA — UI Redesign v2.0

**Fecha:** 2026-05-25  
**Alcance:** `templates/index.html` (página principal), con ajustes menores en `login.html`, `metrics.html`, `evaluate.html`  
**Objetivo:** Subir el nivel visual para presentación académica — dark glassmorphism sobrio, acento emerald, sin gradientes agresivos.

---

## Decisiones de diseño (confirmadas por el usuario)

| Decisión | Elección |
|----------|----------|
| Estilo | Dark glassmorphism con pocos gradientes |
| Fondo base | `#090e1a` (azul-negro profundo) |
| Surface cards | `#0f1629` / `#111d35` |
| Acento principal | Emerald `#10b981` (sin cambio de color) |
| Layout | Sidebar compacto siempre visible (~200px, ícono + label) |
| Welcome screen | Logo + título + badge técnico + chips de ejemplo |
| Dark mode | Por defecto — el toggle sigue existiendo |

---

## 1. Tokens de color (CSS variables)

Reemplazar las variables actuales de `data-theme="dark"` como estado por un conjunto base dark:

```css
:root {
  --bg:        #090e1a;
  --surface:   #0f1629;
  --surface-2: #111d35;
  --surface-3: #162140;
  --border:    rgba(255,255,255,0.06);
  --border-md: rgba(255,255,255,0.09);
  --border-em: rgba(16,185,129,0.20);
  --em:        #10b981;
  --em-dim:    rgba(16,185,129,0.12);
  --em-glow:   rgba(16,185,129,0.18);
  --text:      #f1f5f9;
  --text-2:    #94a3b8;
  --text-3:    #475569;
  --amber:     #f59e0b;
  --red:       #ef4444;
  --purple:    #8b5cf6;
  --blue:      #3b82f6;
  /* shadows dark-native */
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.4);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.45);
  --shadow-lg: 0 10px 30px rgba(0,0,0,0.55);
}

/* Light mode override (toggle sigue funcionando) */
[data-theme="light"] {
  --bg:        #f0f4f8;
  --surface:   #ffffff;
  --surface-2: #f8fafc;
  /* ... resto igual que el actual "light" ... */
}
```

---

## 2. Sidebar

**Antes:** 260px, muchas secciones, fondo blanco / dark.  
**Después:** 200px, fondo `var(--surface)`, borde derecho `1px solid var(--border)`.

### Estructura
```
Logo (ícono 30px + "MEDI-IA" + "Asistente médico")
─────────────────────────────────
NAV LABEL: "CONSULTA"
  [active] ● Síntomas
  [ ]      ↗ Estado del sistema
  [ ]      ▦ Métricas
  [ ]      ⧉ Evaluación RAG
─────────────────────────────────
NAV LABEL: "ESTADO"
  Status box (Sistema / Índice / Modo)
─────────────────────────────────
[Historial — si existe]
─────────────────────────────────
Footer (margin-top:auto)
  [Exportar sesión]
  [Nueva consulta]
```

### Estilos clave
- `.nav-item.active`: `background: var(--em-dim)`, `border: 1px solid var(--border-em)`, `color: var(--em)`
- `.logo-icon`: `background: var(--em-dim)`, `border: 1px solid var(--border-em)`, `box-shadow: 0 0 14px var(--em-glow)`
- `.status-box`: `background: rgba(255,255,255,0.02)`, `border: 1px solid var(--border)`
- Eliminar sección "Herramientas activas" (demasiado técnico, ya aparece en card de detalles)

---

## 3. Topbar

**Antes:** 56px, muy cargado.  
**Después:** 52px, más minimalista.

- Izquierda: ícono emerald + "MEDI-IA" + breadcrumb gris
- Derecha: chip "RAG · 14 libros" + live dot + botón tema

Eliminar el botón "Salir" del topbar si no hay `AUTH_PASSWORD` configurada (condicional en Jinja2 — ya existe la lógica). En presentación sin auth no debe aparecer.

---

## 4. Welcome screen

```
[Logo 64px — glass border, emerald glow]
"¿Cómo te sientes hoy?"          ← h2 24px bold
"Describe tus síntomas..."        ← p gris, max-width 420px
[● badge: 136K chunks · e5-base · BM25+RRF · Recall@1 97.1%]
[grid 2 cols, 6 chips de ejemplo]
```

- Logo: `border: 1.5px solid var(--border-em)`, `box-shadow: 0 0 32px var(--em-glow), 0 0 0 8px rgba(16,185,129,0.04)`
- El badge técnico carga los valores reales desde `/api/health` (igual que el `welcomeStats` actual)
- Chips: `background: rgba(255,255,255,0.03)`, hover → `border-color: var(--border-em)`, `color: var(--em)`, `background: var(--em-dim)`

---

## 5. Cards de respuesta AI

### Card header
- Background: `rgba(255,255,255,0.02)` en lugar de `var(--surface-2)` 
- Severity pills: Reemplazar colores light (`--emerald-light`, etc.) por versiones rgba sobre dark:
  - leve:       `background: var(--em-dim)`, `border: 1px solid rgba(16,185,129,0.25)`, `color: var(--em)`
  - moderada:   `background: rgba(245,158,11,0.10)`, `border: rgba(245,158,11,0.25)`, `color: #f59e0b`
  - grave:      `background: rgba(239,68,68,0.10)`, `border: rgba(239,68,68,0.25)`, `color: #ef4444`
  - emergencia: `background: rgba(139,92,246,0.12)`, `border: rgba(139,92,246,0.35)`, `color: #a78bfa`

### Confidence bar
- Track: `rgba(255,255,255,0.06)` (no más `--border` claro)
- Fill: color sólido `var(--em)` — sin gradiente azul-verde

### Card body
- Background: `var(--surface)` directamente
- Texto `var(--text-2)`, strong → `var(--text)`

### Rec box
- `background: rgba(16,185,129,0.04)` — sin gradiente lineal
- Border bottom: `1px solid var(--border)`

### Card footer
- `background: rgba(255,255,255,0.01)`
- Botones foot: `background: rgba(255,255,255,0.04)`, `border: 1px solid var(--border-md)`, texto `var(--text-3)`

### Glass effect general
```css
.ai-card {
  box-shadow: 0 4px 24px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.04);
}
```

---

## 6. Input bar

- Container: `background: var(--surface)`, `border-top: 1px solid var(--border)`
- Wrap: `background: var(--surface-2)`, `border: 1.5px solid var(--border-md)`
- Focus: `border-color: var(--border-em)`, `box-shadow: 0 0 0 3px rgba(16,185,129,0.07)`
- Send button: color sólido `var(--em)`, `box-shadow: 0 2px 10px var(--em-glow)` — sin transformaciones agresivas

---

## 7. Otras páginas (ajuste mínimo)

- `login.html`, `metrics.html`, `evaluate.html`: Aplicar los mismos tokens CSS dark como base. No rediseñar estructura. Solo cambiar variables y asegurarse que cargan en dark por defecto.

---

## 8. Toggle de tema

El toggle permanece. Cambio de comportamiento:
- `localStorage` key `medi-theme`, default `"dark"` en vez de `"light"`
- Al cargar sin preferencia guardada → dark automático

---

## 9. Qué NO cambia

- Toda la lógica JS (streaming, SSE, feedback, export PDF, historial)
- Estructura HTML de los elementos (clases, IDs)
- Responsive / mobile (hamburger, sidebar overlay)
- Animaciones existentes (slideIn, bounce, blink)
- Sección de detalles / trazabilidad RAG
- Emergency bar

---

## Archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `templates/index.html` | Rediseño completo de CSS (variables, sidebar, topbar, welcome, cards, input) |
| `templates/login.html` | Variables dark como base, ajuste mínimo |
| `templates/metrics.html` | Variables dark como base, ajuste mínimo |
| `templates/evaluate.html` | Variables dark como base, ajuste mínimo |

No se crean archivos nuevos. No se toca Python.
