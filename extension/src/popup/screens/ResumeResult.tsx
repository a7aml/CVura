import { useEffect, useState } from "react"

import { analyzeJob, isLimitReachedError, tailorResume } from "~lib/api"
import { WEB_APP_URL } from "~lib/config"
import { downloadFile, openTab } from "~lib/runtime-actions"
import type { Job, ResumeTailorResult } from "~lib/types"

type State =
  | { status: "analyzing" }
  | { status: "tailoring" }
  | { status: "done"; result: ResumeTailorResult; downloaded: boolean }
  | { status: "error"; message: string }
  | { status: "limit-reached" }

function sanitizeFilenamePart(value: string): string {
  return value.replace(/[\\/:*?"<>|]/g, "").trim()
}

function buildFilename(job: Job): string {
  const parts = [job.company, job.title].filter((part): part is string => Boolean(part)).map(sanitizeFilenamePart)
  const base = parts.length > 0 ? parts.join(" - ") : job.title ? sanitizeFilenamePart(job.title) : "resume"
  return `CVura - ${base}.pdf`
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
      setState({ status: "analyzing" })
      try {
        await analyzeJob(job.id)
        if (cancelled) return
        setState({ status: "tailoring" })

        const result = await tailorResume(job.id)
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

          {state.downloaded ? (
            <p style={{ color: "var(--color-text-muted)", fontSize: 13, margin: 0 }}>
              Downloaded to your computer as a PDF.
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
              Download again
            </button>
          )}
        </div>
      )}
    </div>
  )
}
