import type { ExtractedJob, Job, ResumeTailorResult, User } from "~lib/types"

const API_BASE_URL = process.env.PLASMO_PUBLIC_API_URL ?? "http://localhost:8000"

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

// Billing/plan limits aren't built yet (Build Order step 8), so the backend
// never actually returns this today — this just lets callers branch on a
// future "plan limit reached" response (402 Payment Required) without
// duplicating that check at every call site.
export function isLimitReachedError(err: unknown): boolean {
  return err instanceof ApiError && err.status === 402
}

export interface ApiRequestMessage {
  type: "API_REQUEST"
  path: string
  method?: string
  body?: string
}

export interface ApiResponseMessage {
  ok: boolean
  status: number
  body: unknown
}

export function isApiRequestMessage(message: unknown): message is ApiRequestMessage {
  return typeof message === "object" && message !== null && (message as Record<string, unknown>).type === "API_REQUEST"
}

// The backend's CORS allowlist only grants cookie-bearing access to the
// extension's own origin (chrome-extension://<id>) — a fetch made from a
// content script instead carries the *host page's* origin (e.g.
// https://job-boards.greenhouse.io), which isn't allow-listed and can't be
// (project_rules.md §3: never widen CORS to "*"). So every caller, popup
// included, relays through this and the background script actually performs
// the fetch — see background/index.ts's onMessage listener.
export async function performApiRequest(message: ApiRequestMessage): Promise<ApiResponseMessage> {
  const response = await fetch(`${API_BASE_URL}${message.path}`, {
    method: message.method,
    body: message.body,
    credentials: "include",
    cache: "no-store",
    headers: { "Content-Type": "application/json" }
  })

  const body = response.status === 204 ? undefined : await response.json().catch(() => ({}))
  return { ok: response.ok, status: response.status, body }
}

async function apiFetch<T>(path: string, options: { method: string; body?: string } = { method: "GET" }): Promise<T> {
  const request: ApiRequestMessage = { type: "API_REQUEST", path, method: options.method, body: options.body }
  const response: ApiResponseMessage = await chrome.runtime.sendMessage(request)

  if (!response.ok) {
    const detail = (response.body as { detail?: string } | undefined)?.detail
    throw new ApiError(detail ?? `Request failed with status ${response.status}`, response.status)
  }
  return response.body as T
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

export function analyzeJob(jobId: string): Promise<Job> {
  return apiFetch<Job>(`/jobs/${jobId}/analyze`, { method: "POST" })
}

export function tailorResume(jobId: string): Promise<ResumeTailorResult> {
  return apiFetch<ResumeTailorResult>(`/jobs/${jobId}/tailor`, { method: "POST" })
}
