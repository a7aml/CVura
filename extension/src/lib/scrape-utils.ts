// Generic, board-agnostic DOM/JSON-LD helpers shared by the content scripts
// in `contents/`. Board-specific selectors and parsing stay in each board's
// own file — only truly shared plumbing belongs here.

export function queryText(selectors: string[]): string | null {
  for (const selector of selectors) {
    const text = document.querySelector(selector)?.textContent?.trim()
    if (text) return text
  }
  return null
}

// Job board detail pages are frequently client-rendered, so a content script
// injected at document_idle can still run before the target elements exist.
// Poll via MutationObserver instead of a fixed sleep.
export function waitForElement(selectors: string[], timeoutMs = 8000): Promise<void> {
  return new Promise((resolve) => {
    if (queryText(selectors)) {
      resolve()
      return
    }

    const observer = new MutationObserver(() => {
      if (queryText(selectors)) {
        observer.disconnect()
        clearTimeout(timer)
        resolve()
      }
    })
    observer.observe(document.body, { childList: true, subtree: true })

    const timer = setTimeout(() => {
      observer.disconnect()
      resolve()
    }, timeoutMs)
  })
}

export function getStringField(obj: Record<string, unknown>, key: string): string | null {
  const value = obj[key]
  return typeof value === "string" && value.trim() ? value.trim() : null
}

export function getNestedStringField(obj: Record<string, unknown>, key: string, nestedKey: string): string | null {
  const nested = obj[key]
  if (typeof nested !== "object" || nested === null) return null
  return getStringField(nested as Record<string, unknown>, nestedKey)
}

export function isJobPosting(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && (value as Record<string, unknown>)["@type"] === "JobPosting"
}
