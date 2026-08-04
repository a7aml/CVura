import type {
  Award,
  Certification,
  Education,
  Experience,
  FullProfile,
  Language,
  Profile,
  ProfileFields,
  Project,
  Skill,
  User,
} from "./types"

const API_BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

async function apiFetch<T>(path: string, options: RequestInit = {}, timeoutMs?: number): Promise<T> {
  // FormData bodies (file uploads) must let the browser set their own
  // multipart boundary in Content-Type — forcing application/json here
  // would break the upload.
  const isFormData = options.body instanceof FormData
  const controller = timeoutMs ? new AbortController() : undefined
  const timeoutId = controller ? window.setTimeout(() => controller.abort(), timeoutMs) : undefined

  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      credentials: "include",
      cache: "no-store",
      headers: isFormData ? options.headers : { "Content-Type": "application/json", ...options.headers },
      signal: controller?.signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError("This is taking longer than expected. Please try again.", 0)
    }
    throw err
  } finally {
    if (timeoutId) window.clearTimeout(timeoutId)
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    throw new ApiError(body.detail ?? `Request failed with status ${response.status}`, response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }
  return response.json()
}

// --- auth ---

export function signup(email: string, password: string): Promise<User> {
  return apiFetch<User>("/auth/signup", { method: "POST", body: JSON.stringify({ email, password }) })
}

export function login(email: string, password: string): Promise<User> {
  return apiFetch<User>("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) })
}

export function loginWithGoogle(idToken: string): Promise<User> {
  return apiFetch<User>("/auth/google", { method: "POST", body: JSON.stringify({ id_token: idToken }) })
}

export function logout(): Promise<void> {
  return apiFetch<void>("/auth/logout", { method: "POST" })
}

export function refreshSession(): Promise<User> {
  return apiFetch<User>("/auth/refresh", { method: "POST" })
}

// --- profile core ---

export function getProfile(): Promise<FullProfile> {
  return apiFetch<FullProfile>("/profile")
}

export function createProfile(data: ProfileFields): Promise<Profile> {
  return apiFetch<Profile>("/profile", { method: "POST", body: JSON.stringify(data) })
}

export function updateProfile(data: Partial<ProfileFields>): Promise<Profile> {
  return apiFetch<Profile>("/profile", { method: "PATCH", body: JSON.stringify(data) })
}

const IMPORT_RESUME_TIMEOUT_MS = 60_000

export function importResumeProfile(file: File, replaceExisting = false): Promise<FullProfile> {
  const formData = new FormData()
  formData.append("file", file)
  formData.append("replace_existing", String(replaceExisting))
  return apiFetch<FullProfile>(
    "/profile/import-resume",
    { method: "POST", body: formData },
    IMPORT_RESUME_TIMEOUT_MS
  )
}

// --- repeatable sections ---

function sectionApi<TIn, TOut>(path: string) {
  return {
    add: (data: TIn) =>
      apiFetch<TOut>(`/profile/${path}`, { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: TIn) =>
      apiFetch<TOut>(`/profile/${path}/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
    remove: (id: string) => apiFetch<void>(`/profile/${path}/${id}`, { method: "DELETE" }),
  }
}

export const educationApi = sectionApi<Omit<Education, "id">, Education>("education")
export const experienceApi = sectionApi<Omit<Experience, "id">, Experience>("experiences")
export const projectApi = sectionApi<Omit<Project, "id">, Project>("projects")
export const skillApi = sectionApi<Omit<Skill, "id">, Skill>("skills")
export const certificationApi = sectionApi<Omit<Certification, "id">, Certification>("certifications")
export const languageApi = sectionApi<Omit<Language, "id">, Language>("languages")
export const awardApi = sectionApi<Omit<Award, "id">, Award>("awards")
