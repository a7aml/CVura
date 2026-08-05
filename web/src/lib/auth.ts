import { refreshSession } from "./api"
import type { User } from "./types"

const GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"

// sessionStorage (not a cookie) so the value never leaves this tab/browser
// and can't be replayed across sessions.
const NONCE_STORAGE_KEY = "google_oauth_nonce"

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
// landing back on our own /app/auth/callback route. The nonce generated
// here is stored locally and checked against the returned token's `nonce`
// claim in extractIdTokenFromCallback — without that check, this callback
// route would accept *any* valid Google id_token placed in its URL
// fragment, letting an attacker craft a link that logs a victim into the
// attacker's own account (login CSRF).
export function redirectToGoogleSignIn(): void {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
  if (!clientId) {
    throw new Error("Missing VITE_GOOGLE_CLIENT_ID")
  }

  const nonce = crypto.randomUUID()
  sessionStorage.setItem(NONCE_STORAGE_KEY, nonce)

  const redirectUri = `${window.location.origin}/app/auth/callback`
  const authUrl = new URL(GOOGLE_AUTH_ENDPOINT)
  authUrl.searchParams.set("client_id", clientId)
  authUrl.searchParams.set("response_type", "id_token")
  authUrl.searchParams.set("redirect_uri", redirectUri)
  authUrl.searchParams.set("scope", "openid email")
  authUrl.searchParams.set("nonce", nonce)

  window.location.href = authUrl.toString()
}

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const base64Url = token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")
    const padded = base64Url.padEnd(base64Url.length + ((4 - (base64Url.length % 4)) % 4), "=")
    return JSON.parse(atob(padded))
  } catch {
    return null
  }
}

// Single-use: the stored nonce is consumed (removed) on first check, so a
// token can't be re-verified against a stale value on a later page load.
function consumesMatchingNonce(idToken: string): boolean {
  const expected = sessionStorage.getItem(NONCE_STORAGE_KEY)
  sessionStorage.removeItem(NONCE_STORAGE_KEY)
  if (!expected) return false

  const payload = decodeJwtPayload(idToken)
  return payload?.nonce === expected
}

export function extractIdTokenFromCallback(): string | null {
  const hash = window.location.hash.replace(/^#/, "")
  const idToken = new URLSearchParams(hash).get("id_token")
  if (!idToken || !consumesMatchingNonce(idToken)) {
    return null
  }
  return idToken
}
