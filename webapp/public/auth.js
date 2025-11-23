const form = document.querySelector('#auth-form');
const errorEl = document.querySelector('#auth-error');
if (!form || !errorEl) {
  throw new Error('Auth form missing from page');
}
const mode = form.dataset.mode || 'login';

const handleExistingSession = async () => {
  try {
    const response = await fetch('/api/auth/me', { credentials: 'include' });
    if (response.ok) {
      window.location.href = '/lobby';
    }
  } catch (_error) {
    // Ignore and allow normal flow
  }
};

const submitAuth = async (event) => {
  event.preventDefault();
  errorEl.textContent = '';

  const formData = new FormData(form);
  const payload = {
    email: formData.get('email'),
    password: formData.get('password'),
  };

  if (mode === 'register') {
    payload.displayName = formData.get('displayName');
  }

  try {
    const response = await fetch(`/api/auth/${mode}`, {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.message || 'Unable to complete request');
    }

    window.location.href = '/lobby';
  } catch (error) {
    errorEl.textContent = error.message;
  }
};

form?.addEventListener('submit', submitAuth);
handleExistingSession();
