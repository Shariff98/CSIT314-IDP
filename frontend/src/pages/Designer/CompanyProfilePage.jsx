import { useEffect, useState } from 'react';
import PageHeader from '../../components/PageHeader';
import { useApp } from '../../context/AppContext';
import { flaskApi } from '../../services/api';
import { pageRequest } from '../../utils/projects';

const INFO = [['name', 'Company name'], ['registration_no', 'Registration number'], ['address', 'Address'],
  ['phone', 'Phone'], ['email', 'Email']];
const blankInfo = { name: '', registration_no: '', address: '', phone: '', email: '', description: '' };
const list = (value) => (Array.isArray(value) ? value.join(', ') : value || '');

export function companyForms(company) {
  return {
    info: company ? Object.fromEntries(Object.keys(blankInfo).map((key) => [key, company[key] || ''])) : blankInfo,
    specialisations: { specialisations: list(company?.specialisations), service_areas: list(company?.service_areas) },
    credentials: { certifications: company?.certifications || '', awards: company?.awards || '',
      years_experience: String(company?.years_experience ?? 0) },
    services: { budget_min: company?.budget_min ? String(company.budget_min) : '',
      budget_max: company?.budget_max ? String(company.budget_max) : '', services: list(company?.services) },
  };
}

// The designer's company profile. Each section saves on its own, with the matching story:
// US-24 create, US-02 view, US-32 details, US-25 specialisations, US-12 credentials,
// US-14 budget and services, US-13 team, US-52 logo and cover, US-15 preview.
export default function CompanyProfilePage({ go }) {
  const { user } = useApp();
  const [company, setCompany] = useState(undefined);
  const [team, setTeam] = useState([]);
  const [forms, setForms] = useState(companyForms(null));
  const [member, setMember] = useState({ name: '', position: '' });
  const [busy, setBusy] = useState('');
  const [message, setMessage] = useState(null);
  const [loadError, setLoadError] = useState('');

  function show(data) {
    setCompany(data.company);
    setTeam(data.team);
    setForms(companyForms(data.company));
  }

  useEffect(() => pageRequest(signal => flaskApi.getMyCompany({ signal }), {
    success: response => show(response.data),
    failure: failure => setLoadError(failure.message),
  }), []);

  async function run(name, request, success) {
    setBusy(name);
    setMessage(null);
    try {
      const response = await request();
      show(response.data);
      setMessage({ ok: true, text: success });
      return true;
    } catch (error) {
      setMessage({ ok: false, text: error.message });
      return false;
    } finally {
      setBusy('');
    }
  }

  const edit = (section, field) => (event) => setForms({ ...forms, [section]: { ...forms[section], [field]: event.target.value } });
  const field = (section, key, label, props = {}) => (
    <label key={key}>{label}<input value={forms[section][key]} onChange={edit(section, key)} {...props} /></label>
  );
  const submit = (name, request, success) => (event) => { event.preventDefault(); run(name, request, success); };

  if (loadError) return <div className="page-shell"><div className="alert error-alert" role="alert">Could not load your company: {loadError}</div></div>;
  if (company === undefined) return <div className="page-shell"><p role="status">Loading company profile...</p></div>;

  const detailsForm = (
    <form className="panel form-card" aria-label="Company details" onSubmit={submit('info',
      () => (company ? flaskApi.updateCompany(forms.info) : flaskApi.createCompany(forms.info)),
      company ? 'Company details saved.' : 'Company profile created.')}>
      <h2>{company ? 'Company details' : 'Create your company profile'}</h2>
      <fieldset disabled={!!busy} style={{ border: 0, margin: 0, padding: 0, minWidth: 0 }}>
        <div className="two-column-form">{INFO.map(([key, label]) => field('info', key, label))}</div>
        <label>About the company<textarea rows="3" value={forms.info.description} onChange={edit('info', 'description')} /></label>
        <button className="primary-button" type="submit">{company ? 'Save details' : 'Create company profile'}</button>
      </fieldset>
    </form>
  );

  return (
    <div className="page-shell">
      <PageHeader eyebrow="Company" title={company?.name || 'Company profile'}
        text="What customers see on your company page."
        actions={company && <button className="secondary-button" onClick={() => go('designer', { id: user.id })}>Preview public page</button>} />
      {message && <div className={`alert ${message.ok ? 'success-alert' : 'error-alert'}`} role={message.ok ? 'status' : 'alert'}>{message.text}</div>}
      {!company ? detailsForm : <>
        <div className="two-panel-grid">
          {detailsForm}
          <section className="panel form-card" aria-label="Logo and cover image">
            <h2>Logo and cover image</h2>
            {['logo', 'cover'].map((kind) => <div key={kind} className="button-row" style={{ marginBottom: 12 }}>
              {company[`${kind}_url`] ? <img className="company-logo" src={company[`${kind}_url`]} alt={`Current ${kind}`} /> : <span className="muted">No {kind} yet.</span>}
              <label>{kind === 'logo' ? 'Upload logo' : 'Upload cover image'}<input type="file" accept="image/*" disabled={!!busy} onChange={(event) => {
                const file = event.currentTarget.files?.[0];
                event.currentTarget.value = '';
                if (file) run(kind, () => flaskApi.uploadCompanyImage(kind, file), `${kind === 'logo' ? 'Logo' : 'Cover image'} uploaded.`);
              }} /></label>
            </div>)}
          </section>
        </div>

        <div className="two-panel-grid section-block">
          <form className="panel form-card" aria-label="Specialisations" onSubmit={submit('specialisations', () => flaskApi.updateSpecialisations(forms.specialisations), 'Specialisations saved.')}>
            <h2>Specialisations and service areas</h2>
            <fieldset disabled={!!busy} style={{ border: 0, margin: 0, padding: 0, minWidth: 0 }}>
              {field('specialisations', 'specialisations', 'Styles you specialise in (comma-separated)', { placeholder: 'Modern, Japandi' })}
              {field('specialisations', 'service_areas', 'Areas you serve (comma-separated)', { placeholder: 'North, East' })}
              <button className="primary-button" type="submit">Save</button>
            </fieldset>
          </form>

          <form className="panel form-card" aria-label="Budget and services" onSubmit={submit('services', () => flaskApi.updateServices(forms.services), 'Budget and services saved.')}>
            <h2>Budget range and services</h2>
            <fieldset disabled={!!busy} style={{ border: 0, margin: 0, padding: 0, minWidth: 0 }}>
              <div className="two-column-form">
                {field('services', 'budget_min', 'Minimum budget (SGD)', { type: 'number', min: 1 })}
                {field('services', 'budget_max', 'Maximum budget (SGD)', { type: 'number', min: 1 })}
              </div>
              {field('services', 'services', 'Services (comma-separated)', { placeholder: 'Full renovation, Carpentry' })}
              <button className="primary-button" type="submit">Save</button>
            </fieldset>
          </form>

          <form className="panel form-card" aria-label="Credentials" onSubmit={submit('credentials', () => flaskApi.updateCredentials(forms.credentials), 'Credentials saved.')}>
            <h2>Certifications, awards and experience</h2>
            <fieldset disabled={!!busy} style={{ border: 0, margin: 0, padding: 0, minWidth: 0 }}>
              {field('credentials', 'certifications', 'Certifications (comma-separated)')}
              {field('credentials', 'awards', 'Awards (comma-separated)')}
              {field('credentials', 'years_experience', 'Years of experience', { type: 'number', min: 0, max: 80 })}
              <button className="primary-button" type="submit">Save</button>
            </fieldset>
          </form>

          <section className="panel form-card" aria-label="Team members">
            <h2>Team members</h2>
            {team.length ? <ul className="team-list">{team.map((person) => <li key={person.id}>
              <span><strong>{person.name}</strong> <span className="muted">{person.position}</span></span>
              <button className="danger-button compact" disabled={!!busy}
                onClick={() => run('team', () => flaskApi.removeTeamMember(person.id), `${person.name} removed.`)}>Remove</button>
            </li>)}</ul> : <p className="muted">No team members yet.</p>}
            <form className="inline-form" onSubmit={async (event) => {
              event.preventDefault();
              if (await run('team', () => flaskApi.addTeamMember(member), `${member.name} added.`)) setMember({ name: '', position: '' });
            }}>
              <label>Name<input value={member.name} onChange={(e) => setMember({ ...member, name: e.target.value })} /></label>
              <label>Position<input value={member.position} onChange={(e) => setMember({ ...member, position: e.target.value })} /></label>
              <button className="primary-button" type="submit" disabled={!!busy}>Add</button>
            </form>
          </section>
        </div>
      </>}
    </div>
  );
}
