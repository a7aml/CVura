import { isApiRequestMessage, performApiRequest } from "~lib/api"
import type { ApiRequestMessage, ApiResponseMessage } from "~lib/api"
import { WEB_APP_LOGIN_PATH, WEB_APP_URL } from "~lib/config"
import { isDownloadFileMessage, isOpenTabMessage } from "~lib/runtime-actions"

// The popup and the content-script widget (~lib/widget/useWidgetSession) both
// independently call checkSession() and can end up doing so within the same
// instant — e.g. opening the popup right after the widget mounts on a job
// page. /auth/refresh's refresh token is single-use and rotates on every
// call, with reuse of an already-rotated token treated as theft and revoking
// the whole token family (backend/app/services/auth_service.py). Two
// simultaneous callers racing for the same cookie would otherwise mean one
// legitimate caller gets treated as a thief and the user's session is
// revoked outright. Coalescing identical in-flight requests here — the one
// place both callers already funnel through — collapses them into a single
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

// Fulfils OPEN_TAB / DOWNLOAD_FILE (~lib/runtime-actions) and API_REQUEST
// (~lib/api) messages. chrome.tabs / chrome.downloads are unavailable to
// content scripts, and a fetch from the content-script widget would carry
// the host job-board page's origin rather than the extension's — both are
// routed here so popup and widget share one working code path.
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (isOpenTabMessage(message)) {
    chrome.tabs.create({ url: message.url }).then(() => sendResponse())
    return true
  }
  if (isDownloadFileMessage(message)) {
    chrome.downloads.download({ url: message.url, filename: message.filename, saveAs: false }).then(() => sendResponse())
    return true
  }
  if (isApiRequestMessage(message)) {
    dedupedApiRequest(message).then(sendResponse)
    return true
  }
  return undefined
})
