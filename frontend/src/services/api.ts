const base =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "") ?? "";

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${base}${path}`, { headers: { Accept: "application/json" } });
  if (!res.ok) throw new Error(`${res.status}`);
  return res.json() as Promise<T>;
}

export async function checkBackendHealth(): Promise<boolean> {
  try {
    const data = await getJson<{ status?: string }>("/health");
    return data.status === "ok";
  } catch {
    return false;
  }
}
