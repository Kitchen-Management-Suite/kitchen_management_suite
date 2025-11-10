/* validation.js */

export function validateEmail(email) {
  if (!email) return false;
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email.trim());
}

export function validateUsername(username) {
  if (!username || username.trim().length === 0) {
    return { valid: false, error: "Username is required" };
  }

  const trimmed = username.trim();

  if (trimmed.length < 3) {
    return { valid: false, error: "Username must be at least 3 characters" };
  }

  if (trimmed.length > 50) {
    return { valid: false, error: "Username must be less than 50 characters" };
  }

  if (!/^[a-zA-Z0-9_-]+$/.test(trimmed)) {
    return {
      valid: false,
      error:
        "Username can only contain letters, numbers, hyphens, and underscores",
    };
  }

  return { valid: true, error: null };
}

export function validatePassword(pwd) {
  if (!pwd) {
    return { valid: false, error: "Password is required", strength: "" };
  }

  if (pwd.length < 6) {
    return {
      valid: false,
      error: "Password must be at least 6 characters",
      strength: "weak",
    };
  }

  if (pwd.length > 128) {
    return {
      valid: false,
      error: "Password must be less than 128 characters",
      strength: "",
    };
  }

  const strength = calculatePasswordStrength(pwd);
  return { valid: true, error: null, strength };
}

export function calculatePasswordStrength(pwd) {
  if (!pwd) return "";
  if (pwd.length < 6) return "weak";

  const hasLower = /[a-z]/.test(pwd);
  const hasUpper = /[A-Z]/.test(pwd);
  const hasDigit = /\d/.test(pwd);
  const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(pwd);

  let strengthScore = 0;
  if (pwd.length >= 8) strengthScore++;
  if (pwd.length >= 12) strengthScore++;
  if (hasLower) strengthScore++;
  if (hasUpper) strengthScore++;
  if (hasDigit) strengthScore++;
  if (hasSpecial) strengthScore++;

  if (strengthScore <= 2) return "weak";
  if (strengthScore <= 4) return "medium";
  return "strong";
}

export function validateAge(dateString) {
  if (!dateString) {
    return { valid: false, error: "Date of birth is required", age: 0 };
  }

  const birthDate = new Date(dateString);
  const today = new Date();

  if (isNaN(birthDate.getTime())) {
    return { valid: false, error: "Invalid date format", age: 0 };
  }

  if (birthDate > today) {
    return {
      valid: false,
      error: "Date of birth cannot be in the future",
      age: 0,
    };
  }

  let age = today.getFullYear() - birthDate.getFullYear();
  const monthDiff = today.getMonth() - birthDate.getMonth();

  if (
    monthDiff < 0 ||
    (monthDiff === 0 && today.getDate() < birthDate.getDate())
  ) {
    age--;
  }

  if (age < 13) {
    return {
      valid: false,
      error: "You must be at least 13 years old to register",
      age,
    };
  }

  if (age > 120) {
    return { valid: false, error: "Please enter a valid date of birth", age };
  }

  return { valid: true, error: null, age };
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
