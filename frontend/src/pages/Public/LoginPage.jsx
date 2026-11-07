import { useState } from 'react';
import FieldError from '../../components/FieldError';
import { useApp } from '../../context/AppContext';
import { isEmail, isRequired } from '../../utils/validation';

export default function LoginPage({ go }) {
  const { login } = useApp();
  const [form, setForm] = useState({ email: '', password: '' });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState('');

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: '' }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const next = {};
    if (!isEmail(form.email)) next.email = 'Enter a valid email address.';
    if (!isRequired(form.password)) next.password = 'Password is required.';
    setErrors(next);
    if (Object.keys(next).length) return;

    try {
      setServerError('');
      // === BACKEND INTEGRATION === AppContext.login() currently validates against mock accounts.
      const loggedIn = await login(form.email, form.password);
      go(loggedIn.role === 'customer' ? 'customer-home' : loggedIn.role === 'designer' ? 'designer-dashboard' : 'admin-dashboard');
    } catch (error) {
      setServerError(error.message);
    }
  }

  return (
    <div className="auth-page">
      <form className="panel auth-card" onSubmit={handleSubmit} noValidate>
        <span className="eyebrow">Welcome back</span>
        <h1>Log in</h1>
        <p className="muted">Use a demo account or a customer account created in this prototype.</p>
        <label>Email address<input type="email" value={form.email} onChange={(e) => update('email', e.target.value)} placeholder="you@example.com" /><FieldError message={errors.email} /></label>
        <label>Password<input type="password" value={form.password} onChange={(e) => update('password', e.target.value)} placeholder="Enter password" /><FieldError message={errors.password} /></label>
        {serverError && <div className="alert error-alert">{serverError}</div>}
        <button className="primary-button full-width" type="submit">Log in</button>
        <div className="demo-box">
          <strong>Demo accounts</strong>
          <code>customer@example.com / password123</code>
          <code>designer@example.com / password123</code>
          <code>admin@example.com / password123</code>
          <code>admin2@example.com / password123</code>
          <code>pending@example.com / password123 (unverified ID demo)</code>
        </div>
        <button className="text-button" type="button" onClick={() => go('register')}>Need a homeowner account? Register</button>
      </form>
    </div>
  );
}
