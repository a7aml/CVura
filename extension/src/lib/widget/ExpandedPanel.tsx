import { detectBoard, extractForBoard } from "~lib/job-board"
import type { User } from "~lib/types"
import JobAnalyze from "~popup/screens/JobAnalyze"
import Login from "~popup/screens/Login"

interface ExpandedPanelProps {
  user: User | null | "loading"
  onCollapse: () => void
  onDismiss: () => void
}

// Reuses the same Login/JobAnalyze/ResumeResult screens the toolbar popup
// uses (JobAnalyze renders ResumeResult itself once a job is saved) — the
// widget only adds the fab/panel chrome around them, not a parallel flow.
export default function ExpandedPanel({ user, onCollapse, onDismiss }: ExpandedPanelProps) {
  return (
    <div className="cvura-panel">
      <div className="cvura-panel-header">
        <div className="brand">
          <div className="brand-mark">CV</div>
          <div className="brand-name">CVura</div>
        </div>
        <div className="cvura-panel-actions">
          <button type="button" className="cvura-icon-button" onClick={onCollapse} aria-label="Collapse">
            –
          </button>
          <button type="button" className="cvura-icon-button" onClick={onDismiss} aria-label="Hide for this page">
            ×
          </button>
        </div>
      </div>

      {user === "loading" && (
        <div className="center-screen">
          <span className="spinner spinner-dark" />
        </div>
      )}

      {user === null && <Login />}

      {user !== "loading" && user !== null && (
        <JobAnalyze extract={() => extractForBoard(detectBoard())} onBack={onCollapse} />
      )}
    </div>
  )
}
