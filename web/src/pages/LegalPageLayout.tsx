import type { ReactNode } from "react"
import { Link } from "react-router-dom"

import "./LandingPage.css"

export default function LegalPageLayout({ children }: { children: ReactNode }) {
  return (
    <div className="landing-page">
      <header className="nav">
        <div className="wrap">
          <Link className="wordmark" to="/">
            CV<span>ura</span>
          </Link>
          <div className="nav-actions">
            <Link className="btn btn-ghost btn-small" to="/">
              Back to CVura
            </Link>
          </div>
        </div>
      </header>

      <main className="doc">
        <div className="wrap">{children}</div>
      </main>

      <footer className="footer">
        <div className="wrap">
          <Link className="wordmark" to="/">
            CV<span>ura</span>
          </Link>
          <div className="footer-links">
            <Link to="/privacy">Privacy Policy</Link>
            <Link to="/terms">Terms</Link>
            <a href="mailto:hello@cvura.app">Contact</a>
            <a href="https://github.com/a7aml/CVura" rel="noopener">
              GitHub
            </a>
          </div>
          <p className="copyright">© 2026 CVura. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}
