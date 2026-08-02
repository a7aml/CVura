import { refreshSession } from "~lib/api"
import type { User } from "~lib/types"

// Cookies are HttpOnly, so there's no client-readable "am I logged in" flag —
// the only way to know is to ask the backend, which also silently renews the
// access token from the refresh cookie if the session is still valid.
export async function checkSession(): Promise<User | null> {
  try {
    return await refreshSession()
  } catch {
    return null
  }
}
