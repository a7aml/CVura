import { useEffect, useState } from "react"
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom"

import { checkSession } from "./lib/auth"
import type { User } from "./lib/types"
import AuthCallbackPage from "./pages/AuthCallbackPage"
import LandingPage from "./pages/LandingPage"
import LoginPage from "./pages/LoginPage"
import PrivacyPage from "./pages/PrivacyPage"
import ProfileBuilderPage from "./pages/ProfileBuilderPage"
import TermsPage from "./pages/TermsPage"

type Status = "loading" | "authenticated" | "unauthenticated"

const AUTH_CALLBACK_PATH = "/app/auth/callback"

function AppShell() {
  const [status, setStatus] = useState<Status>("loading")
  const [user, setUser] = useState<User | null>(null)
  const location = useLocation()
  const isCallback = location.pathname === AUTH_CALLBACK_PATH

  useEffect(() => {
    if (isCallback) return
    checkSession().then((restoredUser) => {
      setUser(restoredUser)
      setStatus(restoredUser ? "authenticated" : "unauthenticated")
    })
    // Only ever run once per mount — re-checking on every navigation within
    // /app/* would race with the login/callback flows updating this state.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function handleAuthenticated(authedUser: User) {
    setUser(authedUser)
    setStatus("authenticated")
  }

  function handleLoggedOut() {
    setUser(null)
    setStatus("unauthenticated")
  }

  if (isCallback) {
    return <AuthCallbackPage onAuthenticated={handleAuthenticated} />
  }

  if (status === "loading") {
    return (
      <div className="auth-shell center-screen">
        <span className="spinner spinner-dark" />
      </div>
    )
  }

  const isAuthenticated = status === "authenticated" && user !== null

  return (
    <Routes>
      <Route
        path="login"
        element={isAuthenticated ? <Navigate to="/app/profile" replace /> : <LoginPage onAuthenticated={handleAuthenticated} />}
      />
      <Route
        path="profile"
        element={
          isAuthenticated ? (
            <ProfileBuilderPage user={user as User} onLoggedOut={handleLoggedOut} />
          ) : (
            <Navigate to="/app/login" replace />
          )
        }
      />
      <Route path="*" element={<Navigate to={isAuthenticated ? "/app/profile" : "/app/login"} replace />} />
    </Routes>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/app/*" element={<AppShell />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
