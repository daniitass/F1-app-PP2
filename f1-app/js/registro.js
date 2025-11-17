// Password policy: at least 1 uppercase, 1 lowercase, 1 digit
const pwdRegex = /(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{6,}/;

const form = document.getElementById('registroForm');
const alertEl = document.getElementById('formAlert');
const submitBtn = document.getElementById('submitBtn');

function showAlert(message, type='danger'){
  alertEl.style.display = 'block';
  alertEl.className = 'alert alert-' + type;
  alertEl.textContent = message;
}

form.addEventListener('submit', async (e)=>{
  e.preventDefault();
  alertEl.style.display = 'none';

  const nombre = document.getElementById('nombre').value.trim();
  const apellido = document.getElementById('apellido').value.trim();
  const email = document.getElementById('email').value.trim();
  const fecha = document.getElementById('fecha').value;
  const password = document.getElementById('password').value;
  const confirmar = document.getElementById('confirmar').value;

  if(password !== confirmar){
    showAlert('Las contraseñas no coinciden', 'danger');
    return;
  }
  if(!pwdRegex.test(password)){
    showAlert('La contraseña debe tener al menos 1 mayúscula, 1 minúscula y 1 número, y mínimo 6 caracteres', 'danger');
    return;
  }

  // submit via fetch to backend
  submitBtn.disabled = true;
  try{
    const res = await fetch('http://127.0.0.1:5500/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre, apellido, email, fecha_nacimiento: fecha, password })
    });
    const data = await res.json();
    if(res.ok && data.success){
      showAlert('Registro completado correctamente', 'success');
      form.reset();
    } else {
      showAlert(data.message || 'Error en el registro', 'danger');
    }
  }catch(err){
    showAlert('Error de comunicación con el servidor', 'danger');
  }finally{
    submitBtn.disabled = false;
  }
});
