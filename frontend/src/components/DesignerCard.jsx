// One design company from GET /api/designers.
const placeholder = '/floor-plan.svg';
const money = (value) => `$${Number(value).toLocaleString()}`;

export default function DesignerCard({ designer, onView }) {
  const picture = designer.cover_url || designer.preview_url || designer.logo_url || placeholder;
  const budget = designer.budget_min && designer.budget_max ? `${money(designer.budget_min)} – ${money(designer.budget_max)}` : null;
  return (
    <article className="card designer-card">
      <img className="card-image logo-image" src={picture} alt=""
        onError={(event) => { event.currentTarget.onerror = null; event.currentTarget.src = placeholder; }} />
      <div className="card-body">
        <div className="card-kicker">{(designer.service_areas || []).join(' · ') || 'Singapore'}</div>
        <h3>{designer.name}</h3>
        <p className="muted">{designer.project_count} published project(s){designer.years_experience ? ` · ${designer.years_experience} years` : ''}</p>
        <div className="tag-row">
          {(designer.specialisations || []).slice(0, 3).map((item) => <span className="tag" key={item}>{item}</span>)}
        </div>
        <p className="muted line-clamp">{designer.description}</p>
        {budget && <p><strong>Typical budget:</strong> {budget}</p>}
        <div className="card-actions">
          <button className="primary-button" onClick={() => onView(designer.designer_id)}>View company</button>
        </div>
      </div>
    </article>
  );
}
