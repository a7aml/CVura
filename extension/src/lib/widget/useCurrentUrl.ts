import { useEffect, useState } from "react"

// LinkedIn/Greenhouse/Lever are client-routed SPAs, so a job page can appear
// or disappear (e.g. LinkedIn's feed <-> job view) without the content script
// being re-injected. Polling location.href is simpler and safer here than
// monkey-patching history.pushState on a third-party page.
export function useCurrentUrl(pollMs = 800): string {
  const [href, setHref] = useState(location.href)

  useEffect(() => {
    const id = window.setInterval(() => {
      setHref((prev) => (prev === location.href ? prev : location.href))
    }, pollMs)
    return () => window.clearInterval(id)
  }, [pollMs])

  return href
}
