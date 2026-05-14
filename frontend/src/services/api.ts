/**
 * API service — all calls to the FastAPI backend.
 * Base URL is empty in dev (Vite proxies /v1 and /health → :8000).
 */

const BASE = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { Accept: "application/json" },
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ChatRequest {
  message: string;
  session_id?: string | null;
  patient_id?: string | null;
}

export interface ChatResponse {
  response: string;
  session_id: string | null;
}

export interface EstimateRequest {
  patient_id: string;
  symptom: string;
  costo_estimado?: number | null;
}

export interface HospitalInfo {
  hospital_id: string;
  nombre: string;
  ciudad: string;
  nivel: string;
  especialidades: string[];
  en_red: boolean;
}

export interface EstimateResponse {
  especialidad_sugerida: string | null;
  patient: {
    patient_id: string | null;
    nombre: string | null;
    plan_id: string | null;
    plan_nombre: string | null;
    deducible_anual: number | null;
    deducible_cubierto: number | null;
    copago_base: number | null;
  } | null;
  monto_copago: number | null;
  copago_info: Record<string, unknown> | null;
  hospitales: HospitalInfo[];
  error: string | null;
}

// ── API calls ─────────────────────────────────────────────────────────────────

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const data = await getJson<{ status?: string }>("/health");
    return data.status === "ok";
  } catch {
    return false;
  }
}

export async function sendChatMessage(req: ChatRequest): Promise<ChatResponse> {
  return postJson<ChatResponse>("/v1/chat/", req);
}

export async function getEstimate(req: EstimateRequest): Promise<EstimateResponse> {
  return postJson<EstimateResponse>("/v1/estimate/", req);
}
