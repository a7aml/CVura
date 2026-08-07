import type { ResumeTailorResult } from "~lib/types"

const KEY_PREFIX = "resume-result:"

function storageKey(jobId: string): string {
  return `${KEY_PREFIX}${jobId}`
}

// chrome.storage.session persists across the popup closing and reopening
// (unlike React/component state, which is destroyed with the popup's
// document) but clears when the browser session ends — the right lifetime
// for "don't re-run the expensive pipeline for a job we already tailored,"
// without needing a backend lookup or building resume version history early.
export async function getCachedResult(jobId: string): Promise<ResumeTailorResult | null> {
  const key = storageKey(jobId)
  const stored = await chrome.storage.session.get(key)
  return (stored[key] as ResumeTailorResult | undefined) ?? null
}

export async function setCachedResult(jobId: string, result: ResumeTailorResult): Promise<void> {
  await chrome.storage.session.set({ [storageKey(jobId)]: result })
}
