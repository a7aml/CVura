import { useEffect, useState } from "react"

import { createJob } from "~lib/api"
import type { ExtractedJob, Job } from "~lib/types"
import ResumeResult from "~popup/screens/ResumeResult"

type State =
  | { status: "extracting" }
  | { status: "failed" }
  | { status: "preview"; job: ExtractedJob }
  | { status: "saving"; job: ExtractedJob }
  | { status: "save-failed"; job: ExtractedJob; error: string }
  | { status: "saved"; job: Job }

interface JobAnalyzeProps {
  // A function rather than a tabId directly, so the popup's tabId-messaging
  // strategy (Popup.tsx) stays out of this component's concerns.
  extract: () => Promise<ExtractedJob | null>
  onBack: () => void
}

export default function JobAnalyze({ extract, onBack }: JobAnalyzeProps) {
  const [state, setState] = useState<State>({ status: "extracting" })
  const [attempt, setAttempt] = useState(0)
  const [showResult, setShowResult] = useState(false)

  useEffect(() => {
    let cancelled = false
    setState({ status: "extracting" })
    setShowResult(false)
    extract().then((result) => {
      if (cancelled) return
      setState(result ? { status: "preview", job: result } : { status: "failed" })
    })
    return () => {
      cancelled = true
    }
    // Deliberately only re-runs on `attempt` (the "try again" button) — not on
    // `extract`, which callers may pass as a fresh closure every render.
  }, [attempt])

  async function handleSave(job: ExtractedJob) {
    setState({ status: "saving", job })
    try {
      const saved = await createJob(job)
      setState({ status: "saved", job: saved })
    } catch (err) {
      setState({ status: "save-failed", job, error: err instanceof Error ? err.message : "Could not save" })
    }
  }

  if (state.status === "saved" && showResult) {
    return <ResumeResult job={state.job} onBack={() => setShowResult(false)} />
  }

  return (
    <div className="app">
      <button type="button" className="button button-link" onClick={onBack} style={{ alignSelf: "flex-start" }}>
        ← Account
      </button>

      {state.status === "extracting" && (
        <div className="center-screen">
          <span className="spinner spinner-dark" />
        </div>
      )}

      {state.status === "failed" && (
        <div className="form">
          <p style={{ color: "var(--color-text-muted)", fontSize: 13, margin: 0 }}>
            Couldn't read this job posting. Try opening the full posting page (not a search results list) and try
            again.
          </p>
          <button type="button" className="button button-secondary" onClick={() => setAttempt((n) => n + 1)}>
            Try again
          </button>
        </div>
      )}

      {(state.status === "preview" || state.status === "saving" || state.status === "save-failed") && (
        <div className="form">
          <div className="job-preview">
            <div className="job-preview-title">{state.job.title}</div>
            {state.job.company && <div className="job-preview-company">{state.job.company}</div>}
          </div>

          {state.status === "save-failed" && (
            <div className="error-banner" role="alert">
              {state.error}
            </div>
          )}

          <button
            type="button"
            className="button button-primary"
            disabled={state.status === "saving"}
            onClick={() => handleSave(state.job)}>
            {state.status === "saving" && <span className="spinner" />}
            Save this job
          </button>
        </div>
      )}

      {state.status === "saved" && (
        <div className="form">
          <div className="job-preview job-preview-saved">
            <div className="job-preview-title">{state.job.title}</div>
            {state.job.company && <div className="job-preview-company">{state.job.company}</div>}
          </div>
          <p style={{ color: "var(--color-text-muted)", fontSize: 13, margin: 0 }}>Saved to your CVura account.</p>
          <button type="button" className="button button-primary" onClick={() => setShowResult(true)}>
            Generate CV
          </button>
        </div>
      )}
    </div>
  )
}
