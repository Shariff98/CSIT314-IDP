import { useState } from 'react';
import FieldError from '../../components/FieldError';
import { useApp } from '../../context/AppContext';
import { isEmail, isRequired, minLength } from '../../utils/validation';

export default function RegisterPage({ go }) {
  const { registerCustomer } = useApp();
  const [form, setForm] = useState({ name: '', email: '' });
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
    setErrors((current) => ({ ...current, [field]: '' }));
  }

  async function submit(event) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const fields = new FormData(formElement);
    const password = fields.get('password');
    const confirmPassword = fields.get('confirmPassword');
    const next = {};
    if (!isRequired(form.name)) next.name = 'Name is required.';
    if (!isEmail(form.email)) next.email = 'Enter a valid email address.';
    if (!minLength(password, 8)) next.password = 'Password must be at least 8 characters.';
    if (confirmPassword !== password) next.confirmPassword = 'Passwords do not match.';
    setErrors(next);
    if (Object.keys(next).length) return;

    try {
      setServerError('');
      setSubmitting(true);
      await registerCustomer({ ...form, password, confirmPassword });
      go('login');
    } catch (error) {
      setServerError(error.message);
    } finally {
      formElement.elements.password.value = '';
      formElement.elements.confirmPassword.value = '';
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="panel auth-card" onSubmit={submit} noValidate>
        <span className="eyebrow">Homeowner registration</span>
        <h1>Create customer account</h1>
        <label>Full name<input value={form.name} onChange={(e) => update('name', e.target.value)} /><FieldError message={errors.name} /></label>
        <label>Email<input type="email" value={form.email} onChange={(e) => update('email', e.target.value)} /><FieldError message={errors.email} /></label>
        <label>Password<input type="password" name="password" autoComplete="new-password" /><FieldError message={errors.password} /></label>
        <label>Confirm password<input type="password" name="confirmPassword" autoComplete="new-password" /><FieldError message={errors.confirmPassword} /></label>
        {serverError && <div className="alert error-alert">{serverError}</div>}
        <button className="primary-button full-width" type="submit" disabled={submitting}>{submitting ? 'Creating account...' : 'Create account'}</button>
        <button className="text-button" type="button" onClick={() => go('login')}>Already have an account? Log in</button>
      </form>
    </div>
  );
}
