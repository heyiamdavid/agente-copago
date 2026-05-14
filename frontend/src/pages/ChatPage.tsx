import { useEffect, useRef, useState, useCallback } from "react";
import type { KeyboardEvent, ChangeEvent } from "react";
import { sendChatMessage, checkBackendHealth } from "@/services/api";
import type { Message, Session } from "@/types";

/* ── Tiny helpers ─────────────────────────────────────────────────────────── */

function formatTime(d: Date) {
  return d.toLocaleTimeString("es", { hour: "2-digit", minute: "2-digit" });
}

const QUICK_CHIPS = [
  "Tengo dolor de cabeza fuerte",
  "Me duele el pecho y me falta el aire",
  "¿Cuánto pago si voy al cardiólogo?",
  "Tengo fiebre y tos desde hace 3 días",
  "¿Qué hospitales están en mi red?",
  "Dolor de rodilla, posible fractura",
];

/* ── Sub-components ──────────────────────────────────────────────────────── */

function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <div className="message-avatar assistant">🤖</div>
      <div className="typing-bubble">
        <div className="typing-dot" />
        <div className="typing-dot" />
        <div className="typing-dot" />
      </div>
    </div>
  );
}

interface MessageBubbleProps {
  msg: Message;
}

function MessageBubble({ msg }: MessageBubbleProps) {
  return (
    <div className={`message-wrapper ${msg.role}`}>
      <div className={`message-avatar ${msg.role}`}>
        {msg.role === "assistant" ? "🤖" : "👤"}
      </div>
      <div>
        <div className={`message-bubble ${msg.role}`}>{msg.content}</div>
        <div className="message-time">{formatTime(msg.timestamp)}</div>
      </div>
    </div>
  );
}

/* ── Main component ──────────────────────────────────────────────────────── */

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState<Session>({ id: null, patientId: null });
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  /* Health check */
  useEffect(() => {
    checkBackendHealth().then((ok) =>
      setBackendStatus(ok ? "online" : "offline")
    );
  }, []);

  /* Auto-scroll */
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  /* Auto-resize textarea */
  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 140)}px`;
  };

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || loading) return;

      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content: trimmed,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setInput("");
      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
      setLoading(true);

      try {
        const res = await sendChatMessage({
          message: trimmed,
          session_id: session.id,
          patient_id: session.patientId || undefined,
        });

        const botMsg: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: res.response,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, botMsg]);
        if (res.session_id) {
          setSession((s) => ({ ...s, id: res.session_id }));
        }
      } catch (err) {
        const errMsg: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `⚠️ Error al conectar con el servidor: ${err instanceof Error ? err.message : String(err)}`,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errMsg]);
      } finally {
        setLoading(false);
      }
    },
    [loading, session]
  );

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  };

  const handlePatientIdChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSession((s) => ({ ...s, patientId: e.target.value || null }));
  };

  const resetChat = () => {
    setMessages([]);
    setSession({ id: null, patientId: session.patientId });
  };

  return (
    <>
      <div className="bg-animated" />
      <div className="app-layout">

        {/* Header */}
        <header className="app-header">
          <div className="header-brand">
            <div className="header-logo">🏥</div>
            <div>
              <div className="header-title">Asistente Morgan</div>
              <div className="header-subtitle">Estimador de copago y cobertura</div>
            </div>
          </div>

          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            {messages.length > 0 && (
              <button
                onClick={resetChat}
                title="Nueva conversación"
                style={{
                  background: "var(--bg-card)",
                  border: "1px solid var(--border-subtle)",
                  borderRadius: "var(--radius-md)",
                  color: "var(--text-secondary)",
                  padding: "0.4rem 0.75rem",
                  cursor: "pointer",
                  fontSize: "0.75rem",
                  fontFamily: "inherit",
                  transition: "var(--transition)",
                }}
              >
                🔄 Nueva sesión
              </button>
            )}
            <div className="header-status">
              <div
                className={`status-dot ${backendStatus === "online"
                    ? "online"
                    : backendStatus === "offline"
                      ? "offline"
                      : ""
                  }`}
              />
              {backendStatus === "checking"
                ? "Verificando…"
                : backendStatus === "online"
                  ? "Servidor en línea"
                  : "Servidor no disponible"}
            </div>
          </div>
        </header>

        {/* Patient ID bar */}
        <div className="patient-bar">
          <div className="patient-bar-inner">
            <span className="patient-bar-icon">🪪</span>
            <span className="patient-bar-label">ID Paciente</span>
            <input
              id="patient-id-input"
              type="text"
              className="patient-bar-input"
              placeholder="Ingresa tu ID de paciente (opcional)"
              value={session.patientId ?? ""}
              onChange={handlePatientIdChange}
              autoComplete="off"
            />
            {session.patientId && (
              <span className="patient-bar-badge">✓ Guardado</span>
            )}
          </div>
        </div>

        {/* Chat area */}
        <main className="chat-area" id="chat-area">
          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-icon">🏥</div>
              <h1 className="welcome-title">¿Cómo puedo ayudarte hoy?</h1>
              <p className="welcome-desc">
                Cuéntame tu síntoma y te indicaré la especialidad adecuada,
                cuánto será tu copago exacto y qué hospital de tu red te
                conviene más.
              </p>
              <div className="welcome-chips">
                {QUICK_CHIPS.map((chip) => (
                  <button
                    key={chip}
                    className="chip"
                    onClick={() => send(chip)}
                    id={`chip-${chip.slice(0, 20).replace(/\s/g, "-").toLowerCase()}`}
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <MessageBubble key={msg.id} msg={msg} />
              ))}
              {loading && <TypingIndicator />}
            </>
          )}
          <div ref={bottomRef} />
        </main>

        {/* Input area */}
        <div className="input-area">
          <div className="input-container">
            <textarea
              ref={textareaRef}
              id="chat-input"
              className="message-input"
              placeholder="Describe tu síntoma o pregunta sobre tu cobertura…"
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              rows={1}
              disabled={loading}
            />
            <button
              id="send-btn"
              className="send-btn"
              onClick={() => send(input)}
              disabled={!input.trim() || loading}
              title="Enviar (Enter)"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
            </button>
          </div>
          <p className="input-hint">
            Presiona <kbd style={{ fontFamily: "monospace", opacity: 0.7 }}>Enter</kbd> para enviar ·{" "}
            <kbd style={{ fontFamily: "monospace", opacity: 0.7 }}>Shift+Enter</kbd> para salto de línea
          </p>
        </div>

      </div>
    </>
  );
}
