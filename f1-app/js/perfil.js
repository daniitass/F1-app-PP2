// perfil.js - manejo del formulario de cambio de contraseña
const API_BASE = 'http://127.0.0.1:5500';

const form = document.getElementById('perfilForm');
const currentPassword = document.getElementById('currentPassword');
const newPassword = document.getElementById('newPassword');
const confirmPassword = document.getElementById('confirmPassword');
const alertBox = document.getElementById('perfilAlert');
const submitBtn = form?.querySelector('button[type="submit"]');

// Regex para validar contraseña: al menos 1 mayúscula, 1 minúscula, 1 número, mínimo 8 caracteres
const pwdRegex = /(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}/;

function showAlert(message, type = 'danger') {
  if (!alertBox) return;
  alertBox.textContent = message;
  alertBox.className = `alert alert-${type} mt-4`;
  alertBox.classList.remove('d-none');
}

function hideAlert() {
  if (!alertBox) return;
  alertBox.textContent = '';
  alertBox.className = 'alert mt-4 d-none';
}

function validatePassword(password) {
  return pwdRegex.test(password);
}

if (form) {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    event.stopPropagation();
    hideAlert();

    const currentPwd = currentPassword.value.trim();
    const newPwd = newPassword.value.trim();
    const confirmPwd = confirmPassword.value.trim();

    // Validación de coincidencia de contraseñas
    if (newPwd !== confirmPwd) {
      confirmPassword.setCustomValidity('Las contraseñas no coinciden');
      showAlert('Las contraseñas no coinciden.', 'danger');
      form.classList.add('was-validated');
      return;
    } else {
      confirmPassword.setCustomValidity('');
    }

    // Validación de formato de nueva contraseña
    if (!validatePassword(newPwd)) {
      newPassword.setCustomValidity('La contraseña debe tener al menos 1 mayúscula, 1 minúscula y 1 número, y mínimo 8 caracteres');
      showAlert('La nueva contraseña no cumple con los requisitos mínimos.', 'danger');
      form.classList.add('was-validated');
      return;
    } else {
      newPassword.setCustomValidity('');
    }

    // Validación básica HTML5
    if (!form.checkValidity()) {
      showAlert('Revisá los campos marcados en rojo antes de continuar.', 'danger');
      form.classList.add('was-validated');
      return;
    }

    // Verificar que el usuario esté logueado
    const userId = localStorage.getItem('user_id');
    if (!userId) {
      showAlert('Debes iniciar sesión para cambiar tu contraseña.', 'warning');
      return;
    }

    // Deshabilitar botón durante la petición
    if (submitBtn) submitBtn.disabled = true;

    try {
      const payload = {
        user_id: Number(userId),
        current_password: currentPwd,
        new_password: newPwd
      };

      const res = await fetch(`${API_BASE}/change-password`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      const data = await res.json().catch(() => ({}));

      if (res.ok && data.success) {
        showAlert('Contraseña actualizada correctamente.', 'success');
        form.reset();
        form.classList.remove('was-validated');
        // Opcional: redirigir después de un tiempo
        setTimeout(() => {
          window.location.href = 'index.html';
        }, 2000);
      } else {
        showAlert(data.message || 'No se pudo actualizar la contraseña.', 'danger');
        form.classList.add('was-validated');
      }
    } catch (err) {
      console.error('Error changing password', err);
      showAlert('Error de comunicación con el servidor.', 'danger');
    } finally {
      if (submitBtn) submitBtn.disabled = false;
    }
  });

  // Validación en tiempo real para confirmar contraseña
  confirmPassword.addEventListener('input', () => {
    if (confirmPassword.value !== newPassword.value) {
      confirmPassword.setCustomValidity('Las contraseñas no coinciden');
    } else {
      confirmPassword.setCustomValidity('');
    }
  });

  // Validación en tiempo real para nueva contraseña
  newPassword.addEventListener('input', () => {
    if (confirmPassword.value && confirmPassword.value !== newPassword.value) {
      confirmPassword.setCustomValidity('Las contraseñas no coinciden');
    } else {
      confirmPassword.setCustomValidity('');
    }
    if (newPassword.value && !validatePassword(newPassword.value)) {
      newPassword.setCustomValidity('La contraseña debe tener al menos 1 mayúscula, 1 minúscula y 1 número, y mínimo 8 caracteres');
    } else {
      newPassword.setCustomValidity('');
    }
  });
}

