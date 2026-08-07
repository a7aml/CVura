import { useEffect, useState } from "react"

import { analyzeJob, isLimitReachedError, tailorResume } from "~lib/api"
import { WEB_APP_URL } from "~lib/config"
import { getCachedResult, setCachedResult } from "~lib/resume-cache"
import { downloadFile, openTab } from "~lib/runtime-actions"
import type { Job, ResumeTailorResult } from "~lib/types"

type State =
  | { status: "analyzing" }
  | { status: "tailoring" }
  | { status: "done"; result: ResumeTailorResult; downloaded: boolean }
  | { status: "error"; message: string }
  | { status: "limit-reached" }

// chrome.downloads.download() rejects the whole download with a generic
// "Invalid filename" error for control characters (a scraped job title/
// company can carry a stray newline — e.g. from a multi-line company link's
// textContent), for names ending in "." or whitespace (a Windows path rule
// Chrome enforces even off-Windows), and — confirmed via a real rejection on
// a real RTL-locale LinkedIn posting — for Unicode bidi formatting
// characters (RLM/LRM and the embedding/override/isolate marks), which
// Chrome treats as a filename-spoofing risk and refuses outright. LinkedIn's
// Arabic-locale rendering wraps interpolated text in these (confirmed via
// view-source: title/company came through as e.g. "‏Luxoft‏"),
// and the first fix here only stripped ASCII control characters, missing
// this entirely. Previously this failure left the popup stuck on
// "Tailoring your resume…" forever too, since the background script didn't
// used to propagate it back to the caller either (see background/index.ts).
function sanitizeFilenamePart(value: string): string {
  return value
    .replace(/[\x00-\x1f\x7f]/g, " ")
    .replace(/[\u200b-\u200f\u202a-\u202e\u2066-\u2069]/g, "")
    .replace(/[\\/:*?"<>|]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/[.\s]+$/, "")
}

function buildFilename(job: Job): string {
  const parts = [job.company, job.title]
    .filter((part): part is string => Boolean(part))
    .map(sanitizeFilenamePart)
    .filter(Boolean)
  const base = parts.length > 0 ? parts.join(" - ") : "resume"
  // Chrome/most filesystems cap path components well above this, but the
  // job board content feeding `base` is otherwise unbounded.
  return `${`CVura - ${base}`.slice(0, 150)}.pdf`
}

function downloadPdf(url: string, job: Job): Promise<void> {
  return downloadFile(url, buildFilename(job))
}

export default function ResumeResult({ job, onBack }: { job: Job; onBack: () => void }) {
  const [state, setState] = useState<State>({ status: "analyzing" })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function run() {
      // attempt === 0 means this run wasn't triggered by "Try again" or
      // "Regenerate" (both bump attempt), so it's either a fresh job or one
      // reopened from a prior popup session — check for an existing result
      // before re-running analyze -> tailor -> download for it.
      if (attempt === 0) {
        const cached = await getCachedResult(job.id)
        if (cancelled) return
        if (cached) {
          setState({ status: "done", result: cached, downloaded: false })
          return
        }
      }

      setState({ status: "analyzing" })
      try {
        await analyzeJob(job.id)
        if (cancelled) return
        setState({ status: "tailoring" })

        const result = await tailorResume(job.id)
        if (cancelled) return
        await setCachedResult(job.id, result)
        if (cancelled) return

        if (result.pdf_url) {
          await downloadPdf(result.pdf_url, job)
          if (cancelled) return
          setState({ status: "done", result, downloaded: true })
        } else {
          setState({ status: "done", result, downloaded: false })
        }
      } catch (err) {
        if (cancelled) return
        if (isLimitReachedError(err)) {
          setState({ status: "limit-reached" })
          return
        }
        setState({ status: "error", message: err instanceof Error ? err.message : "Something went wrong" })
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [job.id, attempt])

  async function handleRedownload(result: ResumeTailorResult) {
    if (!result.pdf_url) return
    await downloadPdf(result.pdf_url, job)
  }

  return (
    <div className="app">
      <button type="button" className="button button-link" onClick={onBack} style={{ alignSelf: "flex-start" }}>
        ← Job
      </button>

      {(state.status === "analyzing" || state.status === "tailoring") && (
        <div className="center-screen" style={{ flexDirection: "column", gap: 12 }}>
          <span className="spinner spinner-dark" />
          <p style={{ color: "var(--color-text-muted)", fontSize: 13, margin: 0 }}>
            {state.status === "analyzing" ? "Analyzing job description…" : "Tailoring your resume…"}
          </p>
        </div>
      )}

      {state.status === "error" && (
        <div className="form">
          <div className="error-banner" role="alert">
            {state.message}
          </div>
          <button type="button" className="button button-secondary" onClick={() => setAttempt((n) => n + 1)}>
            Try again
          </button>
        </div>
      )}

      {state.status === "limit-reached" && (
        <div className="form">
          <p style={{ fontSize: 13, margin: 0 }}>
            You've used all your free resumes for this period. Upgrade to keep tailoring resumes for new jobs.
          </p>
          <button type="button" className="button button-primary" onClick={() => openTab(WEB_APP_URL)}>
            Upgrade plan
          </button>
        </div>
      )}

      {state.status === "done" && (
        <div className="form">
          <div className="job-preview job-preview-saved">
            <div className="job-preview-title">{job.title}</div>
            {job.company && <div className="job-preview-company">{job.company}</div>}
          </div>

          <p style={{ fontSize: 13, margin: 0 }}>{state.result.summary}</p>

          {state.result.skills.length > 0 && (
            <div className="skill-chips">
              {state.result.skills.map((skill) => (
                <span key={skill} className="skill-chip">
                  {skill}
                </span>
              ))}
            </div>
          )}

          {state.result.pdf_url ? (
            <p style={{ color: "var(--color-text-muted)", fontSize: 13, margin: 0 }}>
              {state.downloaded ? "Downloaded to your computer as a PDF." : "Your tailored resume is ready."}
            </p>
          ) : (
            <div className="error-banner" role="alert">
              PDF generation failed, but your tailored resume content was saved.
            </div>
          )}

          {state.result.pdf_url && (
            <button
              type="button"
              className="button button-secondary"
              onClick={() => handleRedownload(state.result)}>
              {state.downloaded ? "Download again" : "Download"}
            </button>
          )}

          <button type="button" className="button button-link" onClick={() => setAttempt((n) => n + 1)}>
            Regenerate
          </button>
        </div>
      )}
    </div>
  )
}
