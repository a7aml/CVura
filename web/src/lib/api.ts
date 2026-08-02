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

class ApiError extends Error {}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...options.headers },
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
