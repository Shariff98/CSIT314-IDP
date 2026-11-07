import { useState } from 'react';
import FieldError from '../../components/FieldError';
import { useApp } from '../../context/AppContext';
import { homeForRole } from '../../utils/auth';
import { isEmail, isRequired } from '../../utils/validation';

export default function LoginPage({ go }) {
  const { login } = useApp();
  const [form, setForm] = useState({ email: '' });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: '' }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const password = new FormData(event.currentTarget).get('password');
    const formElement = event.currentTarget;
    const next = {};
    if (!isEmail(form.email)) next.email = 'Enter a valid email address.';
    if (!isRequired(password)) next.password = 'Password is required.';
    setErrors(next);
    if (Object.keys(next).length) return;

    try {
      setServerError('');
      setSubmitting(true);
      const loggedIn = await login(form.email, password);
      go(homeForRole[loggedIn.role] || 'landing');
    } catch (error) {
      setServerError(error.message);
    } finally {
      formElement.elements.password.value = '';
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="panel auth-card" onSubmit={handleSubmit} noValidate>
        <span className="eyebrow">Welcome back</span>
        <h1>Log in</h1>
        <p className="muted">Log in with your Design Match account.</p>
        <label>Email address<input type="email" value={form.email} onChange={(e) => update('email', e.target.value)} placeholder="you@example.com" /><FieldError message={errors.email} /></label>
        <label>Password<input type="password" name="password" autoComplete="current-password" placeholder="Enter password" /><FieldError message={errors.password} /></label>
        {serverError && <div className="alert error-alert">{serverError}</div>}
        <button className="primary-button full-width" type="submit" disabled={submitting}>{submitting ? 'Logging in...' : 'Log in'}</button>
        <button className="text-button" type="button" onClick={() => go('register')}>Need a homeowner account? Register</button>
      </form>
    </div>
  );
}
