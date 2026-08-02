import { useState } from "react"

import { experienceApi } from "../../lib/api"
import { prefersReducedMotion } from "../../lib/motion"
import type { Experience } from "../../lib/types"

type Fields = Omit<Experience, "id">
const EMPTY: Fields = { title: "", company: "", start_date: null, end_date: null, bullets: [] }

function ExperienceForm({
  initial,
  onSaved,
  onCancel,
}: {
  initial: Experience | null
  onSaved: () => Promise<void>
  onCancel: () => void
}) {
  const [fields, setFields] = useState<Fields>(initial ?? EMPTY)
  const [bulletsText, setBulletsText] = useState((initial?.bullets ?? []).join("\n"))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function set<K extends keyof Fields>(key: K, value: Fields[K]) {
    setFields((f) => ({ ...f, [key]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    const bullets = bulletsText.split("\n").map((line) => line.trim()).filter(Boolean)
    const payload = { ...fields, bullets }
    try {
      if (initial) await experienceApi.update(initial.id, payload)
      else await experienceApi.add(payload)
      await onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save")
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="form item-card" onSubmit={handleSubmit}>
      <div className="form-row">
        <div className="field">
          <label htmlFor="title">Title</label>
          <input id="title" value={fields.title} onChange={(e) => set("title", e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="company">Company</label>
          <input id="company" value={fields.company} onChange={(e) => set("company", e.target.value)} required />
        </div>
      </div>
      <div className="form-row">
        <div className="field">
          <label htmlFor="start_date">Start date</label>
          <input
            id="start_date"
            type="date"
            value={fields.start_date ?? ""}
            onChange={(e) => set("start_date", e.target.value || null)}
          />
        </div>
        <div className="field">
          <label htmlFor="end_date">End date (blank = current)</label>
          <input
            id="end_date"
            type="date"
            value={fields.end_date ?? ""}
            onChange={(e) => set("end_date", e.target.value || null)}
          />
        </div>
      </div>
      <div className="field">
        <label htmlFor="bullets">Bullet points (one per line)</label>
        <textarea id="bullets" value={bulletsText} onChange={(e) => setBulletsText(e.target.value)} />
      </div>
      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}
      <div className="item-actions">
        <button type="submit" className="button button-primary button-small" disabled={saving}>
          {saving && <span className="spinner" />}
          Save
        </button>
        <button type="button" className="button button-secondary button-small" onClick={onCancel}>
          Cancel
        </button>
      </div>
    </form>
  )
}

export default function ExperienceSection({
  items,
  onChange,
}: {
  items: Experience[]
  onChange: () => Promise<void>
}) {
  const [editingId, setEditingId] = useState<string | "new" | null>(null)
  const [removingId, setRemovingId] = useState<string | null>(null)

  async function handleDelete(id: string) {
    if (prefersReducedMotion()) {
      await experienceApi.remove(id)
      await onChange()
      return
    }
    setRemovingId(id)
    window.setTimeout(async () => {
      await experienceApi.remove(id)
      await onChange()
      setRemovingId(null)
    }, 220)
  }

  async function handleSaved() {
    setEditingId(null)
    await onChange()
  }

  return (
    <div className="section-block">
      <h2>Experience</h2>
      {items.length === 0 && editingId !== "new" && <p className="empty-state">No experience added yet.</p>}
      {items.map((item) =>
        editingId === item.id ? (
          <ExperienceForm key={item.id} initial={item} onSaved={handleSaved} onCancel={() => setEditingId(null)} />
        ) : (
          <div className={`item-card ${removingId === item.id ? "item-card-removing" : ""}`} key={item.id}>
            <div className="item-card-head">
              <div>
                <div className="item-title">
                  {item.title} · {item.company}
                </div>
                {item.bullets.length > 0 && (
                  <ul className="bullets-list">
                    {item.bullets.map((bullet, i) => (
                      <li key={i}>{bullet}</li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="item-actions">
                <button
                  type="button"
                  className="button button-secondary button-small"
                  onClick={() => setEditingId(item.id)}>
                  Edit
                </button>
                <button
                  type="button"
                  className="button button-danger button-small"
                  onClick={() => handleDelete(item.id)}>
                  Delete
                </button>
              </div>
            </div>
          </div>
        ),
      )}
      {editingId === "new" ? (
        <ExperienceForm initial={null} onSaved={handleSaved} onCancel={() => setEditingId(null)} />
      ) : (
        <button type="button" className="button button-secondary" onClick={() => setEditingId("new")}>
          + Add experience
        </button>
      )}
    </div>
  )
}
