export default function EmptyState({ title, text }) {
  return <div className="empty-state panel"><h3>{title}</h3><p className="muted">{text}</p></div>;
}
