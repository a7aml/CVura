import { isApiRequestMessage, performApiRequest } from "~lib/api"
import type { ApiRequestMessage, ApiResponseMessage } from "~lib/api"
import { WEB_APP_LOGIN_PATH, WEB_APP_URL } from "~lib/config"
import { isDownloadFileMessage, isOpenTabMessage } from "~lib/runtime-actions"

// /auth/refresh's refresh token is single-use and rotates on every call, with
// reuse of an already-rotated token treated as theft and revoking the whole
// token family (backend/app/services/auth_service.py). Any two callers
// racing to refresh the same session within the same instant — e.g. a
// component's effect re-firing, or a second extension surface calling
// checkSession() around the same time a future feature adds one — would mean
// one legitimate caller gets treated as a thief and the user's session is
// revoked outright. Coalescing identical in-flight requests here — the one
// place every caller already funnels through — collapses them into a single
// network call so there's never a second, colliding consumer of the same
// token.
const inFlightApiRequests = new Map<string, Promise<ApiResponseMessage>>()

function dedupedApiRequest(message: ApiRequestMessage): Promise<ApiResponseMessage> {
  const key = `${message.method ?? "GET"} ${message.path} ${message.body ?? ""}`
  const existing = inFlightApiRequests.get(key)
  if (existing) return existing

  const request = performApiRequest(message).finally(() => inFlightApiRequests.delete(key))
  inFlightApiRequests.set(key, request)
  return request
}

// First-run onboarding: signup/login and the full Profile Builder live on the
// website, not in the popup (too little room for 8 sections there), so send
// new installs straight to the website's login page instead of leaving them
// to find it themselves.
chrome.runtime.onInstalled.addListener(({ reason }) => {
  if (reason === "install") {
    chrome.tabs.create({ url: `${WEB_APP_URL}${WEB_APP_LOGIN_PATH}` })
  }
})

function errorMessage(err: unknown): string {
  return err instanceof Error ? err.message : String(err)
}

// Fulfils OPEN_TAB / DOWNLOAD_FILE (~lib/runtime-actions) and API_REQUEST
// (~lib/api) messages relayed from the popup and content scripts. Every
// branch must call sendResponse on both success AND failure — a rejected
// chrome.tabs/chrome.downloads/fetch call with no .catch() here leaves the
// caller's chrome.runtime.sendMessage promise unresolved forever (observed:
// an invalid download filename left the popup stuck on its loading state
// indefinitely instead of surfacing an error).
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (isOpenTabMessage(message)) {
    chrome.tabs
      .create({ url: message.url })
      .then(() => sendResponse({ ok: true }))
      .catch((err) => sendResponse({ ok: false, error: errorMessage(err) }))
    return true
  }
  if (isDownloadFileMessage(message)) {
    chrome.downloads
      .download({ url: message.url, filename: message.filename, saveAs: false })
      .then(() => sendResponse({ ok: true }))
      .catch((err) => sendResponse({ ok: false, error: errorMessage(err) }))
    return true
  }
  if (isApiRequestMessage(message)) {
    dedupedApiRequest(message)
      .then(sendResponse)
      .catch((err) => sendResponse({ ok: false, status: 0, body: { detail: errorMessage(err) } }))
    return true
  }
  return undefined
})
