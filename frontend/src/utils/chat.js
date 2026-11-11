// Helpers for the Budget Match Assistant (ChatWidget). Kept here so node --test can cover them.
const money = (n) => '$' + Number(n).toLocaleString();

function describeBudget(prefs) {
  if (!prefs.budget) return '';
  if (prefs.budget_min) return `${money(prefs.budget_min)}–${money(prefs.budget)}`;
  return `${prefs.strict_max ? 'up to' : 'around'} ${money(prefs.budget)}`;
}

// One line summary of what the assistant remembers, e.g. "Modern Kitchen · around $10,000 · not Industrial".
export function describePrefs(prefs) {
  if (!prefs) return '';
  const what = [...(prefs.styles || []), prefs.category, prefs.property_type].filter(Boolean).join(' ');
  const avoid = (prefs.exclude_styles || []).length ? `not ${prefs.exclude_styles.join(', ')}` : '';
  return [what, describeBudget(prefs), avoid].filter(Boolean).join(' · ');
}
