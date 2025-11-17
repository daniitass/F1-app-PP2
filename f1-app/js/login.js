const form = document.getElementById('loginForm');
const alertEl = document.getElementById('loginAlert');
const submitBtn = document.getElementById('submitBtn');

function showAlert(message, type='danger'){
  alertEl.style.display = 'block';
  alertEl.className = 'alert alert-' + type;
  alertEl.textContent = message;
}

form.addEventListener('submit', async (e)=>{
  e.preventDefault();
  alertEl.style.display = 'none';

  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;

  if(!email || !password){
    showAlert('Por favor completa todos los campos', 'danger');
    return;
  }

  // submit via fetch to backend
  submitBtn.disabled = true;
  try{
    const res = await fetch('http://127.0.0.1:5500/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if(res.ok && data.success){
      showAlert('¡Bienvenido! Redirigiendo...', 'success');
      // Guardar token en localStorage
      if(data.token){
        localStorage.setItem('auth_token', data.token);
      }
      localStorage.setItem('user_id', data.user_id);
      localStorage.setItem('user_name', data.user_name);
      // Redirigir a apuestas después de 1.5 segundos
      setTimeout(() => {
        window.location.href = 'apuestas.html';
      }, 1500);
    } else {
      showAlert(data.message || 'Error en el login', 'danger');
    }
  }catch(err){
    showAlert('Error de comunicación con el servidor', 'danger');
    console.error(err);
  }finally{
    submitBtn.disabled = false;
  }
});
