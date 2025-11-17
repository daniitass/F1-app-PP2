// apuestas.js - frontend helpers for apuestas.html
// Loads pilotos from the apuestas API and populates the TOP3 selects.
const API_BASE = 'http://127.0.0.1:5500';

async function loadPilotos() {
  try {
    const res = await fetch(`${API_BASE}/api/pilotos`);
    if (!res.ok) return;
    const data = await res.json();
    if (!data.success) return;
    const pilotos = data.pilotos || [];
    // If custom-select elements exist, populate them; otherwise fallback to native selects
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
      // update disabled state according to current selections
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

document.addEventListener('DOMContentLoaded', () => {
  loadPilotos();
  const tabTop3 = document.getElementById('tab-top3');
  if (tabTop3) tabTop3.addEventListener('shown.bs.tab', loadPilotos);
  // wire up custom select behavior
  initCustomSelects();
});

// Optional: prevent selecting the same pilot twice
function preventDuplicates(selectIds = ['top1','top2','top3']){
  // Works for native selects only; when using custom selects we call updateCustomDisabled()
  const sels = selectIds.map(id => document.getElementById(id)).filter(Boolean);
  sels.forEach(s => s.addEventListener('change', () => {
    const values = sels.map(x => x.value).filter(v => v !== '');
    // enable all options
    sels.forEach(sx => {
      Array.from(sx.options).forEach(opt => opt.disabled = false);
    });
    // disable selected values on other selects
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

// enable duplicate prevention by default
document.addEventListener('DOMContentLoaded', () => preventDuplicates());

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
  const rect = container.getBoundingClientRect();
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
