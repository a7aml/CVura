import { useState } from "react"

import ResumeUploadForm from "./ResumeUploadForm"
import { EditIcon, UploadIcon } from "./wizard-icons"

export default function OnboardingChoice({
  onManual,
  onImported,
}: {
  onManual: () => void
  onImported: () => void
}) {
  const [uploading, setUploading] = useState(false)

  if (uploading) {
    return <ResumeUploadForm onSuccess={onImported} onManual={onManual} />
  }

  return (
    <div className="section-block">
      <h2>How would you like to start?</h2>
      <p className="hint">Upload an existing resume and we'll fill in your profile for you, or build it from scratch.</p>

      <div className="onboarding-choice-grid">
        <button type="button" className="onboarding-choice-card" onClick={() => setUploading(true)}>
          <UploadIcon aria-hidden="true" />
          <span className="onboarding-choice-title">Upload your resume</span>
          <span className="onboarding-choice-desc">We'll extract your details from a PDF automatically.</span>
        </button>
        <button type="button" className="onboarding-choice-card" onClick={onManual}>
          <EditIcon aria-hidden="true" />
          <span className="onboarding-choice-title">Fill in manually</span>
          <span className="onboarding-choice-desc">Step through the guided profile wizard yourself.</span>
        </button>
      </div>
    </div>
  )
}
