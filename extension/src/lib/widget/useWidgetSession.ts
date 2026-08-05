import { useEffect, useState } from "react"

import { checkSession } from "~lib/auth"
import type { User } from "~lib/types"

// Re-checks auth on every new posting (not just once on mount) — the user
// could log in on the website in another tab while this widget stays open.
export function useWidgetSession(postingUrl: string | null): User | null | "loading" {
  const [user, setUser] = useState<User | null | "loading">("loading")

  useEffect(() => {
    if (!postingUrl) return
    let cancelled = false
    setUser("loading")
    checkSession().then((restoredUser) => {
      if (!cancelled) setUser(restoredUser)
    })
    return () => {
      cancelled = true
    }
  }, [postingUrl])

  return user
}
