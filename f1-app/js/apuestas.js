// apuestas.js - frontend helpers for apuestas.html
// Loads pilotos from the apuestas API and populates the TOP3 selects.
const API_BASE = 'http://127.0.0.1:5500';
let top3Form;
let top3Alert;
let misApuestasList;
let misApuestasEmpty;
let misApuestasAlert;

document.addEventListener('DOMContentLoaded', () => {
  top3Form = document.getElementById('form-top3');
  top3Alert = document.getElementById('top3Alert');
  misApuestasList = document.getElementById('misApuestasList');
  misApuestasEmpty = document.getElementById('misApuestasEmpty');
  misApuestasAlert = document.getElementById('misApuestasAlert');

  loadPilotos();
  loadMisApuestas();
  const tabTop3 = document.getElementById('tab-top3');
  if (tabTop3) tabTop3.addEventListener('shown.bs.tab', loadPilotos);
  const tabMis = document.getElementById('tab-mis');
  if (tabMis) tabMis.addEventListener('shown.bs.tab', loadMisApuestas);

  initCustomSelects();
  preventDuplicates();
  if (top3Form) {
    top3Form.addEventListener('submit', handleTop3Submit);
  }
});

async function loadPilotos() {
  try {
    const res = await fetch(`${API_BASE}/api/pilotos`);
    if (!res.ok) return;
    const data = await res.json();
    if (!data.success) return;
    const pilotos = data.pilotos || [];
    const custom = document.querySelectorAll('.custom-select');
    if (custom && custom.length > 0) {
      custom.forEach(c => {
        const ul = c.querySelector('.options');
        ul.innerHTML = '';
        pilotos.forEach(p => {
          const li = document.createElement('li');
          li.dataset.value = p.id;
          li.textContent = p.name;
          ul.appendChild(li);
        });
      });
      updateCustomDisabled();
      return;
    }
    const selects = ['top1', 'top2', 'top3'].map(id => document.getElementById(id));
    selects.forEach(sel => {
      while (sel.options.length > 1) sel.remove(1);
    });
    pilotos.forEach(p => {
      const option = document.createElement('option');
      option.value = p.id;
      option.textContent = p.name;
      selects.forEach(sel => sel.appendChild(option.cloneNode(true)));
    });
  } catch (err) {
    console.error('Could not load pilotos', err);
  }
}

// Optional: prevent selecting the same pilot twice (native select fallback)
function preventDuplicates(selectIds = ['top1','top2','top3']){
  const sels = selectIds.map(id => document.getElementById(id)).filter(Boolean);
  sels.forEach(s => s.addEventListener('change', () => {
    const values = sels.map(x => x.value).filter(v => v !== '');
    sels.forEach(sx => {
      Array.from(sx.options).forEach(opt => opt.disabled = false);
    });
    sels.forEach(sx => {
      const val = sx.value;
      if (!val) return;
      sels.forEach(other => {
        if (other === sx) return;
        const opt = other.querySelector(`option[value="${val}"]`);
        if (opt) opt.disabled = true;
      });
    });
  }));
}

async function handleTop3Submit(event){
  event.preventDefault();
  hideAlert(top3Alert);
  const userId = localStorage.getItem('user_id');
  if (!userId) {
    showAlert(top3Alert, 'Debes iniciar sesión para guardar una apuesta.', 'warning');
    return;
  }

  const selections = ['top1','top2','top3'].map(id => document.getElementById(id)?.value || '');
  if (selections.some(v => !v)) {
    showAlert(top3Alert, 'Selecciona los tres pilotos antes de confirmar.', 'danger');
    return;
  }

  const submitBtn = top3Form?.querySelector('button[type="submit"]');
  if (submitBtn) submitBtn.disabled = true;

  try {
    const payload = {
      user_id: Number(userId),
      top1: Number(selections[0]),
      top2: Number(selections[1]),
      top3: Number(selections[2]),
    };
    const res = await fetch(`${API_BASE}/apuestas/top3`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (res.ok && data.success && data.bet) {
      showAlert(top3Alert, 'Apuesta guardada correctamente. Redirigiendo al pago...', 'success');
      const betId = data.bet.id;
      localStorage.setItem('pending_bet_id', betId);
      setTimeout(() => {
        window.location.href = `pagos.html?bet_id=${encodeURIComponent(betId)}`;
      }, 800);
    } else {
      showAlert(top3Alert, data.message || 'No se pudo guardar la apuesta.', 'danger');
    }
  } catch (err) {
    console.error('Error saving bet', err);
    showAlert(top3Alert, 'Error de comunicación con el servidor.', 'danger');
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

function resetTop3Selections(){
  ['top1','top2','top3'].forEach(id => {
    const hidden = document.getElementById(id);
    if (!hidden) return;
    hidden.value = '';
    const selected = document.querySelector(`.custom-select[data-id="${id}"] .selected`);
    if (selected) selected.textContent = 'Seleccionar piloto...';
  });
  updateCustomDisabled();
}

async function loadMisApuestas(){
  if (!misApuestasList || !misApuestasEmpty) return;
  const userId = localStorage.getItem('user_id');
  if (!userId) {
    renderMisApuestas([]);
    showAlert(misApuestasAlert, 'Inicia sesión para ver tus apuestas guardadas.', 'info');
    return;
  }
  hideAlert(misApuestasAlert);
  try {
    const res = await fetch(`${API_BASE}/apuestas/top3?user_id=${encodeURIComponent(userId)}`);
    const data = await res.json();
    if (res.ok && data.success) {
      renderMisApuestas(data.apuestas || []);
    } else {
      renderMisApuestas([]);
      showAlert(misApuestasAlert, data.message || 'No se pudieron cargar las apuestas.', 'danger');
    }
  } catch (err) {
    console.error('Could not load bets', err);
    renderMisApuestas([]);
    showAlert(misApuestasAlert, 'Error de comunicación con el servidor.', 'danger');
  }
}

function renderMisApuestas(apuestas){
  if (!misApuestasList || !misApuestasEmpty) return;
  misApuestasList.innerHTML = '';
  if (!apuestas || apuestas.length === 0) {
    misApuestasEmpty.classList.remove('d-none');
    return;
  }
  misApuestasEmpty.classList.add('d-none');
  apuestas.forEach(ap => {
    const li = document.createElement('li');
    li.className = 'list-group-item d-flex flex-column flex-md-row justify-content-between align-items-start gap-2';
    const picks = document.createElement('div');
    const statusBadge = renderStatusBadge(ap.status);
    picks.innerHTML = `<div class="d-flex flex-wrap align-items-center gap-2">
      <span><strong>1º:</strong> ${ap.top1}</span>
      <span><strong>2º:</strong> ${ap.top2}</span>
      <span><strong>3º:</strong> ${ap.top3}</span>
      ${statusBadge}
    </div>`;
    const date = document.createElement('small');
    date.className = 'text-muted';
    date.textContent = formatDate(ap.created_at);
    li.appendChild(picks);
    li.appendChild(date);
    misApuestasList.appendChild(li);
  });
}

function formatDate(value){
  if (!value) return '';
  const normalized = value.replace(' ', 'T');
  const dt = new Date(normalized);
  if (Number.isNaN(dt.getTime())) return value;
  return dt.toLocaleString();
}

function showAlert(el, message, type='danger'){
  if (!el) return;
  const base = el.dataset.baseClass || 'alert';
  el.textContent = message;
  el.className = `${base} alert-${type}`;
  el.style.display = '';
  el.classList.remove('d-none');
}

function hideAlert(el){
  if (!el) return;
  const base = el.dataset.baseClass || 'alert';
  el.textContent = '';
  el.className = base;
  el.style.display = 'none';
  el.classList.add('d-none');
}

function renderStatusBadge(status){
  const normalized = (status || '').toLowerCase();
  let text = 'Estado desconocido';
  let cls = 'bg-secondary';
  if (normalized === 'pendiente') { text = 'En proceso'; cls = 'bg-warning text-dark'; }
  else if (normalized === 'activa') { text = 'Activa'; cls = 'bg-success'; }
  else if (normalized === 'rechazada') { text = 'Rechazada'; cls = 'bg-danger'; }
  return `<span class="badge ${cls}">${text}</span>`;
}

/* ---------- Custom select helpers ---------- */
function initCustomSelects(){
  const customs = document.querySelectorAll('.custom-select');
  customs.forEach(c => {
    const sel = c.querySelector('.selected');
    const ul = c.querySelector('.options');
    // open/close on click
    c.addEventListener('click', (e) => {
      // toggle
      const isOpen = c.classList.toggle('open');
      c.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
      if (isOpen) { positionOptionsBelow(c, ul); }
    });
    // keyboard support
    c.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape') { c.classList.remove('open'); c.setAttribute('aria-expanded','false'); }
    });
    // click on option
    ul.addEventListener('click', (ev) => {
      const li = ev.target.closest('li');
      if (!li || li.classList.contains('disabled')) return;
      const value = li.dataset.value;
      const text = li.textContent;
      // set hidden input and visible text
      const hid = c.querySelector('input[type=hidden]');
      hid.value = value;
      sel.textContent = text;
      // close
      c.classList.remove('open');
      c.setAttribute('aria-expanded','false');
      // update other custom selects to disable duplicates
      updateCustomDisabled();
    });
    // close if clicking outside
    document.addEventListener('click', (ev) => {
      if (!c.contains(ev.target)) { c.classList.remove('open'); c.setAttribute('aria-expanded','false'); }
    });
  });
}

function positionOptionsBelow(container, ul){
  // ensure the options box is placed below the control
  // reset any inline styles
  ul.style.top = '';
  ul.style.bottom = '';
  // put below with small offset
  ul.style.top = (container.offsetHeight + 6) + 'px';
}

function updateCustomDisabled(){
  const customs = Array.from(document.querySelectorAll('.custom-select'));
  const selectedValues = customs.map(c => c.querySelector('input[type=hidden]').value).filter(v => v);
  customs.forEach(c => {
    const ul = c.querySelector('.options');
    Array.from(ul.children).forEach(li => {
      if (!li.dataset.value) return;
      if (selectedValues.includes(li.dataset.value) && c.querySelector('input[type=hidden]').value !== li.dataset.value) {
        li.classList.add('disabled');
      } else {
        li.classList.remove('disabled');
      }
    });
  });
}
