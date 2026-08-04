import { useRef, useState } from "react"

import { importResumeProfile } from "../../lib/api"
import { FileTextIcon, UploadIcon } from "./wizard-icons"

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024
const ALLOWED_CONTENT_TYPE = "application/pdf"

function validateFile(file: File): string | null {
  if (!file.name.toLowerCase().endsWith(".pdf") || file.type !== ALLOWED_CONTENT_TYPE) {
    return "Please choose a PDF file."
  }
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return "That file is larger than 5MB. Please choose a smaller PDF."
  }
  return null
}

export default function ResumeUploadForm({
  onSuccess,
  onManual,
}: {
  onSuccess: () => void
  onManual: () => void
}) {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const picked = e.target.files?.[0] ?? null
    if (!picked) return
    const validationError = validateFile(picked)
    if (validationError) {
      setError(validationError)
      setFile(null)
      return
    }
    setError(null)
    setFile(picked)
  }

  function handleTryAnother() {
    setError(null)
    setFile(null)
    if (inputRef.current) inputRef.current.value = ""
    inputRef.current?.click()
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!file) return
    setError(null)
    setUploading(true)
    try {
      await importResumeProfile(file)
      onSuccess()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not read that resume")
      setUploading(false)
    }
  }

  return (
    <form className="form section-block" onSubmit={handleSubmit}>
      <h2>Upload your resume</h2>
      <p className="hint">We'll pull your details from the PDF straight into your profile — you can fine-tune anything afterward.</p>

      <label className="upload-dropzone" htmlFor="resume-file">
        <UploadIcon aria-hidden="true" />
        {file ? (
          <span className="upload-dropzone-file">
            <FileTextIcon aria-hidden="true" />
            {file.name}
          </span>
        ) : (
          <span>Click to choose a PDF (max 5MB)</span>
        )}
      </label>
      <input
        ref={inputRef}
        id="resume-file"
        type="file"
        accept=".pdf,application/pdf"
        onChange={handleFileChange}
        disabled={uploading}
        hidden
      />

      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}

      <div className="upload-actions">
        {error ? (
          <>
            <button type="button" className="button button-secondary" onClick={handleTryAnother}>
              Try another file
            </button>
            <button type="button" className="button button-secondary" onClick={onManual}>
              Fill in manually
            </button>
          </>
        ) : (
          <button type="submit" className="button button-primary" disabled={!file || uploading}>
            {uploading && <span className="spinner" />}
            {uploading ? "Reading your resume…" : "Upload & continue"}
          </button>
        )}
      </div>
    </form>
  )
}
