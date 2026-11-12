// Boundary (UI): floating "Budget Match Assistant" chat for the React app.
//
// Rendered once in App.jsx for visitors and customers. It calls POST /api/chat
// (vite.config.js proxies /api to Flask in development). When onOpenProject is
// given, clicking a card opens that project inside the React app.
import { useEffect, useRef, useState } from "react";
import "./ChatWidget.css";
import { describePrefs, loadChat, saveChat } from "../utils/chat.js";

const API_URL = import.meta.env.VITE_API_URL ?? "/api";
const MAX_LENGTH = 500;
const money = (n) => "$" + Number(n).toLocaleString();
const signedMoney = (n) => (n === 0 ? "on budget" : `${n > 0 ? "+" : "−"}${money(Math.abs(n))}`);
const GREETING = {
  role: "assistant",
  greeting: true,
  content: 'Hi! Tell me about your project and budget, for example "modern kitchen around $10,000".',
};

function sessionStorageOrNull() {
  try {
    return window.sessionStorage;
  } catch {
    return null; // blocked storage (private mode, sandboxed frame)
  }
}

export default function ChatWidget({ onOpenProject }) {
  const saved = useRef(loadChat(sessionStorageOrNull())).current;
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState(saved?.messages ?? [GREETING]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  // What the server understood so far; sent back so the next message builds on it.
  const [context, setContext] = useState(saved?.context ?? null);
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const launcherRef = useRef(null);
  const wasOpen = useRef(false);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Keep the conversation for this browser tab, so a reload or page change doesn't lose it.
  useEffect(() => {
    saveChat(sessionStorageOrNull(), { messages, context });
  }, [messages, context]);

  // Focus the box when the chat opens, and give focus back to the launcher when it closes.
  useEffect(() => {
    if (open) inputRef.current?.focus();
    else if (wasOpen.current) launcherRef.current?.focus();
    wasOpen.current = open;
  }, [open]);

  function startOver() {
    setContext(null);
    setMessages([GREETING]);
    inputRef.current?.focus();
  }

  function send(e) {
    e.preventDefault();
    ask(text.trim());
  }

  // Sends one message: typed in the box, or a follow-up chip.
  async function ask(message) {
    if (!message || loading) return;
    const history = messages
      .filter((m) => !m.greeting && !m.error)
      .map(({ role, content }) => ({ role, content }));
    setMessages((prev) => [...prev, { role: "user", content: message }]);
    setText("");
    setLoading(true);
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ message, history, context }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Something went wrong.");
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant", content: data.reply, projects: data.projects, comparison: data.comparison,
          suggestions: data.suggestions, fallback: data.source === "fallback",
        },
      ]);
      setContext(data.prefs ?? null);
    } catch (err) {
      const content = err instanceof TypeError ? "Can't reach the server. Please try again." : err.message;
      setMessages((prev) => [...prev, { role: "assistant", content, error: true }]);
    } finally {
      setLoading(false);
    }
  }

  function openCard(e, id) {
    if (!onOpenProject) return;
    e.preventDefault();
    setOpen(false);
    onOpenProject(id);
  }

  if (!open) {
    return (
      <button ref={launcherRef} className="cw-launcher" onClick={() => setOpen(true)} aria-label="Open budget assistant">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z" />
        </svg>
        <span>Find by budget</span>
      </button>
    );
  }

  return (
    <div
      className="cw-panel"
      role="dialog"
      aria-label="Budget Match Assistant"
      onKeyDown={(e) => e.key === "Escape" && setOpen(false)}
    >
      <header className="cw-header">
        <span>
          Budget Match Assistant
          <small>Projects that fit your budget</small>
        </span>
        <button onClick={() => setOpen(false)} aria-label="Close">×</button>
      </header>
      {describePrefs(context) && (
        <div className="cw-memory">
          <span>Looking for: {describePrefs(context)}</span>
          <button type="button" onClick={startOver}>Start over</button>
        </div>
      )}

      <div className="cw-messages" aria-live="polite">
        {messages.map((m, i) => (
          <div key={i} className={`cw-msg cw-${m.role}${m.error ? " cw-error" : ""}`}>
            <p>{m.content}</p>
            {m.fallback && <small className="cw-note">Answered without the AI service.</small>}
            {m.comparison?.length > 0 && <ComparisonTable rows={m.comparison} onOpen={openCard} />}
            {m.projects?.length > 0 && (
              <div className="cw-cards">
                {m.projects.map((p) => (
                  // Every value on the card comes from the database, never from the AI text.
                  <a
                    key={p.id}
                    className="cw-card"
                    href={`#/projects/${p.id}`}
                    onClick={(e) => openCard(e, p.id)}
                  >
                    <img src={p.image} alt="" onError={(e) => (e.currentTarget.style.display = "none")} />
                    <span className="cw-label">{p.label}</span>
                    <strong>{p.title}</strong>
                    <span>{money(p.budget)} · {p.category}</span>
                    <small>{p.designer}</small>
                    {p.reasons?.length > 0 && (
                      <span className="cw-reasons" aria-label="Why this matches">
                        {p.reasons.map((r) => <span key={r}>{r}</span>)}
                      </span>
                    )}
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
        {!loading && messages.at(-1)?.suggestions?.length > 0 && (
          <div className="cw-chips" aria-label="Suggested replies">
            {messages.at(-1).suggestions.map((chip) => (
              <button key={chip} type="button" className="cw-chip" onClick={() => ask(chip)}>{chip}</button>
            ))}
          </div>
        )}
        {loading && <div className="cw-msg cw-assistant cw-typing">Thinking…</div>}
        <div ref={endRef} />
      </div>

      <form className="cw-form" onSubmit={send}>
        <input
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={MAX_LENGTH}
          placeholder="Describe your project and budget"
          aria-label="Message"
        />
        <button disabled={loading || !text.trim()}>Send</button>
      </form>
    </div>
  );
}

// Side-by-side facts from the database for "compare #12 and #15" / "Compare these".
function ComparisonTable({ rows, onOpen }) {
  const facts = [
    ["Price", (r) => money(r.budget)],
    ["vs budget", (r) => (r.vs_budget == null ? "–" : signedMoney(r.vs_budget))],
    ["Room", (r) => r.category],
    ["Style", (r) => r.styles.join(", ") || "–"],
    ["Property", (r) => r.property_type || "–"],
    ["Designer", (r) => r.designer],
    ["Saves", (r) => r.saves],
    ["Views", (r) => r.views],
  ];
  return (
    <div className="cw-compare">
      <table>
        <thead>
          <tr>
            <th scope="col"><span className="cw-sr">Fact</span></th>
            {rows.map((r) => (
              <th key={r.id} scope="col"><a href={`#/projects/${r.id}`} onClick={(e) => onOpen(e, r.id)}>{r.title}</a></th>
            ))}
          </tr>
        </thead>
        <tbody>
          {facts.map(([label, value]) => (
            <tr key={label}>
              <th scope="row">{label}</th>
              {rows.map((r) => <td key={r.id}>{value(r)}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
