import { useApp } from '../context/AppContext';

export default function DesignerCard({ designer, onView, showSave = true }) {
  const { favouriteDesignerIds, toggleFavouriteDesigner } = useApp();
  const saved = favouriteDesignerIds.includes(designer.id);

  return (
    <article className="card designer-card">
      <img className="card-image logo-image" src={designer.logo} alt={`${designer.companyName} placeholder`} />
      <div className="card-body">
        <div className="card-kicker">{designer.location}</div>
        <h3>{designer.companyName}</h3>
        <p className="rating-line">★ {designer.rating || 'New'} <span>({designer.reviewCount} reviews)</span></p>
        <div className="tag-row">
          {designer.specialties.slice(0, 3).map((item) => <span className="tag" key={item}>{item}</span>)}
        </div>
        <p className="muted line-clamp">{designer.description}</p>
        <p><strong>Typical budget:</strong> ${designer.budgetMin.toLocaleString()} – ${designer.budgetMax.toLocaleString()}</p>
        <div className="card-actions">
          <button className="primary-button" onClick={() => onView(designer.id)}>View profile</button>
          {showSave && <button className="secondary-button" onClick={() => toggleFavouriteDesigner(designer.id)}>{saved ? 'Saved' : 'Save'}</button>}
        </div>
      </div>
    </article>
  );
}
