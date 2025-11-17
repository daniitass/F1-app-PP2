const API_BASE = 'http://127.0.0.1:5500';
let paymentAlert;
let betSummary;
let paymentForm;
let btnPagar;
let btnRechazar;
let betData = null;

document.addEventListener('DOMContentLoaded', () => {
  paymentAlert = document.getElementById('paymentAlert');
  betSummary = document.getElementById('betSummary');
  paymentForm = document.getElementById('paymentForm');
  btnPagar = document.getElementById('btnPagar');
  btnRechazar = document.getElementById('btnRechazar');

  const params = new URLSearchParams(window.location.search);
  const pendingFromQuery = params.get('bet_id');
  const pendingFromStorage = localStorage.getItem('pending_bet_id');
  const betId = pendingFromQuery || pendingFromStorage;

  if (!betId) {
    showAlert('No encontramos una apuesta pendiente para pagar. Volvé a apuestas e iniciá una nueva.', 'warning');
    return;
  }

  if (btnPagar) btnPagar.addEventListener('click', () => updateStatus('activa'));
  if (btnRechazar) btnRechazar.addEventListener('click', () => updateStatus('rechazada'));

  fetchBetDetail(betId);
});

async function fetchBetDetail(betId){
  showAlert('Cargando información de la apuesta...', 'info');
  try{
    const res = await fetch(`${API_BASE}/apuestas/top3/detalle?bet_id=${encodeURIComponent(betId)}`);
    const data = await res.json();
    if(res.ok && data.success){
      betData = data.bet;
      renderBet();
      hideAlert();
    }else{
      showAlert(data.message || 'No pudimos cargar la apuesta.', 'danger');
    }
  }catch(err){
    console.error(err);
    showAlert('Error al comunicarse con el servidor.', 'danger');
  }
}

function renderBet(){
  if(!betData) return;
  const { top1, top2, top3, status } = betData;
  setText('betTop1', top1);
  setText('betTop2', top2);
  setText('betTop3', top3);
  setText('betStatus', statusLabel(status));

  betSummary?.classList.remove('d-none');

  if(status === 'pendiente'){
    paymentForm?.classList.remove('d-none');
    showAlert('Revisá los datos y confirmá el pago para activar tu apuesta.', 'warning');
  }else if(status === 'activa'){
    paymentForm?.classList.add('d-none');
    localStorage.removeItem('pending_bet_id');
    showAlert('La apuesta ya está activa. Podés volver a apuestas para ver el estado.', 'success');
  }else if(status === 'rechazada'){
    paymentForm?.classList.add('d-none');
    localStorage.removeItem('pending_bet_id');
    showAlert('El pago fue rechazado. Podés crear una nueva apuesta cuando quieras.', 'danger');
  }
}

async function updateStatus(newStatus){
  if(!betData) return;
  const userId = Number(localStorage.getItem('user_id') || 0);
  if(!userId){
    showAlert('Debes iniciar sesión nuevamente para continuar.', 'warning');
    return;
  }

  toggleButtons(true);
  try{
    const payload = {
      bet_id: betData.id,
      user_id: userId,
      status: newStatus,
    };
    const res = await fetch(`${API_BASE}/apuestas/top3/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if(res.ok && data.success){
      betData = data.bet;
      renderBet();
      if(newStatus !== 'pendiente'){
        localStorage.removeItem('pending_bet_id');
      }
    }else{
      showAlert(data.message || 'No pudimos actualizar el estado del pago.', 'danger');
    }
  }catch(err){
    console.error(err);
    showAlert('Error de comunicación con el servidor.', 'danger');
  }finally{
    toggleButtons(false);
  }
}

function statusLabel(status){
  const normalized = (status || '').toLowerCase();
  if(normalized === 'activa') return 'Activa';
  if(normalized === 'rechazada') return 'Rechazada';
  return 'En proceso';
}

function showAlert(message, type='info'){
  if(!paymentAlert) return;
  paymentAlert.textContent = message;
  paymentAlert.className = `alert alert-${type}`;
  paymentAlert.classList.remove('d-none');
}

function hideAlert(){
  if(!paymentAlert) return;
  paymentAlert.className = 'alert alert-info';
  paymentAlert.classList.add('d-none');
  paymentAlert.textContent = '';
}

function setText(id, text){
  const el = document.getElementById(id);
  if(el) el.textContent = text;
}

function toggleButtons(disabled){
  if(btnPagar) btnPagar.disabled = disabled;
  if(btnRechazar) btnRechazar.disabled = disabled;
}

