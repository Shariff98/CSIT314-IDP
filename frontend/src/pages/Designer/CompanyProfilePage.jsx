import { useEffect, useState } from 'react';
import FieldError from '../../components/FieldError';
import PageHeader from '../../components/PageHeader';
import StatusBadge from '../../components/StatusBadge';
import { useApp } from '../../context/AppContext';
import { PROPERTY_TYPES } from '../../data/options';
import { isEmail, isPhone, isPositiveNumber, isRequired } from '../../utils/validation';

export default function CompanyProfilePage() {
  const { user, designers, categories, saveCompanyProfile } = useApp();
  const company = designers.find((item) => item.id === (user?.designerId || 101));
  const [form, setForm] = useState({companyName: '', registrationNo: '', contactEmail: '', phone: '', location: '', description: '', yearsExperience: '', budgetMin: '', budgetMax: '', specialties: '', services: '', propertyTypes: [], categoriesServed: []});
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (company) setForm({
      companyName: company.companyName,
      registrationNo: company.registrationNo,
      contactEmail: company.contactEmail,
      phone: company.phone,
      location: company.location,
      description: company.description,
      yearsExperience: company.yearsExperience,
      budgetMin: company.budgetMin,
      budgetMax: company.budgetMax,
      specialties: company.specialties.join(', '),
      services: company.services.join(', '),
      propertyTypes: company.propertyTypes || [],
      categoriesServed: company.categoriesServed || [],
    });
  }, [company]);

  function toggleSelection(field, value) {
    setForm((current) => ({
      ...current,
      [field]: current[field].includes(value)
        ? current[field].filter((item) => item !== value)
        : [...current[field], value]
    }));
  }

  async function submit(event) {
    event.preventDefault();
    const next = {};
    if (!isRequired(form.companyName)) next.companyName = 'Company name is required.';
    if (!isRequired(form.registrationNo)) next.registrationNo = 'Registration number is required.';
    if (!isEmail(form.contactEmail)) next.contactEmail = 'Enter a valid email.';
    if (!isPhone(form.phone)) next.phone = 'Enter a valid phone number.';
    if (!isRequired(form.location)) next.location = 'Location is required.';
    if (!isRequired(form.description)) next.description = 'Company description is required.';
    if (!isPositiveNumber(form.yearsExperience)) next.yearsExperience = 'Years of experience must be greater than 0.';
    if (!isPositiveNumber(form.budgetMin)) next.budgetMin = 'Minimum budget must be greater than 0.';
    if (!isPositiveNumber(form.budgetMax) || Number(form.budgetMax) < Number(form.budgetMin)) next.budgetMax = 'Maximum budget must be at least the minimum budget.';
    if (!isRequired(form.specialties)) next.specialties = 'Add at least one specialty.';
    if (!isRequired(form.services)) next.services = 'Add at least one service.';
    if (!form.propertyTypes.length) {next.propertyTypes = 'Select at least one property type.';}
    if (!form.categoriesServed.length) {next.categoriesServed = 'Select at least one renovation category.';}
    setErrors(next);
    if (Object.keys(next).length) return;

    // === BACKEND INTEGRATION === Company changes should be stored in DB; new/unverified companies are reviewed by admin.
    await saveCompanyProfile({
      ...form,
      yearsExperience: Number(form.yearsExperience),
      budgetMin: Number(form.budgetMin),
      budgetMax: Number(form.budgetMax),
      specialties: form.specialties.split(',').map((item) => item.trim()).filter(Boolean),
      services: form.services.split(',').map((item) => item.trim()).filter(Boolean),
      propertyTypes: form.propertyTypes,
      categoriesServed: form.categoriesServed,
    });
    setMessage(company?.verified ? 'Company profile updated.' : 'Company profile saved and remains pending administrator verification.');
  }

  return (
    <div className="page-shell narrow-content">
      <PageHeader eyebrow="Company profile" title={company?.verified ? 'Manage company profile' : 'Create / complete company profile'} text="Maintain company information, contact details, specialties and services." actions={<StatusBadge>{company?.verified ? 'verified' : company?.status || 'pending'}</StatusBadge>} />
      <form className="panel form-card large-form" onSubmit={submit} noValidate>
        <div className="two-column-form">
          <label>Company name<input value={form.companyName} onChange={(e) => setForm({ ...form, companyName: e.target.value })} /><FieldError message={errors.companyName} /></label>
          <label>Registration number<input value={form.registrationNo} onChange={(e) => setForm({ ...form, registrationNo: e.target.value })} /><FieldError message={errors.registrationNo} /></label>
          <label>Contact email<input type="email" value={form.contactEmail} onChange={(e) => setForm({ ...form, contactEmail: e.target.value })} /><FieldError message={errors.contactEmail} /></label>
          <label>Contact phone<input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /><FieldError message={errors.phone} /></label>
          <label>Location<input value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} /><FieldError message={errors.location} /></label>
          <label>Years of experience<input type="number" min="1" value={form.yearsExperience} onChange={(e) => setForm({ ...form, yearsExperience: e.target.value })} /><FieldError message={errors.yearsExperience} /></label>
          <label>Typical minimum budget<input type="number" min="1" value={form.budgetMin} onChange={(e) => setForm({ ...form, budgetMin: e.target.value })} /><FieldError message={errors.budgetMin} /></label>
          <label>Typical maximum budget<input type="number" min="1" value={form.budgetMax} onChange={(e) => setForm({ ...form, budgetMax: e.target.value })} /><FieldError message={errors.budgetMax} /></label>
        </div>
        <label>Company description<textarea rows="5" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /><FieldError message={errors.description} /></label>
        <label>Design specialties (comma-separated)<input value={form.specialties} onChange={(e) => setForm({ ...form, specialties: e.target.value })} placeholder="Modern, Minimalist, Scandinavian" /><FieldError message={errors.specialties} /></label>
        <label>Services (comma-separated)<input value={form.services} onChange={(e) => setForm({ ...form, services: e.target.value })} placeholder="Space Planning, Carpentry, Project Management" /><FieldError message={errors.services} /></label>
        <fieldset>
          <legend>Property types served</legend>

          <div className="tag-row">
            {PROPERTY_TYPES.map((type) => (
              <label
                key={type}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginRight: 14
                }}
              >
                <input
                  type="checkbox"
                  style={{ width: 'auto' }}
                  checked={form.propertyTypes.includes(type)}
                  onChange={() => toggleSelection('propertyTypes', type)}
                />
                {type}
              </label>
            ))}
          </div>

          <FieldError message={errors.propertyTypes} />
        </fieldset>

        <fieldset>
          <legend>Renovation categories (rooms / areas)</legend>

          <div className="tag-row">
            {categories.map((category) => (
              <label
                key={category}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  marginRight: 14
                }}
              >
                <input
                  type="checkbox"
                  style={{ width: 'auto' }}
                  checked={form.categoriesServed.includes(category)}
                  onChange={() => toggleSelection('categoriesServed', category)}
                />
                {category}
              </label>
            ))}
          </div>

          <FieldError message={errors.categoriesServed} />
        </fieldset>
        <button className="primary-button" type="submit">Save company profile</button>{message && <div className="alert success-alert">{message}</div>}
      </form>
    </div>
  );
}
