import { WEB_APP_LOGIN_PATH, WEB_APP_URL } from "~lib/config"

// First-run onboarding: signup/login and the full Profile Builder live on the
// website, not in the popup (too little room for 8 sections there), so send
// new installs straight to the website's login page instead of leaving them
// to find it themselves.
chrome.runtime.onInstalled.addListener(({ reason }) => {
  if (reason === "install") {
    chrome.tabs.create({ url: `${WEB_APP_URL}${WEB_APP_LOGIN_PATH}` })
  }
})
