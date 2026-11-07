// Helpers for the Budget Match Assistant (ChatWidget). Kept here so node --test can cover them.
const money = (n) => '$' + Number(n).toLocaleString();

// One line summary of what the assistant remembers, e.g. "Modern Kitchen · around $10,000".
export function describePrefs(prefs) {
  if (!prefs) return '';
  const what = [...(prefs.styles || []), prefs.category, prefs.property_type].filter(Boolean).join(' ');
  const budget = prefs.budget ? `${prefs.strict_max ? 'up to' : 'around'} ${money(prefs.budget)}` : '';
  return [what, budget].filter(Boolean).join(' · ');
}
