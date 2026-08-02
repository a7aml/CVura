import { useState } from "react"

import type { Profile, ProfileFields } from "../../lib/types"

const EMPTY: ProfileFields = {
  full_name: "",
  phone: null,
  location: null,
  linkedin_url: null,
  github_url: null,
  portfolio_url: null,
  desired_title: null,
  summary: null,
  career_objective: null,
}

export default function BasicInfoForm({
  initial,
  onSubmit,
  submitLabel,
}: {
  initial: Profile | null
  onSubmit: (fields: ProfileFields) => Promise<void>
  submitLabel: string
}) {
  const [fields, setFields] = useState<ProfileFields>(initial ?? EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function set<K extends keyof ProfileFields>(key: K, value: ProfileFields[K]) {
    setFields((f) => ({ ...f, [key]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      await onSubmit(fields)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save")
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="form" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="full_name">Full name</label>
        <input
          id="full_name"
          value={fields.full_name}
          onChange={(e) => set("full_name", e.target.value)}
          required
        />
      </div>
      <div className="field">
        <label htmlFor="desired_title">Desired title</label>
        <input
          id="desired_title"
          value={fields.desired_title ?? ""}
          onChange={(e) => set("desired_title", e.target.value || null)}
        />
      </div>
      <div className="form-row">
        <div className="field">
          <label htmlFor="phone">Phone</label>
          <input id="phone" value={fields.phone ?? ""} onChange={(e) => set("phone", e.target.value || null)} />
        </div>
        <div className="field">
          <label htmlFor="location">Location</label>
          <input
            id="location"
            value={fields.location ?? ""}
            onChange={(e) => set("location", e.target.value || null)}
          />
        </div>
      </div>
      <div className="form-row">
        <div className="field">
          <label htmlFor="linkedin_url">LinkedIn URL</label>
          <input
            id="linkedin_url"
            value={fields.linkedin_url ?? ""}
            onChange={(e) => set("linkedin_url", e.target.value || null)}
          />
        </div>
        <div className="field">
          <label htmlFor="github_url">GitHub URL</label>
          <input
            id="github_url"
            value={fields.github_url ?? ""}
            onChange={(e) => set("github_url", e.target.value || null)}
          />
        </div>
      </div>
      <div className="field">
        <label htmlFor="portfolio_url">Portfolio URL</label>
        <input
          id="portfolio_url"
          value={fields.portfolio_url ?? ""}
          onChange={(e) => set("portfolio_url", e.target.value || null)}
        />
      </div>
      <div className="field">
        <label htmlFor="summary">Summary</label>
        <textarea
          id="summary"
          value={fields.summary ?? ""}
          onChange={(e) => set("summary", e.target.value || null)}
        />
      </div>
      <div className="field">
        <label htmlFor="career_objective">Career objective</label>
        <textarea
          id="career_objective"
          value={fields.career_objective ?? ""}
          onChange={(e) => set("career_objective", e.target.value || null)}
        />
      </div>

      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}

      <button type="submit" className="button button-primary" disabled={saving}>
        {saving && <span className="spinner" />}
        {submitLabel}
      </button>
    </form>
  )
}
