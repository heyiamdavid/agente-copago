import { useEffect, useState } from "react";
import { checkBackendHealth } from "@/services/api";

export function HomePage() {
  const [backendOk, setBackendOk] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    checkBackendHealth()
      .then((ok) => {
        if (!cancelled) setBackendOk(ok);
      })
      .catch(() => {
        if (!cancelled) setBackendOk(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main style={{ maxWidth: 720, margin: "0 auto", padding: "2rem 1rem" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700 }}>
        Estimador de copago y cobertura
      </h1>
      <p style={{ color: "#475569" }}>
        Describe tu síntoma y conectaremos con tu plan para estimar copago y hospital en red.
      </p>
      <p style={{ fontSize: "0.875rem", color: "#64748b" }}>
        Backend:{" "}
        {backendOk === null && "comprobando…"}
        {backendOk === true && "en línea"}
        {backendOk === false && "no disponible (¿uvicorn en :8000?)"}
      </p>
    </main>
  );
}
