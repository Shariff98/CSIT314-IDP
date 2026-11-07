// Boundary (UI): floating "Budget Match Assistant" chat for the React app.
//
// Rendered once in App.jsx for visitors and customers. It calls POST /api/chat
// (vite.config.js proxies /api to Flask in development). When onOpenProject is
// given, clicking a card opens that project inside the React app.
import { useEffect, useRef, useState } from "react";
import "./ChatWidget.css";
import { describePrefs } from "../utils/chat.js";

const API_URL = import.meta.env.VITE_API_URL ?? "/api";
const MAX_LENGTH = 500;
const money = (n) => "$" + Number(n).toLocaleString();
const GREETING = {
  role: "assistant",
  content: 'Hi! Tell me about your project and budget, for example "modern kitchen around $10,000".',
};

export default function ChatWidget({ onOpenProject }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([GREETING]);
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  // What the server understood so far; sent back so the next message builds on it.
  const [context, setContext] = useState(null);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function send(e) {
    e.preventDefault();
    const message = text.trim();
    if (!message || loading) return;
    const history = messages
      .filter((m) => m !== GREETING && !m.error)
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
        { role: "assistant", content: data.reply, projects: data.projects, fallback: data.source === "fallback" },
      ]);
      setContext(data.prefs ?? null);
    } catch (err) {
      const content = err instanceof TypeError ? "Can't reach the server. Please try again." : err.message;
      setMessages((prev) => [...prev, { role: "assistant", content, error: true }]);
    } finally {
      setLoading(false);
    }
  }

  if (!open) {
    return (
      <button className="cw-launcher" onClick={() => setOpen(true)} aria-label="Open budget assistant">
        💬
      </button>
    );
  }

  return (
    <div className="cw-panel" role="dialog" aria-label="Budget Match Assistant">
      <header className="cw-header">
        <span>Budget Match Assistant</span>
        <button onClick={() => setOpen(false)} aria-label="Close">×</button>
      </header>
      {describePrefs(context) && (
        <div className="cw-memory">
          <span>Looking for: {describePrefs(context)}</span>
          <button type="button" onClick={() => setContext(null)}>Start over</button>
        </div>
      )}

      <div className="cw-messages">
        {messages.map((m, i) => (
          <div key={i} className={`cw-msg cw-${m.role}${m.error ? " cw-error" : ""}`}>
            <p>{m.content}</p>
            {m.fallback && <small className="cw-note">Answered without the AI service.</small>}
            {m.projects?.length > 0 && (
              <div className="cw-cards">
                {m.projects.map((p) => (
                  // Every value on the card comes from the database, never from the AI text.
                  <a
                    key={p.id}
                    className="cw-card"
                    href={p.url}
                    onClick={(e) => {
                      if (!onOpenProject) return;
                      e.preventDefault();
                      setOpen(false);
                      onOpenProject(p.id);
                    }}
                  >
                    <img src={p.image} alt="" onError={(e) => (e.currentTarget.style.display = "none")} />
                    <span className="cw-label">{p.label}</span>
                    <strong>{p.title}</strong>
                    <span>{money(p.budget)} · {p.category}</span>
                    <small>{p.designer}</small>
                  </a>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="cw-msg cw-assistant cw-typing">Thinking…</div>}
        <div ref={endRef} />
      </div>

      <form className="cw-form" onSubmit={send}>
        <input
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
