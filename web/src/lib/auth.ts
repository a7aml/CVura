import { refreshSession } from "./api"
import type { User } from "./types"

const GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"

// Cookies are HttpOnly, so this is the only way to know if a session is
// still valid — it also silently renews the access token if so.
export async function checkSession(): Promise<User | null> {
  try {
    return await refreshSession()
  } catch {
    return null
  }
}

// Websites can't use chrome.identity (extension-only API), so sign-in is a
// plain full-page redirect requesting an id_token via the implicit flow,
// landing back on our own /app/auth/callback route.
export function redirectToGoogleSignIn(): void {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
  if (!clientId) {
    throw new Error("Missing VITE_GOOGLE_CLIENT_ID")
  }

  const redirectUri = `${window.location.origin}/app/auth/callback`
  const authUrl = new URL(GOOGLE_AUTH_ENDPOINT)
  authUrl.searchParams.set("client_id", clientId)
  authUrl.searchParams.set("response_type", "id_token")
  authUrl.searchParams.set("redirect_uri", redirectUri)
  authUrl.searchParams.set("scope", "openid email")
  authUrl.searchParams.set("nonce", crypto.randomUUID())

  window.location.href = authUrl.toString()
}

export function extractIdTokenFromCallback(): string | null {
  const hash = window.location.hash.replace(/^#/, "")
  return new URLSearchParams(hash).get("id_token")
}
