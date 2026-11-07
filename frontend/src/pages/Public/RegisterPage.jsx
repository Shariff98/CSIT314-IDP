import { useState } from 'react';
import FieldError from '../../components/FieldError';
import { useApp } from '../../context/AppContext';
import { isEmail, isPhone, isRequired, minLength } from '../../utils/validation';

export default function RegisterPage({ go }) {
  const { registerCustomer } = useApp();
  const [form, setForm] = useState({ name: '', email: '', phone: '', password: '', confirmPassword: '' });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState('');

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: '' }));
  }

  async function submit(event) {
    event.preventDefault();
    const next = {};
    if (!isRequired(form.name)) next.name = 'Name is required.';
    if (!isEmail(form.email)) next.email = 'Enter a valid email address.';
    if (!isPhone(form.phone)) next.phone = 'Enter a valid phone number.';
    if (!minLength(form.password, 8)) next.password = 'Password must be at least 8 characters.';
    if (form.confirmPassword !== form.password) next.confirmPassword = 'Passwords do not match.';
    setErrors(next);
    if (Object.keys(next).length) return;

    try {
      setServerError('');
      // === BACKEND INTEGRATION === Replace mock customer registration with POST /customers/register.
      await registerCustomer(form);
      go('customer-home');
    } catch (error) {
      setServerError(error.message);
    }
  }

  return (
    <div className="auth-page">
      <form className="panel auth-card" onSubmit={submit} noValidate>
        <span className="eyebrow">Homeowner registration</span>
        <h1>Create customer account</h1>
        <label>Full name<input value={form.name} onChange={(e) => update('name', e.target.value)} /><FieldError message={errors.name} /></label>
        <label>Email<input type="email" value={form.email} onChange={(e) => update('email', e.target.value)} /><FieldError message={errors.email} /></label>
        <label>Phone number<input value={form.phone} onChange={(e) => update('phone', e.target.value)} placeholder="+65 9123 4567" /><FieldError message={errors.phone} /></label>
        <label>Password<input type="password" value={form.password} onChange={(e) => update('password', e.target.value)} /><FieldError message={errors.password} /></label>
        <label>Confirm password<input type="password" value={form.confirmPassword} onChange={(e) => update('confirmPassword', e.target.value)} /><FieldError message={errors.confirmPassword} /></label>
        {serverError && <div className="alert error-alert">{serverError}</div>}
        <button className="primary-button full-width" type="submit">Create account</button>
        <button className="text-button" type="button" onClick={() => go('login')}>Already have an account? Log in</button>
      </form>
    </div>
  );
}
