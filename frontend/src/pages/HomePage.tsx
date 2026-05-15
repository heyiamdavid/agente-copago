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
    <main className="home-page-main">
      <h1 className="home-page-title">
        Estimador de copago y cobertura
      </h1>
      <p className="home-page-desc">
        Describe tu síntoma y conectaremos con tu plan para estimar copago y hospital en red.
      </p>
      <p className="home-page-status">
        Backend:{" "}
        {backendOk === null && "comprobando…"}
        {backendOk === true && "en línea"}
        {backendOk === false && "no disponible (¿uvicorn en :8000?)"}
      </p>
    </main>
  );
}
