import { useEffect, useState } from "react"

import { logout } from "~lib/api"
import { checkSession } from "~lib/auth"
import { matchSupportedJobBoard } from "~lib/config"
import type { ExtractedJob, User } from "~lib/types"
import JobAnalyze from "~popup/screens/JobAnalyze"
import Login from "~popup/screens/Login"

type Status = "loading" | "authenticated" | "unauthenticated"

interface ExtractJobMessage {
  type: "EXTRACT_JOB"
}

// The popup isn't on the job's tab itself, so extraction has to be requested
// from the tab's content script (contents/detect.ts) via messaging — unlike
// the widget, which runs in that tab and can call ~lib/job-board directly.
function requestExtraction(tabId: number): Promise<ExtractedJob | null> {
  const message: ExtractJobMessage = { type: "EXTRACT_JOB" }
  return chrome.tabs.sendMessage(tabId, message).catch(() => null)
}

function initials(email: string) {
  return email.slice(0, 2).toUpperCase()
}

function AccountCard({
  user,
  loading,
  onLogout
}: {
  user: User
  loading: boolean
  onLogout: () => void
}) {
  return (
    <div className="app">
      <div className="account-card">
        <div className="avatar">{initials(user.email)}</div>
        <div className="account-email">{user.email}</div>
        <span className="plan-badge">{user.plan} plan</span>
      </div>
      <button type="button" className="button button-secondary" disabled={loading} onClick={onLogout}>
        {loading && <span className="spinner spinner-dark" />}
        Log out
      </button>
    </div>
  )
}

function LoadingScreen() {
  return (
    <div className="app center-screen">
      <span className="spinner spinner-dark" />
    </div>
  )
}

function Popup() {
  const [status, setStatus] = useState<Status>("loading")
  const [user, setUser] = useState<User | null>(null)
  const [loggingOut, setLoggingOut] = useState(false)
  const [jobTabId, setJobTabId] = useState<number | null>(null)
  const [showAccount, setShowAccount] = useState(false)

  useEffect(() => {
    checkSession().then((restoredUser) => {
      setUser(restoredUser)
      setStatus(restoredUser ? "authenticated" : "unauthenticated")
    })
  }, [])

  useEffect(() => {
    if (status !== "authenticated") return
    chrome.tabs.query({ active: true, currentWindow: true }).then(([tab]) => {
      if (!tab || tab.id === undefined || !tab.url) {
        setJobTabId(null)
        return
      }
      setJobTabId(matchSupportedJobBoard(tab.url) ? tab.id : null)
    })
  }, [status])

  async function handleLogout() {
    setLoggingOut(true)
    try {
      await logout()
    } finally {
      setUser(null)
      setStatus("unauthenticated")
      setLoggingOut(false)
    }
  }

  if (status === "loading") {
    return <LoadingScreen />
  }

  if (status === "authenticated" && user) {
    if (jobTabId !== null && !showAccount) {
      return <JobAnalyze extract={() => requestExtraction(jobTabId)} onBack={() => setShowAccount(true)} />
    }
    return <AccountCard user={user} loading={loggingOut} onLogout={handleLogout} />
  }

  return <Login />
}

export default Popup
