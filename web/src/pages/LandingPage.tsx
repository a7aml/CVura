import { useEffect } from "react"
import { Link } from "react-router-dom"

import "./LandingPage.css"
import {
  BadgeCheckIcon,
  CheckCircleIcon,
  DownloadIcon,
  FileTextIcon,
  ListChecksIcon,
  PenLineIcon,
  SearchIcon,
  ShieldCheckIcon,
  SparklesIcon,
  UserRoundIcon,
  ZapIcon,
} from "./landing-icons"

export default function LandingPage() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return

    const targets = document.querySelectorAll<HTMLElement>(".landing-page .reveal")
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue
          entry.target.classList.add("in-view")
          observer.unobserve(entry.target)
        }
      },
      { threshold: 0.2, rootMargin: "0px 0px -60px 0px" },
    )
    for (const el of targets) observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return (
    <div className="landing-page">
      <header className="nav">
        <div className="wrap">
          <a className="wordmark" href="#top">
            CV<span>ura</span>
          </a>
          <nav className="nav-links">
            <a href="#how-it-works">How it works</a>
            <a href="#pricing">Pricing</a>
          </nav>
          <div className="nav-actions">
            <Link className="btn btn-primary btn-small" to="/app/login">
              Add to Chrome
            </Link>
          </div>
        </div>
      </header>

      <main id="top">
        {/* Hero */}
        <section className="hero">
          <div className="wrap">
            <div className="hero-copy">
              <p className="eyebrow">Chrome extension · Free to start</p>
              <h1>Open the posting. Click once. Get a résumé that actually fits.</h1>
              <p className="lede">
                CVura reads the job description, matches it against your real experience, and
                reorders — never invents — your résumé into something ATS software and hiring
                managers both read cleanly. Under a minute, straight from LinkedIn, Greenhouse, or
                Lever.
              </p>
              <div className="hero-actions">
                <Link className="btn btn-primary" to="/app/login">
                  Add to Chrome — it's free
                </Link>
                <span className="hero-note">3 tailored résumés free, forever. No card required.</span>
              </div>
            </div>

            <div className="card-frame">
              <span className="reg-mark tl" aria-hidden="true"></span>
              <span className="reg-mark br" aria-hidden="true"></span>
              <div className="resume-card">
                <div className="resume-head">
                  <div className="resume-id">
                    <div className="resume-avatar">JD</div>
                    <div>
                      <div className="resume-name">Jordan Diaz</div>
                      <div className="resume-role">Senior Product Designer</div>
                    </div>
                  </div>
                  <span className="match-chip">MATCH 96%</span>
                </div>
                <div className="resume-progress">
                  <span className="resume-progress-fill" />
                </div>
                <ul className="resume-lines">
                  <li>Managed the design system and component library for the core product.</li>
                  <li>
                    <mark>Led a team of 5 designers</mark> across three product lines.
                  </li>
                  <li>
                    <mark>Reduced onboarding time by 40%</mark> through a redesigned first-run flow.
                  </li>
                </ul>
                <div className="resume-badge">
                  <BadgeCheckIcon className="resume-badge-icon" aria-hidden="true" />
                  <span>ATS optimized</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Problem */}
        <section className="section">
          <div className="wrap">
            <div className="section-head">
              <p className="eyebrow">The old way</p>
              <h2>Right now, tailoring a résumé means doing the same four things by hand — for every single posting.</h2>
              <p className="lede">Multiply that by every application you send this month.</p>
            </div>
            <div className="loop reveal">
              <span className="loop-step">
                <FileTextIcon className="loop-icon" aria-hidden="true" />
                Read the job description
              </span>
              <span className="loop-arrow">→</span>
              <span className="loop-step">
                <PenLineIcon className="loop-icon" aria-hidden="true" />
                Rewrite your summary
              </span>
              <span className="loop-arrow">→</span>
              <span className="loop-step">
                <ListChecksIcon className="loop-icon" aria-hidden="true" />
                Reorder your skills to match
              </span>
              <span className="loop-arrow">→</span>
              <span className="loop-step">
                <DownloadIcon className="loop-icon" aria-hidden="true" />
                Export a new PDF
              </span>
            </div>
            <p className="loop-return">↻ repeat for the next posting</p>
          </div>
        </section>

        {/* How it works */}
        <section className="section" id="how-it-works">
          <div className="wrap">
            <div className="section-head">
              <p className="eyebrow">How CVura works</p>
              <h2>Four steps. You only do the first one once.</h2>
            </div>
            <div className="steps">
              <div className="step reveal">
                <span className="step-icon">
                  <UserRoundIcon aria-hidden="true" />
                </span>
                <span className="step-num">01</span>
                <h3>Build your profile once</h3>
                <p>Real roles, real bullet points, real dates — stored in your account, not on any job board.</p>
              </div>
              <div className="step reveal">
                <span className="step-icon">
                  <SearchIcon aria-hidden="true" />
                </span>
                <span className="step-num">02</span>
                <h3>Open a posting</h3>
                <p>On LinkedIn, Greenhouse, or Lever — CVura reads it in the background.</p>
              </div>
              <div className="step reveal">
                <span className="step-icon">
                  <SparklesIcon aria-hidden="true" />
                </span>
                <span className="step-num">03</span>
                <h3>Click Generate</h3>
                <p>CVura matches your profile against the posting's actual language and requirements.</p>
              </div>
              <div className="step reveal">
                <span className="step-icon">
                  <DownloadIcon aria-hidden="true" />
                </span>
                <span className="step-num">04</span>
                <h3>Download the PDF</h3>
                <p>ATS-formatted and tailored — ready to submit.</p>
              </div>
            </div>
            <div className="boards">
              <span>Currently reads postings on:</span>
              <span className="board-chip">LinkedIn</span>
              <span className="board-chip">Greenhouse</span>
              <span className="board-chip">Lever</span>
            </div>
          </div>
        </section>

        {/* Trust */}
        <section className="section trust">
          <div className="wrap">
            <div className="reveal">
              <p className="eyebrow trust-eyebrow" style={{ marginBottom: 12 }}>
                <ShieldCheckIcon aria-hidden="true" />
                The one rule
              </p>
              <p className="trust-quote">CVura never invents a skill, a title, or an achievement you don't already have.</p>
              <p className="lede">
                Every tailored résumé is built only from what you told us in your profile. When
                something on the posting doesn't match your real experience, CVura leaves it out —
                it doesn't make it up.
              </p>
            </div>
            <div className="trust-points reveal">
              <div className="trust-point">
                <span className="check">
                  <CheckCircleIcon aria-hidden="true" />
                </span>
                <p>Only real facts from your profile are ever used.</p>
              </div>
              <div className="trust-point">
                <span className="check">
                  <CheckCircleIcon aria-hidden="true" />
                </span>
                <p>Missing requirements are omitted, never fabricated.</p>
              </div>
              <div className="trust-point">
                <span className="check">
                  <CheckCircleIcon aria-hidden="true" />
                </span>
                <p>You review every change before you download anything.</p>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing */}
        <section className="section" id="pricing">
          <div className="wrap">
            <div className="section-head">
              <p className="eyebrow">Pricing</p>
              <h2>Start free. Upgrade when you're actually job hunting.</h2>
            </div>
            <div className="plans">
              <div className="plan reveal">
                <p className="plan-name">Free</p>
                <p className="plan-price">$0</p>
                <ul className="plan-list">
                  <li>
                    <CheckCircleIcon className="plan-check" aria-hidden="true" />
                    3 tailored résumés, forever
                  </li>
                  <li>
                    <CheckCircleIcon className="plan-check" aria-hidden="true" />
                    All 3 supported job boards
                  </li>
                  <li>
                    <CheckCircleIcon className="plan-check" aria-hidden="true" />
                    ATS-formatted PDF export
                  </li>
                </ul>
                <Link className="btn btn-ghost" to="/app/login">
                  Add to Chrome
                </Link>
              </div>
              <div className="plan plan-pro reveal">
                <span className="reg-mark tl" aria-hidden="true"></span>
                <span className="reg-mark br" aria-hidden="true"></span>
                <p className="plan-name">
                  <ZapIcon className="plan-icon" aria-hidden="true" />
                  Pro
                </p>
                <p className="plan-price">
                  $9.99<span>/month</span>
                </p>
                <ul className="plan-list">
                  <li>
                    <CheckCircleIcon className="plan-check" aria-hidden="true" />
                    Unlimited tailored résumés
                  </li>
                  <li>
                    <CheckCircleIcon className="plan-check" aria-hidden="true" />
                    Full résumé version history
                  </li>
                  <li>
                    <CheckCircleIcon className="plan-check" aria-hidden="true" />
                    Priority generation
                  </li>
                </ul>
                <Link className="btn btn-primary" to="/app/login">
                  Start Pro
                </Link>
                <p className="plan-caption">Most people upgrade after their 3rd résumé.</p>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="footer">
        <div className="wrap">
          <a className="wordmark" href="#top">
            CV<span>ura</span>
          </a>
          <div className="footer-links">
            <Link to="/privacy">Privacy Policy</Link>
            <Link to="/terms">Terms</Link>
            {/* Placeholder contact address — replace with a real support address before launch */}
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
