import { WEB_APP_LOGIN_PATH, WEB_APP_URL } from "~lib/config"

// Signup/login only exists on the website — this screen never collects
// credentials, it just hands off to the website's login page in a new tab.
export default function Login() {
  function openWebLogin() {
    chrome.tabs.create({ url: `${WEB_APP_URL}${WEB_APP_LOGIN_PATH}` })
  }

  return (
    <div className="app center-screen">
      <div className="brand">
        <div className="brand-mark">CV</div>
        <div className="brand-name">CVura</div>
      </div>
      <p style={{ color: "var(--color-text-muted)", fontSize: 13, textAlign: "center", margin: 0 }}>
        Sign in on the CVura website to use the extension.
      </p>
      <button type="button" className="button button-primary" onClick={openWebLogin}>
        Sign in on website
      </button>
    </div>
  )
}
