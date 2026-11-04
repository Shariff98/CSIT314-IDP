export default function StatusBadge({ children }) {
  const value = String(children || '').toLowerCase().replaceAll(' ', '-');
  return <span className={`status-badge status-${value}`}>{children}</span>;
}
