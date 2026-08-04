import { useEffect, useState } from "react"

import { getProfile, logout } from "../lib/api"
import { prefersReducedMotion } from "../lib/motion"
import type { FullProfile, User } from "../lib/types"
import "./ProfileBuilderPage.css"
import OnboardingChoice from "./profile/OnboardingChoice"
import ProfileWizard from "./profile/ProfileWizard"

export default function ProfileBuilderPage({
  user,
  onLoggedOut,
}: {
  user: User
  onLoggedOut: () => void
}) {
  const [profile, setProfile] = useState<FullProfile | null>(null)
  const [needsCreate, setNeedsCreate] = useState(false)
  const [loading, setLoading] = useState(true)
  const [onboardingMode, setOnboardingMode] = useState<"choice" | "manual">("choice")
  const [loggingOut, setLoggingOut] = useState(false)

  async function refresh() {
    try {
      setProfile(await getProfile())
      setNeedsCreate(false)
    } catch {
      setNeedsCreate(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function handleLogout() {
    await logout()
    if (prefersReducedMotion()) {
      onLoggedOut()
      return
    }
    // Let the fade-out play before swapping to the login page.
    setLoggingOut(true)
    window.setTimeout(onLoggedOut, 220)
  }

  if (loading) {
    return (
      <div className="shell center-screen">
        <span className="spinner spinner-dark" />
      </div>
    )
  }

  const hasProfile = !needsCreate && profile !== null
  const showOnboardingChoice = !hasProfile && onboardingMode === "choice"

  return (
    <div className={`shell wizard-shell ${loggingOut ? "wizard-shell-leaving" : ""}`}>
      <div className="header-bar">
        <div className="brand">
          <div className="brand-mark">CV</div>
          <div className="brand-name">CVura</div>
        </div>
        <div>
          <span style={{ marginRight: 12, color: "var(--color-text-muted)", fontSize: 13 }}>{user.email}</span>
          <button type="button" className="button button-secondary button-small" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </div>

      {showOnboardingChoice ? (
        <OnboardingChoice onManual={() => setOnboardingMode("manual")} onImported={refresh} />
      ) : (
        <ProfileWizard profile={profile} hasProfile={hasProfile} refresh={refresh} />
      )}
    </div>
  )
}
