/* validation.js */

export function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

export function calculatePasswordStrength(pwd) {
  if (!pwd) return "";
  if (pwd.length < 6) return "weak";
  if (pwd.length < 10 && !/\d/.test(pwd)) return "weak";
  if (pwd.length >= 10 && /\d/.test(pwd) && /[a-zA-Z]/.test(pwd))
    return "strong";
  return "medium";
}

export function validateAge(dateString) {
  const birthDate = new Date(dateString);
  const today = new Date();
  const age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();

  if (
    monthDiff < 0 ||
    (monthDiff === 0 && today.getDate() < birthDate.getDate())
  ) {
    return age - 1;
  }
  return age;
}

export function showError(field, message) {
  const errorEl = document.getElementById(`${field}-error`);
  const successEl = document.getElementById(`${field}-success`);
  const input = document.getElementById(field);

  if (errorEl) {
    errorEl.textContent = message;
    errorEl.style.display = "block";
  }
  if (successEl) successEl.style.display = "none";
  if (input) {
    input.classList.add("input-error");
    input.classList.remove("input-success");
  }
}

export function hideError(field) {
  const errorEl = document.getElementById(`${field}-error`);
  const input = document.getElementById(field);

  if (errorEl) errorEl.style.display = "none";
  if (input) input.classList.remove("input-error");
}

export function showSuccess(field) {
  const successEl = document.getElementById(`${field}-success`);
  const errorEl = document.getElementById(`${field}-error`);
  const input = document.getElementById(field);

  if (successEl) {
    successEl.style.display = "block";
    if (errorEl) errorEl.style.display = "none";
    if (input) {
      input.classList.add("input-success");
      input.classList.remove("input-error");
    }
  }
}
