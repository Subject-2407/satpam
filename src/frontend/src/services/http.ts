// HTTP client tipis untuk backend SATPAM.
// Menangani base URL, header Authorization, parsing JSON, dan error standar FastAPI.

const ENV_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
export const API_BASE_URL = ENV_BASE && ENV_BASE.length > 0 ? ENV_BASE.replace(/\/$/, "") : "http://localhost:8000";

const TOKEN_KEY = "satpam.token";

let inMemoryToken: string | null = null;
let onUnauthorized: (() => void) | null = null;

export function getToken(): string | null {
  if (inMemoryToken) return inMemoryToken;
  try {
    inMemoryToken = localStorage.getItem(TOKEN_KEY);
  } catch {
    inMemoryToken = null;
  }
  return inMemoryToken;
}

export function setToken(token: string | null) {
  inMemoryToken = token;
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* localStorage tidak tersedia — abaikan */
  }
}

export function setOnUnauthorized(handler: (() => void) | null) {
  onUnauthorized = handler;
}

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

// Ekstrak pesan error yang ramah dari berbagai bentuk `detail` FastAPI.
function extractMessage(status: number, payload: unknown): string {
  if (payload && typeof payload === "object" && "detail" in payload) {
    const detail = (payload as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      const first = detail[0] as { msg?: string; loc?: unknown[] } | undefined;
      if (first?.msg) return first.msg;
    }
    if (detail && typeof detail === "object" && "message" in detail) {
      return String((detail as { message: unknown }).message);
    }
  }
  if (status === 401) return "Sesi tidak valid atau sudah berakhir. Silakan login ulang.";
  if (status === 403) return "Role Anda tidak memiliki akses untuk aksi ini.";
  if (status === 404) return "Data tidak ditemukan.";
  if (status === 503) return "Database (Neo4j) tidak tersedia.";
  return `Permintaan gagal (HTTP ${status}).`;
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  // body sudah berupa string/URLSearchParams (mis. form login)
  rawBody?: BodyInit;
  headers?: Record<string, string>;
  // jika true, parse response sebagai text (mis. export markdown)
  asText?: boolean;
  signal?: AbortSignal;
}

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = "GET", body, rawBody, headers = {}, asText = false, signal } = options;
  const token = getToken();

  const finalHeaders: Record<string, string> = { ...headers };
  if (token) finalHeaders.Authorization = `Bearer ${token}`;

  let payload: BodyInit | undefined;
  if (rawBody !== undefined) {
    payload = rawBody;
  } else if (body !== undefined) {
    finalHeaders["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, { method, headers: finalHeaders, body: payload, signal });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") throw err;
    throw new ApiError(0, `Tidak dapat terhubung ke backend (${API_BASE_URL}). Pastikan server berjalan.`);
  }

  if (res.status === 401) {
    setToken(null);
    onUnauthorized?.();
  }

  if (!res.ok) {
    let errPayload: unknown = null;
    try {
      errPayload = await res.json();
    } catch {
      /* body bukan JSON */
    }
    throw new ApiError(res.status, extractMessage(res.status, errPayload), errPayload);
  }

  if (asText) return (await res.text()) as unknown as T;

  if (res.status === 204) return undefined as unknown as T;
  const text = await res.text();
  if (!text) return undefined as unknown as T;
  return JSON.parse(text) as T;
}

export const http = {
  get: <T>(path: string, signal?: AbortSignal) => request<T>(path, { signal }),
  getText: (path: string, signal?: AbortSignal) => request<string>(path, { asText: true, signal }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: "POST", body }),
  postForm: <T>(path: string, form: URLSearchParams) =>
    request<T>(path, {
      method: "POST",
      rawBody: form,
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: "PATCH", body }),
  del: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};

// Helper bangun query string (hanya nilai terdefinisi & non-kosong).
export function qs(params: object): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params as Record<string, unknown>)) {
    if (value !== undefined && value !== null && value !== "") search.append(key, String(value));
  }
  const str = search.toString();
  return str ? `?${str}` : "";
}
