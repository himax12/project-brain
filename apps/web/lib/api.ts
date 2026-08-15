export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const base = process.env.API_URL || "http://127.0.0.1:8000";
  const key = process.env.API_KEY || "dev-local-key-change-me";
  const res = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      "X-API-Key": key,
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  const text = await res.text();
  let data: unknown = text;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { raw: text };
  }
  if (!res.ok) {
    const err = new Error(`API ${res.status}`);
    (err as Error & { payload?: unknown }).payload = data;
    throw err;
  }
  return data as T;
}

export function qs(org: string, repo: string, extra: Record<string, string> = {}) {
  const p = new URLSearchParams({ org_id: org, repo_id: repo, ...extra });
  return p.toString();
}
