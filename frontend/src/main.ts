const chatZone     = document.getElementById('chatZone') as HTMLElement;
const userInput    = document.getElementById('userInput') as HTMLTextAreaElement;
const sendBtn      = document.getElementById('sendBtn') as HTMLButtonElement;
const emergencyBar = document.getElementById('emergencyBar') as HTMLElement;
const progressBar  = document.getElementById('progressBar') as HTMLElement;
let isFirstMsg = true;
let loading = false;
let currentFollowupId = null;
let _progressTimer = null;
let _queryStartTime = null;
let _queryCount = 0;

// V2 — Progress bar
function startProgress() {
  clearTimeout(_progressTimer);
  progressBar.style.transition = 'none';
  progressBar.style.width = '0';
  progressBar.style.opacity = '1';
  requestAnimationFrame(() => {
    progressBar.style.transition = 'width 8s cubic-bezier(0.05,0.8,0.4,1)';
    progressBar.style.width = '82%';
  });
}
function finishProgress() {
  clearTimeout(_progressTimer);
  progressBar.style.transition = 'width 0.25s ease';
  progressBar.style.width = '100%';
  _progressTimer = setTimeout(() => {
    progressBar.style.transition = 'opacity 0.4s ease';
    progressBar.style.opacity = '0';
    setTimeout(() => { progressBar.style.transition = 'none'; progressBar.style.width = '0'; }, 450);
  }, 280);
}

// V5 — Book colors
const BOOK_COLORS = {
  'Harrison':   { bg:'rgba(59,130,246,0.18)',  color:'#60a5fa',  border:'rgba(59,130,246,0.35)'  },
  'Oxford':     { bg:'rgba(16,185,129,0.18)',  color:'#34d399',  border:'rgba(16,185,129,0.35)'  },
  'Symptoms':   { bg:'rgba(139,92,246,0.18)',  color:'#a78bfa',  border:'rgba(139,92,246,0.35)'  },
  'Top 100':    { bg:'rgba(245,158,11,0.18)',  color:'#fbbf24',  border:'rgba(245,158,11,0.35)'  },
  'Tintinalli': { bg:'rgba(239,68,68,0.18)',   color:'#f87171',  border:'rgba(239,68,68,0.35)'   },
  'Adams':      { bg:'rgba(6,182,212,0.18)',   color:'#22d3ee',  border:'rgba(6,182,212,0.35)'   },
  'Robbins':    { bg:'rgba(251,113,133,0.18)', color:'#fb7185',  border:'rgba(251,113,133,0.35)' },
  'Nelson':     { bg:'rgba(52,211,153,0.18)',  color:'#6ee7b7',  border:'rgba(52,211,153,0.35)'  },
  'Kaplan':     { bg:'rgba(168,85,247,0.18)',  color:'#c084fc',  border:'rgba(168,85,247,0.35)'  },
  'Williams':   { bg:'rgba(236,72,153,0.18)',  color:'#f472b6',  border:'rgba(236,72,153,0.35)'  },
  'Lange':      { bg:'rgba(234,179,8,0.18)',   color:'#fde047',  border:'rgba(234,179,8,0.35)'   },
  'ABC':        { bg:'rgba(20,184,166,0.18)',  color:'#2dd4bf',  border:'rgba(20,184,166,0.35)'  },
  'Infectious': { bg:'rgba(99,102,241,0.18)',  color:'#818cf8',  border:'rgba(99,102,241,0.35)'  },
  'HARRISONS':  { bg:'rgba(59,130,246,0.18)',  color:'#60a5fa',  border:'rgba(59,130,246,0.35)'  },
};
function getBookColor(name) {
  for (const [k, v] of Object.entries(BOOK_COLORS)) {
    if ((name || '').includes(k)) return v;
  }
  return { bg:'rgba(100,116,139,0.15)', color:'#94a3b8', border:'rgba(100,116,139,0.3)' };
}

// Auto-resize textarea
userInput.addEventListener('input', () => {
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
});

userInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

// U3 — Escape key handler
document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  const drawer = document.getElementById('bodyDrawer');
  if (drawer?.classList.contains('open')) { closeBodyDrawer(); return; }
  const modal = document.getElementById('profileModal');
  if (modal?.style.display && modal.style.display !== 'none') { closeProfileModal(); return; }
  if (document.getElementById('onboardingOverlay')?.classList.contains('active')) { skipOnboarding(); return; }
  userInput.blur();
});

// U4 — Scroll-to-bottom visibility
const scrollBtn = document.getElementById('scrollBottomBtn');
chatZone.addEventListener('scroll', () => {
  const distFromBottom = chatZone.scrollHeight - chatZone.scrollTop - chatZone.clientHeight;
  scrollBtn?.classList.toggle('visible', distFromBottom > 200);
});
lucide.createIcons({ nodes: [scrollBtn] });

function fillEx(btn) {
  const clone = btn.cloneNode(true);
  clone.querySelectorAll('.chip-icon, i, svg, .demo-badge').forEach(el => el.remove());
  userInput.value = clone.textContent.trim();
  userInput.focus();
}

function runDemo(btn) {
  const query = btn.dataset.query || btn.textContent.trim();
  userInput.value = query;
  sendMessage();
}

async function sendMessage() {
  const msg = userInput.value.trim();
  if (!msg || loading) return;

  if (currentFollowupId) { removeEl(currentFollowupId); currentFollowupId = null; }

  if (isFirstMsg) {
    document.getElementById('welcomeState')?.remove();
    isFirstMsg = false;
  }

  // E4 — Auto TTS demo mode
  if (msg.toLowerCase().includes('demo')) {
    _ttsEnabled = true;
    _syncTTSGlobalBtn();
  }

  _queryStartTime = Date.now();
  _queryCount++;
  const qChip = document.getElementById('queryCounterChip');
  const qNum  = document.getElementById('queryNum');
  if (qChip && qNum) { qNum.textContent = String(_queryCount); qChip.style.display = 'flex'; lucide.createIcons({ nodes: [qChip] }); }

  addUserMsg(msg);
  userInput.value = '';
  userInput.style.height = 'auto';
  setLoading(true);
  startProgress();
  stopSpeaking();
  emergencyBar.classList.remove('show');

  const typId = addTyping();
  let streamCardId = null;

  try {
    const profilePrefix = buildProfilePrefix();
    const zonePrefix = buildZonePrefix();
    const contextPrefix = [profilePrefix, zonePrefix].filter(Boolean).join(' ');
    const fullMsg = contextPrefix ? `${contextPrefix} ${msg}` : msg;
    // Limpiar card de zonas del chat — ya está incluida en el mensaje
    if (zonePrefix) {
      document.getElementById('zoneContextCard')?.remove();
      _selectedZones.clear();
      document.querySelectorAll('.body-zone.selected').forEach(el => el.classList.remove('selected'));
      _renderBodyChips();
      document.getElementById('zoneBtn')?.classList.remove('has-zones');
    }
    const resp = await fetch('/api/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: fullMsg })
    });

    if (!resp.ok) {
      if (handleUnauth(resp.status)) return;
      const err = await resp.json().catch(() => ({}));
      removeEl(typId);
      addError(err.error || 'Error al procesar la consulta.');
      return;
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const chunks = buffer.split('\n\n');
      buffer = chunks.pop(); // guarda fragmento incompleto

      for (const chunk of chunks) {
        if (!chunk.startsWith('data:')) continue;
        let event;
        try { event = JSON.parse(chunk.slice(5).trim()); } catch { continue; }

        if (event.type === 'thought') {
          updateTypingStatus(typId, `🧠 ${event.action || 'pensando'}...`);
        } else if (event.type === 'tool_call') {
          const preview = (event.input || '').substring(0, 35);
          updateTypingStatus(typId, `⚙️ ${event.tool}(${preview})`);
        } else if (event.type === 'observation') {
          updateTypingStatus(typId, `📊 obs: ${event.tool || ''}`);
        } else if (event.type === 'final_start') {
          removeEl(typId);
          streamCardId = addStreamCard();
        } else if (event.type === 'token') {
          appendToken(streamCardId, event.content);
        } else if (event.type === 'done') {
          if (streamCardId) removeEl(streamCardId);
          else removeEl(typId);
          const cardData = { ...event, query: msg };
          // Iniciar fetch TTS ANTES de renderizar la card para ganar ~300ms
          let ttsFetchPromise = null;
          if (_ttsEnabled) {
            const ttsText = _buildDoctorScript(cardData);
            if (ttsText) {
              ttsFetchPromise = fetch('/api/tts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: ttsText, voice: 'es-ES-AlvaroNeural' })
              });
            }
          }
          addAICard(cardData);
          if (event.gravedad === 'emergencia') emergencyBar.classList.add('show');
          if (ttsFetchPromise) {
            stopSpeaking();
            const lastTtsBtn = [...document.querySelectorAll('.tts-card-btn')].at(-1);
            _playFromFetch(ttsFetchPromise, lastTtsBtn || null);
          }
        } else if (event.type === 'error') {
          removeEl(typId);
          if (streamCardId) removeEl(streamCardId);
          addError(event.message || 'Error desconocido.');
        }
      }
    }
  } catch (e) {
    removeEl(typId);
    if (streamCardId) removeEl(streamCardId);
    addError('Error de conexión. Intenta de nuevo.');
  } finally {
    setLoading(false);
    finishProgress();
  }
}

function addUserMsg(text) {
  const d = document.createElement('div');
  d.className = 'msg user';
  d.innerHTML = `<div class="av user-av"><i data-lucide="user" style="width:16px;height:16px;stroke-width:2;color:var(--blue)"></i></div><div class="user-bubble">${esc(text)}</div>`;
  chatZone.appendChild(d);
  lucide.createIcons();
  scrollDown();
}

function addTyping() {
  const id = 'typ_' + Date.now();
  const d = document.createElement('div');
  d.id = id;
  d.className = 'typing-row';
  d.innerHTML = `
    <div class="av ai-av"><i data-lucide="bot" style="width:16px;height:16px;stroke-width:2;color:var(--emerald)"></i></div>
    <div class="typing-card">
      <div class="td"></div><div class="td"></div><div class="td"></div>
      <span id="${id}_status" style="font-size:11.5px;color:var(--text-3);margin-left:8px;font-family:'JetBrains Mono',monospace;">Analizando síntomas...</span>
    </div>`;
  chatZone.appendChild(d);
  lucide.createIcons();
  scrollDown();
  return id;
}

function updateTypingStatus(id, text) {
  const el = document.getElementById(id + '_status');
  if (el) el.textContent = text;
}

function addStreamCard() {
  const id = 'stream_' + Date.now();
  const d = document.createElement('div');
  d.id = id;
  d.className = 'msg';
  d.innerHTML = `
    <div class="av ai-av"><i data-lucide="bot" style="width:16px;height:16px;stroke-width:2;color:var(--emerald)"></i></div>
    <div class="ai-card">
      <div class="card-body" id="${id}_body" style="min-height:48px;white-space:pre-wrap;"></div>
    </div>`;
  chatZone.appendChild(d);
  lucide.createIcons();
  const body = document.getElementById(id + '_body');
  const cur = document.createElement('span');
  cur.className = 'typing-cursor';
  cur.id = id + '_cursor';
  body.appendChild(cur);
  scrollDown();
  return id;
}

function appendToken(id, token) {
  const body = document.getElementById(id + '_body');
  if (!body) return;
  const cur = document.getElementById(id + '_cursor');
  body.insertBefore(document.createTextNode(token), cur || null);
  if (chatZone.scrollHeight - chatZone.scrollTop - chatZone.clientHeight < 120) {
    chatZone.scrollTop = chatZone.scrollHeight;
  }
}

function addAICard(data) {
  const sev   = data.gravedad || 'moderada';
  const SEV_ICONS = { leve:'check-circle', moderada:'alert-circle', grave:'alert-triangle', emergencia:'alert-octagon' };
  const conf  = Math.max(5, Math.min(100, data.confianza || 0));
  const traj  = data.trajectory || [];
  const tools = data.tools_used || [];
  const srcs  = data.fuentes || [];
  const iters = data.iteraciones || 0;
  const ts             = Date.now();
  const exportBtnId    = 'expbtn_'      + ts;
  const copyBtnId      = 'copybtn_'     + ts;
  const ttsBtnId       = 'ttsbtn_'      + ts;
  const detailsBtnId   = 'detbtn_'      + ts;
  const panelId        = 'detpanel_'    + ts;
  const pipelineBtnId  = 'pipebtn_'     + ts;
  const pipelinePanelId = 'pipepanel_'  + ts;
  const feedbackId     = 'fb_'          + ts;

  // ── Contenido del panel de detalles ─────────────────────────────────────
  const toolsSec = tools.length
    ? `<div class="details-section">
        <div class="details-label">Herramientas utilizadas</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          ${tools.map(t => `<span class="tool-badge">⚙ ${esc(t)}</span>`).join('')}
        </div>
       </div>`
    : '';

  const srcsSec = srcs.length
    ? `<div class="details-section">
        <div class="details-label">Fuentes bibliográficas</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          ${srcs.map(f => {
            const bc = getBookColor(f);
            const label = f.split(' ').slice(0,3).join(' ');
            return `<span class="src-chip" style="background:${bc.bg};color:${bc.color};border-color:${bc.border};">${esc(label)}</span>`;
          }).join('')}
        </div>
       </div>`
    : '';

  const modeSec = `<div class="details-section">
    <div class="details-label">Motor de IA</div>
    <span style="font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--text-2);">
      ⚙ ${esc(data.modo || '')}${iters ? ` · ${iters} paso${iters !== 1 ? 's' : ''}` : ''}
    </span>
  </div>`;

  const steps = traj.filter(s => s.type !== 'final');
  const stepsHtml = steps.map(s => {
    if (s.type === 'thought') return `
      <div class="traj-step traj-thought">
        <span class="mini-badge">${esc(s.action || 'think')}</span><br>
        ${esc((s.content || '').substring(0, 200))}
      </div>`;
    if (s.type === 'observation') return `
      <div class="traj-step traj-obs">
        <span class="mini-badge">obs: ${esc(s.tool || '')}</span><br>
        ${esc((s.content || '').substring(0, 200))}
      </div>`;
    return '';
  }).join('');
  const trajSec = stepsHtml
    ? `<div class="details-section">
        <div class="details-label">Razonamiento del agente</div>
        <div style="display:flex;flex-direction:column;gap:5px;">${stepsHtml}</div>
       </div>`
    : '';

  // ── Trazabilidad RAG ──────────────────────────────────────────────────────
  const chunks = data.rag_chunks || [];
  const chunksSec = chunks.length ? `
    <div class="details-section">
      <div class="details-label">Trazabilidad RAG — ${chunks.length} fragmento${chunks.length !== 1 ? 's' : ''} recuperado${chunks.length !== 1 ? 's' : ''}</div>
      <div class="rag-list">
        ${chunks.map(c => {
          const faissW = Math.round(Math.min(100, (c.faiss_score || 0) * 100));
          const rrClass = (c.rerank_score || 0) >= 0 ? 'pos' : 'neg';
          const bookShort = (c.book || '').split(' ').slice(0, 3).join(' ');
          return `<div class="rag-chunk">
            <div class="rag-chunk-hdr">
              <span class="rag-rank">#${c.rank}</span>
              <span class="rag-book" style="color:${getBookColor(c.book||'').color}">${esc(bookShort)}</span>
              <span class="rag-page">p.${c.page}</span>
              <div class="rag-scores">
                <span class="rag-slabel">FAISS</span>
                <div class="rag-bar"><div class="rag-fill" style="width:${faissW}%"></div></div>
                <span class="rag-snum">${(c.faiss_score||0).toFixed(3)}</span>
                <span class="rag-slabel" style="margin-left:5px">Rerank</span>
                <span class="rag-rerank ${rrClass}">${(c.rerank_score||0).toFixed(2)}</span>
              </div>
            </div>
            <div class="rag-chunk-txt">${esc(c.text_preview || '')}…</div>
          </div>`;
        }).join('')}
      </div>
    </div>` : '';

  const hasDetails = toolsSec || srcsSec || trajSec || chunksSec;

  const d = document.createElement('div');
  d.className = 'msg';
  d.innerHTML = `
    <div class="av ai-av"><i data-lucide="bot" style="width:16px;height:16px;stroke-width:2;color:var(--emerald)"></i></div>
    <div class="ai-card${sev === 'emergencia' ? ' card-emergency' : ''}">

      <div class="card-header">
        <span class="sev-pill ${sev}"><i data-lucide="${SEV_ICONS[sev]||'activity'}" style="width:11px;height:11px;stroke-width:2.5;flex-shrink:0;pointer-events:none"></i>${esc(data.gravedad_label)}</span>
        <span class="card-condition">${esc(data.condicion_principal)}</span>
        <div class="confidence">
          <div class="conf-bar"><div class="conf-fill" style="width:${conf}%"></div></div>
          <span class="conf-num">${data.confianza}%</span>
        </div>
      </div>

      <div class="card-body">${fmt(cleanResponse(data.respuesta))}</div>

      <div class="rec-box">
        <div class="rec-icon"><i data-lucide="check-circle" style="width:15px;height:15px;color:var(--emerald);stroke-width:2"></i></div>
        <div class="rec-content">
          <div class="rec-label">Recomendación</div>
          <div class="rec-text">${esc(data.recomendacion)}</div>
        </div>
      </div>

      <div class="card-foot">
        <button class="export-btn" id="${exportBtnId}"><i data-lucide="download" style="width:12px;height:12px"></i> PDF</button>
        <button class="copy-btn" id="${copyBtnId}"><i data-lucide="copy" style="width:12px;height:12px"></i> Copiar</button>
        ${_queryStartTime ? `<span class="resp-time"><i data-lucide="zap" style="width:10px;height:10px;stroke-width:2.5"></i>${((Date.now()-_queryStartTime)/1000).toFixed(1)}s</span>` : ''}
        <button class="tts-card-btn" id="${ttsBtnId}" title="Escuchar respuesta"><i data-lucide="volume-2" style="width:12px;height:12px"></i> Escuchar</button>
        ${chunks.length ? `<button class="pipeline-btn" id="${pipelineBtnId}"><i data-lucide="git-branch" style="width:12px;height:12px"></i> Ver pipeline <span class="arrow">▼</span></button>` : ''}
        ${hasDetails
          ? `<button class="details-btn" id="${detailsBtnId}"><i data-lucide="sliders-horizontal" style="width:12px;height:12px"></i> Detalles del análisis <span class="arrow">▼</span></button>`
          : ''}
        <div class="feedback-group" id="${feedbackId}">
          <button class="feedback-btn" id="${feedbackId}_up" title="Útil"><i data-lucide="thumbs-up" style="width:13px;height:13px;stroke-width:2"></i></button>
          <button class="feedback-btn" id="${feedbackId}_dn" title="No útil"><i data-lucide="thumbs-down" style="width:13px;height:13px;stroke-width:2"></i></button>
        </div>
      </div>

      ${hasDetails
        ? `<div class="details-panel" id="${panelId}">
            ${chunksSec}${toolsSec}${srcsSec}${modeSec}${trajSec}
           </div>`
        : ''}

      ${chunks.length
        ? `<div class="pipeline-panel" id="${pipelinePanelId}">
            ${buildRagPipelineHtml(chunks, pipelinePanelId)}
           </div>`
        : ''}

      <div class="card-disclaimer">MEDI-IA no reemplaza la consulta médica profesional. En emergencias llame al 123.</div>
    </div>`;

  chatZone.appendChild(d);
  lucide.createIcons();
  document.getElementById(exportBtnId)?.addEventListener('click', function() { exportPDF(data, this); });
  document.getElementById(copyBtnId)?.addEventListener('click', function() { copyResponse(data, this); });
  const ttsBtn = document.getElementById(ttsBtnId);
  if (ttsBtn) {
    if (!_ttsAvailable) {
      ttsBtn.style.display = 'none';
    } else {
      ttsBtn.addEventListener('click', () => toggleCardTTS(data, ttsBtnId));
    }
  }
  document.getElementById(pipelineBtnId)?.addEventListener('click', function() { toggleRagPipeline(pipelinePanelId, this); });
  document.getElementById(detailsBtnId)?.addEventListener('click', function() { toggleDetails(panelId, this); });
  document.getElementById(feedbackId + '_up')?.addEventListener('click', () => sendFeedback(feedbackId, data.condicion_principal, 1));
  document.getElementById(feedbackId + '_dn')?.addEventListener('click', () => sendFeedback(feedbackId, data.condicion_principal, -1));
  saveToHistory(data.query, data);
  addFollowupChips(data);
  scrollDown();
}

async function exportPDF(data, btn) {
  if (btn) { btn.disabled = true; btn.innerHTML = 'Generando...'; }
  try {
    const resp = await fetch('/api/export/pdf', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      showToast('Error al generar PDF: ' + (err.error || 'intenta de nuevo'));
      return;
    }
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `medi-ia-reporte-${Date.now()}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('PDF descargado', 'success');
  } catch {
    showToast('Error de conexión al generar PDF.');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<i data-lucide="download" style="width:12px;height:12px"></i> PDF`;
      lucide.createIcons({ nodes: [btn] });
    }
  }
}

function addError(msg) {
  const d = document.createElement('div');
  d.className = 'msg';
  d.innerHTML = `<div class="av ai-av"><i data-lucide="bot" style="width:16px;height:16px;stroke-width:2;color:var(--emerald)"></i></div><div class="error-card"><i data-lucide="alert-circle" style="width:15px;height:15px;flex-shrink:0"></i> ${esc(msg)}</div>`;
  chatZone.appendChild(d);
  lucide.createIcons();
  scrollDown();
}

function toggleDetails(panelId, btn) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const isOpen = panel.classList.toggle('open');
  btn.classList.toggle('open', isOpen);
}

function resetSession() {
  fetch('/api/reset', { method: 'POST' }).catch(() => {});
  chatZone.innerHTML = '';
  isFirstMsg = true;
  currentFollowupId = null;
  emergencyBar.classList.remove('show');
  const w = document.createElement('div');
  w.id = 'welcomeState';
  w.className = 'welcome';
  w.innerHTML = `
    <div class="welcome-logo"><i data-lucide="stethoscope" style="width:38px;height:38px;stroke-width:1.25;color:var(--emerald)"></i></div>
    <h2>Nueva consulta</h2>
    <p>Sesión reiniciada. Describe tus síntomas para comenzar.</p>
    <div class="chips-grid">
      <div class="chips-section-label">Casos reales del benchmark — click para ejecutar</div>
      <button class="ex-chip demo-chip" data-query="dolor en el pecho que se irradia al brazo izquierdo con sudoracion fria y nauseas" onclick="runDemo(this)">
        <div class="demo-chip-top"><i data-lucide="heart" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Dolor torácico al brazo</div>
        <span class="demo-badge emergencia">emergencia</span>
      </button>
      <button class="ex-chip demo-chip" data-query="fiebre alta con rigidez de nuca y fotofobia en adulto joven" onclick="runDemo(this)">
        <div class="demo-chip-top"><i data-lucide="brain" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Fiebre + rigidez de nuca</div>
        <span class="demo-badge emergencia">emergencia</span>
      </button>
      <button class="ex-chip demo-chip" data-query="dolor abdominal en fosa iliaca derecha con fiebre nauseas y vomito de 12 horas de evolucion" onclick="runDemo(this)">
        <div class="demo-chip-top"><i data-lucide="activity" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Abdomen agudo FID 12h</div>
        <span class="demo-badge grave">grave</span>
      </button>
      <button class="ex-chip demo-chip" data-query="artralgia poliarticular con exantema malar en alas de mariposa fiebre y alopecia en mujer joven" onclick="runDemo(this)">
        <div class="demo-chip-top"><i data-lucide="scan" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Exantema malar + artralgia</div>
        <span class="demo-badge moderada">moderada</span>
      </button>
      <button class="ex-chip demo-chip" data-query="antibiotico de eleccion para neumonia adquirida en la comunidad en paciente ambulatorio" onclick="runDemo(this)">
        <div class="demo-chip-top"><i data-lucide="pill" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Antibiótico para NAC</div>
        <span class="demo-badge farmacologia">farmacología</span>
      </button>
      <button class="ex-chip demo-chip" data-query="cual es la fisiopatologia de la insuficiencia cardiaca y el papel del sistema renina angiotensina" onclick="runDemo(this)">
        <div class="demo-chip-top"><i data-lucide="book-open" style="width:14px;height:14px;stroke-width:2;flex-shrink:0"></i> Fisiopatología ICC + RAAS</div>
        <span class="demo-badge leve">fisiopatología</span>
      </button>
    </div>`;
  lucide.createIcons();
  chatZone.appendChild(w);
  showToast('Sesión reiniciada', 'success');
}

function removeEl(id) { document.getElementById(id)?.remove(); }
function setLoading(s) { loading = s; sendBtn.disabled = s; }
function scrollDown() { setTimeout(() => chatZone.scrollTop = chatZone.scrollHeight, 50); }

async function doLogout() {
  await fetch('/auth/logout', { method: 'POST' }).catch(() => {});
  window.location.href = '/login';
}

function handleUnauth(status) {
  if (status === 401) { window.location.href = '/login'; return true; }
  return false;
}

function esc(str) {
  if (str == null) return '';
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(String(str)));
  return d.innerHTML;
}

function cleanResponse(text) {
  if (!text) return '';
  const skip = [
    'condicion principal sugerida',
    'condición principal sugerida',
    'nivel de urgencia',
    'recomendacion',
    'recomendación',
    'esto no reemplaza',
    'este reporte no reemplaza',
    'sintomas clave que coinciden',
    'síntomas clave que coinciden',
  ];
  // Detecta líneas con mayoría de caracteres CJK (chino/japonés/coreano)
  const isCJK = line => {
    const cjk = (line.match(/[　-鿿가-힯豈-﫿]/g) || []).length;
    return cjk > 4 || (line.length > 0 && cjk / line.length > 0.3);
  };
  return text
    .split('\n')
    .filter(line => {
      const l = line.trim().toLowerCase();
      return l.length > 0 && !skip.some(p => l.startsWith(p)) && !isCJK(line);
    })
    .join('\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

function fmt(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .split('\n\n').map(p => `<p>${p.replace(/\n/g,'<br>')}</p>`).join('');
}

// ── Follow-up chips contextuales ─────────────────────────────────────────────
function _followupQuestions(data) {
  const c = data.condicion_principal || 'esta condición';
  const sev = data.gravedad || 'moderada';
  const base = [
    `¿Cuál es el tratamiento de primera línea para ${c}?`,
    `¿Qué exámenes diagnósticos se solicitan en ${c}?`,
  ];
  const byGravedad = {
    leve:       `¿Puedo manejar ${c} en casa o necesito consulta?`,
    moderada:   `¿Cuáles son las complicaciones posibles de ${c}?`,
    grave:      `¿Cuáles son los criterios de hospitalización para ${c}?`,
    emergencia: `¿Qué hacer mientras llega ayuda médica en ${c}?`,
  };
  return [...base, byGravedad[sev] || byGravedad.moderada];
}

function addFollowupChips(data) {
  if (currentFollowupId) removeEl(currentFollowupId);
  const picks = _followupQuestions(data);
  const id = 'followup_' + Date.now();
  const d = document.createElement('div');
  d.id = id;
  d.className = 'followup-row';
  d.innerHTML = picks.map(q =>
    `<button class="followup-chip" data-query="${esc(q)}">${esc(q)}</button>`
  ).join('');
  chatZone.appendChild(d);
  d.querySelectorAll('.followup-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const b = btn as HTMLElement;
      userInput.value = b.dataset.query || b.textContent || '';
      sendMessage();
    });
  });
  currentFollowupId = id;
  scrollDown();
}

// ── Sidebar móvil ─────────────────────────────────────────────────────────────
function toggleSidebar() {
  const sidebar  = document.querySelector('.sidebar');
  const backdrop = document.getElementById('sidebarBackdrop');
  const isOpen   = sidebar.classList.toggle('open');
  backdrop.classList.toggle('show', isOpen);
}

function closeSidebar() {
  document.querySelector('.sidebar').classList.remove('open');
  document.getElementById('sidebarBackdrop').classList.remove('show');
}

// ── Exportar sesión completa como PDF ─────────────────────────────────────────
async function exportConversation(btn) {
  if (btn) { btn.disabled = true; btn.innerHTML = '<i data-lucide="loader-2" style="width:13px;height:13px"></i> Generando...'; lucide.createIcons({ nodes: [btn] }); }
  try {
    const r = await fetch('/api/export/conversation');
    if (!r.ok) {
      const err = await r.json().catch(() => ({}));
      showToast(err.error || 'Error al generar PDF', 'error');
      return;
    }
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'medi-ia-sesion.pdf';
    a.click();
    URL.revokeObjectURL(url);
    showToast('PDF de sesión descargado', 'success');
  } catch {
    showToast('No se pudo exportar la sesión', 'error');
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = '<i data-lucide="file-text" style="width:13px;height:13px"></i> Exportar sesión';
      lucide.createIcons({ nodes: [btn] });
    }
  }
}

// ── Feedback 👍👎 ─────────────────────────────────────────────────────────────
async function sendFeedback(groupId, condicion, rating) {
  const group = document.getElementById(groupId);
  if (!group || group.dataset.voted) return;
  try {
    const r = await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating, condicion }),
    });
    if (!r.ok) throw new Error();
    group.dataset.voted = '1';
    const upBtn = document.getElementById(groupId + '_up') as HTMLButtonElement | null;
    const dnBtn = document.getElementById(groupId + '_dn') as HTMLButtonElement | null;
    if (upBtn) { upBtn.disabled = true; if (rating === 1)  upBtn.classList.add('positive'); }
    if (dnBtn) { dnBtn.disabled = true; if (rating === -1) dnBtn.classList.add('negative'); }
    showToast(rating === 1 ? '¡Gracias por tu valoración!' : 'Gracias, usaremos esto para mejorar.', 'success');
  } catch {
    showToast('No se pudo registrar la valoración.');
  }
}

// ── Copiar respuesta ─────────────────────────────────────────────────────────
function copyResponse(data, btn) {
  const lines = [
    'DIAGNÓSTICO DIFERENCIAL — MEDI-IA',
    '',
    `Condición principal: ${data.condicion_principal}`,
    `Gravedad: ${data.gravedad_label}`,
    `Confianza: ${data.confianza}%`,
    '',
    cleanResponse(data.respuesta),
    '',
    `Recomendación: ${data.recomendacion}`,
  ];
  if (data.fuentes?.length) lines.push('', `Fuentes: ${data.fuentes.join(', ')}`);

  navigator.clipboard.writeText(lines.join('\n')).then(() => {
    showToast('Copiado al portapapeles', 'success');
    if (btn) {
      btn.innerHTML = `<i data-lucide="check" style="width:12px;height:12px"></i> Copiado`;
      lucide.createIcons({ nodes: [btn] });
      setTimeout(() => {
        btn.innerHTML = `<i data-lucide="copy" style="width:12px;height:12px"></i> Copiar`;
        lucide.createIcons({ nodes: [btn] });
      }, 2000);
    }
  }).catch(() => showToast('No se pudo copiar al portapapeles.', 'error'));
}

// ── Historial de consultas (localStorage) ────────────────────────────────────
const HISTORY_KEY = 'medi-history';
const MAX_HISTORY = 15;

function saveToHistory(query, data) {
  if (!query) return;
  const compact = {
    id: Date.now(), ts: Date.now(),
    query,
    condition:      data.condicion_principal || '',
    respuesta:      data.respuesta            || '',
    recomendacion:  data.recomendacion        || '',
    gravedad:       data.gravedad             || 'moderada',
    gravedad_label: data.gravedad_label       || '',
    confianza:      data.confianza            || 0,
    modo:           data.modo                || '',
  };
  const hist = getHistory();
  hist.unshift(compact);
  if (hist.length > MAX_HISTORY) hist.length = MAX_HISTORY;
  localStorage.setItem(HISTORY_KEY, JSON.stringify(hist));
  renderHistory();
}

function getHistory() {
  try { return JSON.parse(localStorage.getItem(HISTORY_KEY) || '[]'); } catch { return []; }
}

function clearHistory() {
  localStorage.removeItem(HISTORY_KEY);
  renderHistory();
}

function deleteHistoryItem(id) {
  const hist = getHistory().filter(h => h.id !== id);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(hist));
  renderHistory();
}

function renderHistory() {
  const hist = getHistory();
  const sec  = document.getElementById('historySec');
  const list = document.getElementById('historyList');
  if (!sec || !list) return;
  if (!hist.length) { sec.style.display = 'none'; return; }
  sec.style.display = '';
  list.innerHTML = hist.map(h => `
    <div class="hist-item-wrap">
      <button class="hist-item" data-hid="${h.id}">
        <i data-lucide="clock" style="width:11px;height:11px;opacity:0.45;flex-shrink:0;margin-top:3px"></i>
        <div class="hist-meta">
          <span class="hist-query">${esc(h.query.substring(0, 42))}</span>
          ${h.condition ? `<span class="hist-condition">${esc(h.condition.substring(0, 32))}</span>` : ''}
        </div>
      </button>
      <button class="hist-del" onclick="deleteHistoryItem(${h.id})" title="Eliminar">×</button>
    </div>`).join('');
  lucide.createIcons({ nodes: [list] });
  list.querySelectorAll('.hist-item').forEach(btn => {
    btn.addEventListener('click', () => fillHistory(Number((btn as HTMLElement).dataset.hid)));
  });
}

function fillHistory(id) {
  const entry = getHistory().find(h => h.id === id);
  if (!entry) return;
  if (isFirstMsg) {
    document.getElementById('welcomeState')?.remove();
    isFirstMsg = false;
  }
  addUserMsg(entry.query);
  addAICard(entry);
  closeSidebar();
  scrollDown();
}

// ── Input de voz ─────────────────────────────────────────────────────────────
const PLACEHOLDER_DEFAULT = 'Describe tus síntomas... (ej: tengo fiebre, escalofríos y dolor de garganta)';
let recognition = null;
let isListening  = false;

function showToast(msg, type = 'error') {
  const t = document.createElement('div');
  const bg = type === 'error' ? 'var(--red)' : 'var(--emerald)';
  t.style.cssText = `position:fixed;bottom:24px;left:50%;transform:translateX(-50%) translateY(0);
    padding:11px 20px;border-radius:10px;font-size:13px;font-family:'Inter',sans-serif;
    z-index:9999;background:${bg};color:#fff;box-shadow:var(--shadow-lg);
    white-space:nowrap;animation:slideIn 0.25s ease;`;
  t.textContent = msg;
  document.body.appendChild(t);
  setTimeout(() => t.style.opacity = '0', 3000);
  setTimeout(() => t.remove(), 3400);
}

function initVoice() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    const btn = document.getElementById('micBtn');
    if (btn) btn.style.display = 'none';
    return;
  }

  recognition = new SR();
  recognition.lang           = 'es-ES';
  recognition.continuous     = false;
  recognition.interimResults = true;

  recognition.onstart = () => {
    isListening = true;
    _setMicState(true);
    userInput.placeholder = 'Escuchando... habla ahora';
  };

  recognition.onresult = (e) => {
    let interim = '', final = '';
    for (let i = e.resultIndex; i < e.results.length; i++) {
      const t = e.results[i][0].transcript;
      if (e.results[i].isFinal) final += t;
      else interim += t;
    }
    userInput.value = final || interim;
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 120) + 'px';
  };

  recognition.onend = () => _stopListening();

  recognition.onerror = (e) => {
    const msgs = {
      'not-allowed': 'Permiso de micrófono denegado. Actívalo en Configuración del navegador.',
      'network':     'El reconocimiento de voz requiere conexión a internet.',
      'no-speech':   'No se detectó voz. Intenta de nuevo.',
    };
    if (msgs[e.error]) showToast(msgs[e.error]);
    _stopListening();
  };
}

function toggleVoice() {
  if (!recognition) { showToast('Tu navegador no soporta entrada de voz.'); return; }
  if (isListening) {
    recognition.stop();
  } else {
    userInput.value = '';
    userInput.style.height = 'auto';
    try {
      recognition.start();
    } catch (e) {
      // Puede lanzar si ya hay una sesion activa — recrear y reintentar
      const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognition = new SR();
      initVoice();
      try { recognition.start(); } catch (_) { showToast('No se pudo iniciar el micrófono.'); }
    }
  }
}

function _stopListening() {
  isListening = false;
  _setMicState(false);
  userInput.placeholder = PLACEHOLDER_DEFAULT;
}

function _setMicState(active) {
  const btn = document.getElementById('micBtn');
  if (!btn) return;
  btn.classList.toggle('listening', active);
  // Reemplazar innerHTML con un <i> fresco para que lucide lo procese correctamente
  btn.innerHTML = `<i data-lucide="${active ? 'mic-off' : 'mic'}" style="width:17px;height:17px;stroke-width:2;pointer-events:none"></i>`;
  lucide.createIcons({ nodes: [btn] });
}

// ── Tema oscuro ──────────────────────────────────────────────────────────────
function toggleTheme() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const next = isDark ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('medi-theme', next);
  _syncThemeIcon(next);
}

function _syncThemeIcon(theme) {
  const icon = document.getElementById('themeIcon');
  if (!icon) return;
  icon.setAttribute('data-lucide', theme === 'dark' ? 'sun' : 'moon');
  lucide.createIcons({ nodes: [icon] });
}

// Aplica el tema guardado antes de pintar el DOM visible
(function initTheme() {
  const saved = localStorage.getItem('medi-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();

// Carga estado real del servidor al iniciar
async function loadHealthStatus() {
  try {
    const r = await fetch('/api/health');
    if (!r.ok) throw new Error();
    const h = await r.json();

    const degraded = h.status === 'degraded' || !h.indice_ok;

    // Dot color
    const dot = document.getElementById('sidebarDot');
    if (dot) dot.style.background = degraded ? 'var(--amber)' : 'var(--emerald)';

    // Estado
    const estado = document.getElementById('sidebarEstado');
    if (estado) estado.innerHTML = `<span class="dot" id="sidebarDot" style="background:${degraded ? 'var(--amber)' : 'var(--emerald)'}"></span> ${degraded ? 'Degradado' : 'Activo'}`;

    // Índice
    const indice = document.getElementById('sidebarIndice');
    if (indice) indice.textContent = degraded
      ? 'Sin índice'
      : h.chunks_indexados.toLocaleString('es') + ' doc.';

    // Modo
    const modo = document.getElementById('sidebarModo');
    if (modo) modo.textContent = h.hf_activo ? 'ReAct' : 'RAG';

    // Motor
    const motor = document.getElementById('sidebarMotor');
    if (motor) motor.textContent = h.hf_activo ? 'Qwen 2.5-7B' : 'RAG Template';

    // Topbar chip
    const topbarLibros = document.getElementById('topbarLibros');
    if (topbarLibros && h.libros?.length) topbarLibros.textContent = h.libros.length;

    // Aviso visible si index falta
    if (degraded) {
      const warn = document.createElement('div');
      warn.style.cssText = 'margin:0 14px 10px;padding:9px 12px;background:var(--amber-light);border:1px solid var(--amber);border-radius:8px;font-size:11px;color:#92400e;line-height:1.4;';
      warn.innerHTML = '⚠️ Índice FAISS no encontrado.<br>Ejecuta <code style="background:rgba(0,0,0,.08);padding:1px 4px;border-radius:3px">make ingest</code> para activar el análisis médico.';
      document.querySelector('.sidebar-footer')?.before(warn);
    }

    const badgeText = document.getElementById('welcomeBadgeText');
    if (badgeText) {
      const chunks = h.chunks_indexados ? h.chunks_indexados.toLocaleString() + ' chunks' : '136K chunks';
      const libros = h.libros?.length ? h.libros.length + ' libros' : '14 libros';
      const modo   = h.hf_activo ? 'ReAct' : 'RAG';
      badgeText.textContent = `${chunks} · e5-base · BM25+RRF · ${libros} · ${modo}`;
    }
  } catch {
    // Si el server no responde, dejamos los valores por defecto
    document.getElementById('sidebarIndice').textContent = '—';
  }
}

// ===== TTS (edge-tts neural via /api/tts) =====
let _ttsEnabled = localStorage.getItem('medi-tts-enabled') === 'true';
let _currentAudio = null;
const _ttsAvailable = true;

function initTTS() { _syncTTSGlobalBtn(); }

function _syncTTSGlobalBtn() {
  const btn = document.getElementById('ttsGlobalBtn');
  if (!btn) return;
  btn.classList.toggle('active', _ttsEnabled);
  const icon = btn.querySelector('i');
  if (icon) { icon.setAttribute('data-lucide', _ttsEnabled ? 'volume-2' : 'volume-x'); lucide.createIcons({ nodes: [icon] }); }
}

function toggleTTSGlobal() {
  _ttsEnabled = !_ttsEnabled;
  localStorage.setItem('medi-tts-enabled', String(_ttsEnabled));
  _syncTTSGlobalBtn();
  if (!_ttsEnabled) stopSpeaking();
}

function stopSpeaking() {
  if (_currentAudio) { _currentAudio.pause(); _currentAudio.src = ''; _currentAudio = null; }
  document.querySelectorAll('.tts-card-btn.speaking').forEach(btn => {
    btn.classList.remove('speaking');
    const icon = btn.querySelector('i');
    if (icon) { icon.setAttribute('data-lucide', 'volume-2'); lucide.createIcons({ nodes: [icon] }); }
  });
}

function _setBtnSpeaking(btn, speaking) {
  if (!btn) return;
  btn.classList.toggle('speaking', speaking);
  const icon = btn.querySelector('i');
  if (icon) { icon.setAttribute('data-lucide', speaking ? 'volume-x' : 'volume-2'); lucide.createIcons({ nodes: [icon] }); }
}

function _buildDoctorScript(data) {
  const condition = (data.condicion_principal || '').trim();
  const conf      = data.confianza || 0;
  const gravedad  = data.gravedad  || 'moderada';
  const rec       = (data.recomendacion || '').replace(/\*\*/g,'').replace(/\*/g,'').trim();

  // Primer párrafo de la respuesta, limpio de markdown
  const rawResp = (data.respuesta || '').replace(/\*\*/g,'').replace(/\*/g,'').replace(/#+\s*/g,'');
  const firstPara = rawResp.split(/\n{2,}/)[0]?.trim() || '';
  const explanation = firstPara.length > 350 ? firstPara.substring(0, 350) + '.' : firstPara;

  const sevLine = {
    leve:       'Parece ser una situación leve, pero observa cómo evolucionan los síntomas.',
    moderada:   'Te recomiendo consultar con tu médico en los próximos días para confirmar el diagnóstico.',
    grave:      'La situación requiere atención médica pronto. No lo dejes pasar.',
    emergencia: 'Esto puede ser una emergencia. Busca atención médica inmediata o llama al servicio de emergencias.'
  }[gravedad] || '';

  let script = '';
  if (condition) {
    script += `Basándome en los síntomas que describes, lo más probable es que estés presentando ${condition}`;
    if (conf >= 75) script += ', con una probabilidad alta';
    script += '. ';
  }
  if (explanation) script += explanation + ' ';
  if (sevLine)    script += sevLine + ' ';
  if (rec)        script += `En cuanto al tratamiento, ${rec}`;
  return script.trim();
}

// Reproducción con MediaSource (streaming progresivo) o fallback a blob
async function _playFromFetch(fetchPromise, btn) {
  _setBtnSpeaking(btn, true);
  try {
    const resp = await fetchPromise;
    if (!resp.ok) throw new Error('tts');

    if (window.MediaSource && MediaSource.isTypeSupported('audio/mpeg') && resp.body) {
      // Streaming: empieza a sonar en cuanto llegan los primeros chunks
      const ms  = new MediaSource();
      const url = URL.createObjectURL(ms);
      const audio = new Audio(url);
      _currentAudio = audio;

      let sb, pendingChunks = [], done = false;

      const tryAppend = () => {
        if (!sb || sb.updating || pendingChunks.length === 0) return;
        try { sb.appendBuffer(pendingChunks.shift()); } catch {}
      };

      ms.addEventListener('sourceopen', () => {
        sb = ms.addSourceBuffer('audio/mpeg');
        sb.addEventListener('updateend', () => { tryAppend(); if (done && pendingChunks.length === 0) { try { ms.endOfStream(); } catch {} } });
        tryAppend();
        audio.play().catch(() => {});
      });

      const reader = resp.body.getReader();
      (async () => {
        while (true) {
          const { done: d, value } = await reader.read();
          if (d) { done = true; tryAppend(); break; }
          pendingChunks.push(value);
          tryAppend();
        }
      })();

      audio.onended = audio.onerror = () => { URL.revokeObjectURL(url); _currentAudio = null; _setBtnSpeaking(btn, false); };
    } else {
      // Fallback: esperar blob completo
      const blob = await resp.blob();
      const url  = URL.createObjectURL(blob);
      const audio = new Audio(url);
      _currentAudio = audio;
      audio.onended = audio.onerror = () => { URL.revokeObjectURL(url); _currentAudio = null; _setBtnSpeaking(btn, false); };
      await audio.play();
    }
  } catch {
    _setBtnSpeaking(btn, false);
  }
}

async function speakResponse(data, cardBtnId) {
  stopSpeaking();
  const btn  = cardBtnId ? document.getElementById(cardBtnId) : null;
  const text = _buildDoctorScript(data);
  if (!text) return;
  const fetchPromise = fetch('/api/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text, voice: 'es-ES-AlvaroNeural' })
  });
  await _playFromFetch(fetchPromise, btn);
}

async function toggleCardTTS(data, cardBtnId) {
  const btn = document.getElementById(cardBtnId);
  if (btn?.classList.contains('speaking')) { stopSpeaking(); }
  else { await speakResponse(data, cardBtnId); }
}

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
  (document.getElementById('profileNombre') as HTMLInputElement).value = p.nombre || '';
  (document.getElementById('profileEdad') as HTMLInputElement).value = p.edad || '';
  _profileChips.alergias = p.alergias ? [...p.alergias] : [];
  _profileChips.medicamentos = p.medicamentos ? [...p.medicamentos] : [];
  _profileChips.condiciones = p.condiciones ? [...p.condiciones] : [];
  const toggle = document.getElementById('profileEmbarazadaToggle');
  if (toggle) toggle.classList.toggle('on', !!p.embarazada);
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
  const input = document.getElementById(inputId) as HTMLInputElement | null;
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
    nombre: (document.getElementById('profileNombre') as HTMLInputElement).value.trim(),
    edad: parseInt((document.getElementById('profileEdad') as HTMLInputElement).value) || null,
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
  if (sessionStorage.getItem('medi-ia-profile')) return;
  if (!localStorage.getItem('medi-onboarding-done')) return; // espera al onboarding
  setTimeout(openProfileModal, 800);
}

function initProfileModal() {
  _setupChipInput('profileAlergiaInput', 'alergias', 'profileAlergiaChips');
  _setupChipInput('profileMedInput', 'medicamentos', 'profileMedChips');
  _setupChipInput('profileCondInput', 'condiciones', 'profileCondChips');
  document.getElementById('profileOverlay')?.addEventListener('click', e => {
    if ((e.target as HTMLElement).id === 'profileOverlay') closeProfileModal();
  });
}

// ===== PIPELINE RAG VIZ =====
function buildRagPipelineHtml(chunks, panelId) {
  if (!chunks || !chunks.length) return '';
  const RERANK_THRESHOLD = -3.0;
  const reranked = [...chunks].sort((a, b) => (b.rerank_score || 0) - (a.rerank_score || 0));

  const renderChunkCard = (c, phase) => {
    const faissW = Math.round(Math.min(100, (c.faiss_score || 0) * 100));
    const rrScore = c.rerank_score || 0;
    const rrNorm = Math.round(Math.min(100, Math.max(0, ((rrScore + 10) / 20) * 100)));
    const rrClass = rrScore >= 0 ? 'rerank-pos' : 'rerank-neg';
    const bookShort = (c.book || '').split(' ').slice(0, 3).join(' ');
    const isKept = rrScore > RERANK_THRESHOLD;

    if (phase === 'retrieval') {
      return `<div class="pipeline-chunk-card">
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
      return `<div class="pipeline-chunk-card ${isKept ? '' : 'discarded'}">
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
      <div class="pipeline-chunks-grid">${chunks.map(c => renderChunkCard(c, 'retrieval')).join('')}</div>
    </div>
    <div class="pipeline-step" id="${panelId}_s2">
      <div class="pipeline-step-title">
        <span>2. Reranker</span>
        <span class="pipeline-step-badge">Cross-Encoder mMARCO</span>
      </div>
      <div class="pipeline-chunks-grid">${reranked.map(c => renderChunkCard(c, 'rerank')).join('')}</div>
    </div>
    <div class="pipeline-step" id="${panelId}_s3">
      <div class="pipeline-step-title">
        <span>3. Contexto enviado al LLM</span>
        <span class="pipeline-step-badge">${reranked.filter(c => (c.rerank_score||0) > RERANK_THRESHOLD).length} fragmentos</span>
      </div>
      <div class="pipeline-chunks-grid">${reranked.map(c => renderChunkCard(c, 'final')).join('')}</div>
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
    ['_s1', '_s2', '_s3'].forEach((suffix, i) => {
      setTimeout(() => {
        const step = document.getElementById(panelId + suffix);
        if (step) step.classList.add('visible');
        step?.querySelectorAll('.pipeline-bar-fill[data-target]').forEach(bar => {
          const el = bar as HTMLElement;
          setTimeout(() => { el.style.width = el.dataset.target + '%'; }, 50);
        });
      }, i * 220);
    });
  } else {
    ['_s1','_s2','_s3'].forEach(s => {
      const step = document.getElementById(panelId + s);
      if (step) {
        step.classList.remove('visible');
        step.querySelectorAll('.pipeline-bar-fill').forEach(b => { (b as HTMLElement).style.width = '0%'; });
      }
    });
  }
}

// ===== BODY MAP =====
const _selectedZones = new Map();

function openBodyDrawer() {
  document.getElementById('bodyDrawer').classList.add('open');
  document.getElementById('bodyDrawerOverlay').classList.add('show');
  lucide.createIcons({ nodes: [document.getElementById('bodyDrawer')] });
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
  _updateZoneChatCard();
}

function _removeZone(zone) {
  _selectedZones.delete(zone);
  document.querySelector(`[data-zone="${zone}"]`)?.classList.remove('selected');
  _renderBodyChips();
  _updateZoneChatCard();
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

function _updateZoneChatCard() {
  const zoneBtn = document.getElementById('zoneBtn');
  const existing = document.getElementById('zoneContextCard');

  if (_selectedZones.size === 0) {
    existing?.remove();
    zoneBtn?.classList.remove('has-zones');
    return;
  }

  zoneBtn?.classList.add('has-zones');

  const chipsHtml = [..._selectedZones.entries()].map(([zone, label]) =>
    `<span class="zone-chip-tag">${esc(label)}<button onclick="_removeZone('${zone}')" title="Quitar">×</button></span>`
  ).join('');

  let card = existing;
  if (!card) {
    card = document.createElement('div');
    card.id = 'zoneContextCard';
    card.className = 'msg zone-context-msg';
    chatZone.appendChild(card);
  }

  card.innerHTML = `
    <div class="av zone-av"><i data-lucide="map-pin" style="width:14px;height:14px;stroke-width:2;color:#22d3ee"></i></div>
    <div class="zone-context-card">
      <div class="zone-context-hdr">
        <span class="zone-context-title">Zonas marcadas</span>
        <button class="zone-context-clear-all" onclick="clearAllZones()">Limpiar todo</button>
      </div>
      <div class="zone-context-chips">${chipsHtml}</div>
      <div class="zone-context-hint">Se incluirán en tu próxima consulta</div>
    </div>`;

  lucide.createIcons({ nodes: [card] });
  scrollDown();
}

function clearAllZones() {
  _selectedZones.forEach((_, zone) => {
    document.querySelector(`[data-zone="${zone}"]`)?.classList.remove('selected');
  });
  _selectedZones.clear();
  _renderBodyChips();
  _updateZoneChatCard();
}

function buildZonePrefix() {
  if (_selectedZones.size === 0) return '';
  const labels = [..._selectedZones.values()].join(', ');
  return `[Zonas afectadas: ${labels}.]`;
}

lucide.createIcons();
_syncThemeIcon(localStorage.getItem('medi-theme') || 'dark');
initVoice();
initTTS();
initProfileModal();
renderHistory();
loadHealthStatus();
checkProfileOnLoad();

// ── E3 — Onboarding de 3 pasos ────────────────────────────────────────────────
const OB_STEPS = [
  {
    targetId: 'userInput',
    title: 'Describe tus síntomas',
    desc: 'Escribe con detalle lo que sientes. Cuanto más información des, más preciso será el diagnóstico diferencial.',
  },
  {
    targetId: 'zoneBtn',
    title: 'Marca la zona de dolor',
    desc: 'Usa el mapa corporal SVG para indicar exactamente dónde sientes el dolor. El agente lo tendrá en cuenta.',
  },
  {
    targetId: 'ttsGlobalBtn',
    title: 'Modo manos libres',
    desc: 'Activa el TTS neural para que MEDI-IA te lea las respuestas como un médico. Ideal para la consulta.',
  },
];
let _obStep = 0;

function _positionOBTooltip(targetRect) {
  const tip  = document.getElementById('obTooltip');
  const spot = document.getElementById('obSpotlight');
  const pad  = 8;
  spot.style.left   = (targetRect.left   - pad) + 'px';
  spot.style.top    = (targetRect.top    - pad) + 'px';
  spot.style.width  = (targetRect.width  + pad*2) + 'px';
  spot.style.height = (targetRect.height + pad*2) + 'px';

  const tipW = 270, tipH = 175, gap = 20;
  const midY = window.innerHeight / 2;

  // Si el target está en la mitad inferior → tooltip va ARRIBA con más margen
  let ty, tx;
  if (targetRect.top > midY) {
    ty = targetRect.top - tipH - gap;
  } else {
    ty = targetRect.bottom + gap;
  }

  // Centrar horizontalmente sobre el target, con límites de pantalla
  tx = targetRect.left + targetRect.width / 2 - tipW / 2;
  tx = Math.max(12, Math.min(tx, window.innerWidth - tipW - 12));
  ty = Math.max(12, Math.min(ty, window.innerHeight - tipH - 12));

  tip.style.left = tx + 'px';
  tip.style.top  = ty + 'px';
}

function _showOBStep(idx) {
  const step = OB_STEPS[idx];
  const el   = document.getElementById(step.targetId);
  if (!el) { nextOnboardingStep(); return; }
  const rect = el.getBoundingClientRect();
  document.getElementById('obStep').textContent  = `Paso ${idx+1} de ${OB_STEPS.length}`;
  document.getElementById('obTitle').textContent = step.title;
  document.getElementById('obDesc').textContent  = step.desc;
  document.getElementById('obNext').textContent  = idx < OB_STEPS.length-1 ? 'Siguiente →' : 'Empezar';
  const dots = document.getElementById('obDots');
  dots.innerHTML = OB_STEPS.map((_,i) => `<div class="ob-dot${i===idx?' active':''}"></div>`).join('');
  _positionOBTooltip(rect);
}

function nextOnboardingStep() {
  if (_obStep >= OB_STEPS.length - 1) { skipOnboarding(); return; }
  _obStep++;
  _showOBStep(_obStep);
}

function skipOnboarding() {
  const ov = document.getElementById('onboardingOverlay');
  ov.classList.remove('active');
  ov.style.display = 'none';
  localStorage.setItem('medi-onboarding-done', '1');
  checkProfileOnLoad();
}

function initOnboarding() {
  if (localStorage.getItem('medi-onboarding-done')) return;
  const ov = document.getElementById('onboardingOverlay');
  ov.style.display = 'block';
  ov.classList.add('active');
  _obStep = 0;
  _showOBStep(0);
}

setTimeout(initOnboarding, 800);

// ── Exposicion global ──────────────────────────────────────────────────────
// templates/index.html (markup estatico y HTML generado dinamicamente mas
// arriba, ej. las cards del historial) usa atributos onclick="..." que
// resuelven contra el scope global. Al empaquetar este archivo como modulo
// ES para Vite, sus funciones dejan de ser globales por defecto — este
// bridge preserva el comportamiento sin reescribir los ~80 handlers inline.
// Migrar esos handlers a addEventListener + data-attributes (como ya se
// hace en el resto del archivo) es el siguiente paso logico, no este pase.
Object.assign(window as unknown as Record<string, unknown>, {
  toggleSidebar, closeSidebar, resetSession, doLogout,
  runDemo, sendMessage, deleteHistoryItem, clearHistory, exportConversation,
  toggleTheme, toggleVoice, toggleTTSGlobal,
  openProfileModal, closeProfileModal, saveProfile, _removeChip,
  openBodyDrawer, closeBodyDrawer, setBodyView, toggleBodyZone, _removeZone, clearAllZones,
  nextOnboardingStep, skipOnboarding,
});
