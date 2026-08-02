import { useEffect, useState } from "react"
import { Link, useNavigate } from "react-router-dom"

import { loginWithGoogle } from "../lib/api"
import { extractIdTokenFromCallback } from "../lib/auth"
import { prefersReducedMotion } from "../lib/motion"
import type { User } from "../lib/types"

const SUCCESS_DELAY_MS = 500

function CheckIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true">
      <path d="M20 6 9 17l-5-5" />
    </svg>
  )
}

export default function AuthCallbackPage({ onAuthenticated }: { onAuthenticated: (user: User) => void }) {
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    const idToken = extractIdTokenFromCallback()
    if (!idToken) {
      setError("Google sign-in did not return a token.")
      return
    }
    loginWithGoogle(idToken)
      .then((user) => {
        function proceed() {
          onAuthenticated(user)
          navigate("/app/profile", { replace: true })
        }
        if (prefersReducedMotion()) {
          proceed()
          return
        }
        setSuccess(true)
        window.setTimeout(proceed, SUCCESS_DELAY_MS)
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Google sign-in failed"))
  }, [onAuthenticated, navigate])

  if (error) {
    return (
      <div className="auth-shell center-screen">
        <div>
          <div className="error-banner" role="alert">
            {error}
          </div>
          <Link to="/app/login" className="button button-secondary" style={{ marginTop: 16, display: "inline-flex" }}>
            Back to login
          </Link>
        </div>
      </div>
    )
  }

  if (success) {
    return (
      <div className="auth-shell center-screen">
        <div className="success-state">
          <span className="success-check">
            <CheckIcon />
          </span>
          <p className="hint" style={{ margin: 0 }}>
            You're in — taking you to your profile…
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="auth-shell center-screen">
      <span className="spinner spinner-dark" />
    </div>
  )
}
