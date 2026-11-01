import type { Card, CardPage, Collection, Dashboard, Preferences, User } from "./types";

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public details?: unknown) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api/v1${path}`, {
      credentials: "same-origin",
      ...init,
      headers: { "Content-Type": "application/json", ...(init.headers || {}) },
    });
  } catch {
    throw new ApiError(0, "network_error", "Can't reach the server. Check your connection and try again.");
  }
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => null);
  if (!res.ok) {
    const err = body?.error;
    let message: string = err?.message || `Request failed (${res.status})`;
    if (err?.code === "validation_error" && Array.isArray(err.details) && err.details[0]?.msg) {
      message = String(err.details[0].msg).replace(/^Value error, /, "");
    }
    if (res.status === 401 && typeof window !== "undefined" && !path.startsWith("/auth/")) {
      window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
    }
    throw new ApiError(res.status, err?.code || "http_error", message, err?.details);
  }
  return body as T;
}

const json = (data: unknown) => JSON.stringify(data);

export const api = {
  register: (email: string, password: string, display_name: string) =>
    request<User>("/auth/register", { method: "POST", body: json({ email, password, display_name }) }),
  login: (email: string, password: string) =>
    request<User>("/auth/login", { method: "POST", body: json({ email, password }) }),
  logout: () => request<void>("/auth/logout", { method: "POST" }),
  me: () => request<User>("/users/me"),
  updatePreferences: (patch: Partial<Preferences>) =>
    request<Preferences>("/users/me/preferences", { method: "PATCH", body: json(patch) }),
  deleteAccount: () => request<void>("/users/me", { method: "DELETE" }),

  dashboard: () => request<Dashboard>("/analytics/dashboard"),

  listCards: (params: Record<string, string | number | undefined>) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => v !== undefined && v !== "" && qs.set(k, String(v)));
    return request<CardPage>(`/vocabulary?${qs}`);
  },
  createCard: (data: unknown) => request<Card>("/vocabulary", { method: "POST", body: json(data) }),
  updateCard: (id: string, data: unknown) => request<Card>(`/vocabulary/${id}`, { method: "PUT", body: json(data) }),
  deleteCard: (id: string) => request<void>(`/vocabulary/${id}`, { method: "DELETE" }),

  collections: () => request<Collection[]>("/collections"),
  createCollection: (name: string, description?: string) =>
    request<Collection>("/collections", { method: "POST", body: json({ name, description }) }),
};
