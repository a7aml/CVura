import { useState } from "react"

import { login, signup } from "../lib/api"
import { redirectToGoogleSignIn } from "../lib/auth"
import { prefersReducedMotion } from "../lib/motion"
import type { User } from "../lib/types"
import "./LoginPage.css"

const SUCCESS_DELAY_MS = 500

type Mode = "login" | "signup"

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
      <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" />
      <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332C2.438 15.983 5.482 18 9 18z" />
      <path fill="#FBBC05" d="M3.964 10.707A5.41 5.41 0 013.682 9c0-.593.102-1.17.282-1.707V4.961H.957A8.996 8.996 0 000 9c0 1.452.348 2.827.957 4.039l3.007-2.332z" />
      <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0 5.482 0 2.438 2.017.957 4.961L3.964 7.293C4.672 5.166 6.656 3.58 9 3.58z" />
    </svg>
  )
}

function AlertIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.75} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="10" />
      <path d="M12 8v5" />
      <path d="M12 16h.01" />
    </svg>
  )
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M20 6 9 17l-5-5" />
    </svg>
  )
}

export default function LoginPage({ onAuthenticated }: { onAuthenticated: (user: User) => void }) {
  const [mode, setMode] = useState<Mode>("login")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  function proceedAuthenticated(user: User) {
    if (prefersReducedMotion()) {
      onAuthenticated(user)
      return
    }
    setSuccess(true)
    window.setTimeout(() => onAuthenticated(user), SUCCESS_DELAY_MS)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const user = mode === "login" ? await login(email, password) : await signup(email, password)
      proceedAuthenticated(user)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong")
    } finally {
      setLoading(false)
    }
  }

  function handleGoogleSignIn() {
    setError(null)
    try {
      redirectToGoogleSignIn()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google sign-in failed")
    }
  }

  return (
    <div className="auth-page">
      <aside className="auth-visual">
        <a className="auth-visual-wordmark" href="/">
          CV<span>ura</span>
        </a>
        <div className="auth-visual-copy">
          <h2>Tailored résumés, one click at a time.</h2>
          <p>
            Build your profile once — CVura matches it against every posting you open and reorders
            it to fit, without ever inventing a skill you don't have.
          </p>
          <ul className="auth-visual-points">
            <li>
              <span className="check">
                <CheckIcon />
              </span>
              3 tailored résumés free, forever
            </li>
            <li>
              <span className="check">
                <CheckIcon />
              </span>
              Works on LinkedIn, Greenhouse & Lever
            </li>
            <li>
              <span className="check">
                <CheckIcon />
              </span>
              ATS-formatted PDF export
            </li>
          </ul>
        </div>
        <p className="auth-visual-foot">© 2026 CVura</p>
      </aside>

      <div className="auth-form-side">
        <div className={`auth-card ${success ? "auth-card-success" : ""}`}>
          {success ? (
            <div className="auth-success">
              <span className="auth-success-check">
                <CheckIcon />
              </span>
              <p>You're in — taking you to your profile…</p>
            </div>
          ) : (
            <>
              <div className="auth-brand-mobile">
                <div className="auth-brand-mark">CV</div>
                <div className="auth-brand-name">CVura</div>
              </div>

              <h1 className="auth-heading">{mode === "login" ? "Welcome back" : "Create your account"}</h1>
              <p className="auth-subheading">
                {mode === "login" ? "Log in to keep tailoring your résumé." : "Start free — no card required."}
              </p>

              <div className="auth-tabs" role="tablist" data-mode={mode}>
                <span className="auth-tab-indicator" aria-hidden="true" />
                <button
                  type="button"
                  role="tab"
                  className={`auth-tab ${mode === "login" ? "active" : ""}`}
                  disabled={loading}
                  aria-selected={mode === "login"}
                  onClick={() => setMode("login")}>
                  Log in
                </button>
                <button
                  type="button"
                  role="tab"
                  className={`auth-tab ${mode === "signup" ? "active" : ""}`}
                  disabled={loading}
                  aria-selected={mode === "signup"}
                  onClick={() => setMode("signup")}>
                  Sign up
                </button>
              </div>

              <form className="auth-form" onSubmit={handleSubmit}>
                <div className="auth-field">
                  <label htmlFor="email">Email</label>
                  <input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    disabled={loading}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </div>
                <div className="auth-field">
                  <label htmlFor="password">Password</label>
                  <input
                    id="password"
                    type="password"
                    placeholder="At least 8 characters"
                    value={password}
                    disabled={loading}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    minLength={8}
                  />
                </div>

                {error && (
                  <div className="auth-error" role="alert">
                    <AlertIcon />
                    <span>{error}</span>
                  </div>
                )}

                <button type="submit" className="auth-submit" disabled={loading}>
                  {loading && <span className="auth-spinner" />}
                  {mode === "login" ? "Log in" : "Create account"}
                </button>
              </form>

              <div className="auth-divider">or</div>

              <button type="button" className="auth-google" onClick={handleGoogleSignIn} disabled={loading}>
                <GoogleIcon />
                Continue with Google
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
