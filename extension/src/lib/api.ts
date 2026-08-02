import type { ExtractedJob, Job, User } from "~lib/types"

const API_BASE_URL = process.env.PLASMO_PUBLIC_API_URL ?? "http://localhost:8000"

class ApiError extends Error {}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...options.headers }
  })

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail ?? `Request failed with status ${response.status}`)
  }

  if (response.status === 204) {
    return undefined as T
  }
  return response.json()
}

export function logout(): Promise<void> {
  return apiFetch<void>("/auth/logout", { method: "POST" })
}

export function refreshSession(): Promise<User> {
  return apiFetch<User>("/auth/refresh", { method: "POST" })
}

// --- jobs ---

export function createJob(data: ExtractedJob): Promise<Job> {
  return apiFetch<Job>("/jobs", { method: "POST", body: JSON.stringify(data) })
}
