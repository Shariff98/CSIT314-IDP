export default function PageHeader({ eyebrow, title, text, actions }) {
  return (
    <div className="page-header">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        {text && <p>{text}</p>}
      </div>
      {actions && <div className="page-actions">{actions}</div>}
    </div>
  );
}
