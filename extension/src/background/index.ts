import { isApiRequestMessage, performApiRequest } from "~lib/api"
import { WEB_APP_LOGIN_PATH, WEB_APP_URL } from "~lib/config"
import { isDownloadFileMessage, isOpenTabMessage } from "~lib/runtime-actions"

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
    performApiRequest(message).then(sendResponse)
    return true
  }
  return undefined
})
