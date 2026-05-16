import { useEffect, useRef, useState, useCallback } from "react";
import type { KeyboardEvent, ChangeEvent } from "react";
import { sendChatMessage, checkBackendHealth } from "@/services/api";
import type { Message, Session } from "@/types";
import morganAvatar from "@/assets/asistente_morgan.png";

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

function validarCedulaEcuador(cedula: string): boolean {
  if (cedula.length !== 10) return false;
  const prov = parseInt(cedula.substring(0, 2));
  if (prov < 1 || prov > 24) return false;
  const d3 = parseInt(cedula[2]);
  if (d3 > 5) return false;

  const digitos = cedula.split("").map(Number);
  const verificador = digitos.pop();
  let suma = 0;
  for (let i = 0; i < digitos.length; i++) {
    let p = digitos[i];
    if (i % 2 === 0) {
      p *= 2;
      if (p > 9) p -= 9;
    }
    suma += p;
  }
  const residuo = suma % 10;
  const resultado = residuo === 0 ? 0 : 10 - residuo;
  return resultado === verificador;
}

/* ── Sub-components ──────────────────────────────────────────────────────── */

function TypingIndicator() {
  return (
    <div className="typing-indicator">
      <div className="message-avatar assistant">
        <img src={morganAvatar} alt="Morgan" className="avatar-image" />
      </div>
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
        {msg.role === "assistant" ? (
          <img src={morganAvatar} alt="Morgan" className="avatar-image" />
        ) : (
          "👤"
        )}
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
  const [messages, setMessages] = useState<Message[]>(() => {
    const saved = localStorage.getItem("copay_messages");
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Restaurar las fechas de string a objeto Date
        return parsed.map((m: any) => ({ ...m, timestamp: new Date(m.timestamp) }));
      } catch { }
    }
    return [];
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [session, setSession] = useState<Session>(() => {
    const saved = localStorage.getItem("copay_session");
    return saved ? JSON.parse(saved) : { id: null, patientId: null };
  });
  const [backendStatus, setBackendStatus] = useState<"checking" | "online" | "offline">("checking");
  const [location, setLocation] = useState<{ lat: number; lon: number } | null>(null);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  /* Health check */
  useEffect(() => {
    checkBackendHealth().then((ok) =>
      setBackendStatus(ok ? "online" : "offline")
    );

    // Solicitar ubicación al cargar si el navegador lo permite
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLocation({ lat: pos.coords.latitude, lon: pos.coords.longitude });
          console.log("Ubicación obtenida:", pos.coords.latitude, pos.coords.longitude);
        },
        (err) => console.warn("Error de geolocalización:", err.message),
        { enableHighAccuracy: true, timeout: 10000 }
      );
    }
  }, []);

  /* Guardar sesión y mensajes localmente */
  useEffect(() => {
    localStorage.setItem("copay_messages", JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    localStorage.setItem("copay_session", JSON.stringify(session));
  }, [session]);

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
          lat: location?.lat,
          lon: location?.lon,
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

  const resetChat = () => {
    setMessages([]);
    setSession({ id: null, patientId: session.patientId });
    localStorage.removeItem("copay_messages");
  };

  return (
    <>
      <div className="bg-animated" />
      <div className="app-layout">

        {/* Header */}
        <header className="app-header">
          <div className="header-brand">
            <div className="header-logo logo-hidden-overflow">
              <img src={morganAvatar} alt="Morgan" className="avatar-image square" />
            </div>
            <div>
              <div className="header-title">Asistente Morgan</div>
              <div className="header-subtitle">Estimador de copago y cobertura</div>
            </div>
          </div>

          <div className="flex-center-gap">
            {messages.length > 0 && (
              <button
                onClick={resetChat}
                title="Nueva conversación"
                className="new-session-btn"
              >
                Nueva sesión
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

        {/* Patient ID bar (solo visible si hay ID) */}
        {session.patientId && (
          <div className="patient-bar">
            <div className="patient-bar-inner">
              <span className="patient-bar-label">C.I PACIENTE</span>
              <span className="patient-bar-input text-opacity-70">
                {session.patientId}
              </span>
              <span className="patient-bar-badge">✓ Verificado</span>
              <button 
                className="new-session-btn ml-auto"
                onClick={() => setSession({ id: null, patientId: null })}
              >
                Cambiar ID
              </button>
            </div>
          </div>
        )}

        {/* Chat area */}
        <main className="chat-area" id="chat-area">
          {!session.patientId ? (
            <div className="welcome-screen">
              <div className="welcome-icon">🏥</div>
              <h1 className="welcome-title">Bienvenido al Asistente Morgan</h1>
              <p className="welcome-desc">
                Para poder consultar tu cobertura, calcular deducibles y buscar hospitales en red, por favor ingresa tu número de identidad o ID de paciente.
              </p>
              <div className="welcome-login-box">
                <input
                  id="patient-id-input"
                  type="text"
                  inputMode="numeric"
                  className="patient-bar-input welcome-input"
                  placeholder="Ej: 0923847582"
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && e.currentTarget.value.trim()) {
                      setSession((s) => ({ ...s, patientId: e.currentTarget.value.trim() }));
                    }
                  }}
                />
                <button
                  id="patient-id-submit"
                  className="id-submit-btn"
                  onClick={() => {
                    const input = document.getElementById("patient-id-input") as HTMLInputElement;
                    const val = input?.value.trim();
                    if (val) {
                      if (validarCedulaEcuador(val)) {
                        setSession((s) => ({ ...s, patientId: val }));
                      } else {
                        alert("⚠️ Cédula inválida. Por favor ingresa un número de cédula de Ecuador real.");
                      }
                    }
                  }}
                >
                  Continuar →
                </button>
                <p className="input-hint text-center">
                  Escribe tu C.I y presiona <kbd className="kbd-hint">Enter</kbd> o el botón
                </p>
              </div>
            </div>
          ) : messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-icon">👋</div>
              <h1 className="welcome-title">¡Hola! ¿Cómo puedo ayudarte hoy?</h1>
              <p className="welcome-desc">
                Ya tengo tu ID de paciente. Cuéntame tu síntoma o pregunta y te indicaré la especialidad, tu copago y los hospitales de tu red.
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

        {/* Input area (solo visible si hay ID) */}
        {session.patientId && (
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
              Presiona <kbd className="kbd-hint">Enter</kbd> para enviar ·{" "}
              <kbd className="kbd-hint">Shift+Enter</kbd> para salto de línea
            </p>
          </div>
        )}

      </div>
    </>
  );
}
