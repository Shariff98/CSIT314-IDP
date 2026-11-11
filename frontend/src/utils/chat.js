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

const STORAGE_KEY = 'budget-chat';
const MAX_SAVED_MESSAGES = 40;

// Reads the saved conversation, or null when there is none or it can't be read.
export function loadChat(storage) {
  try {
    const data = JSON.parse(storage?.getItem(STORAGE_KEY) ?? 'null');
    if (!data || !Array.isArray(data.messages) || data.messages.length === 0) return null;
    return { messages: data.messages, context: data.context && typeof data.context === 'object' ? data.context : null };
  } catch {
    return null;
  }
}

// Saves the latest messages (errors are not kept). Storage failures are ignored.
export function saveChat(storage, { messages, context }) {
  try {
    const kept = messages.filter((m) => !m.error).slice(-MAX_SAVED_MESSAGES);
    storage?.setItem(STORAGE_KEY, JSON.stringify({ messages: kept, context }));
  } catch {
    // Full or blocked storage: the chat still works, it just isn't kept.
  }
}
