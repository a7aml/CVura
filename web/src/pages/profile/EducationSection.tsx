import { useState } from "react"

import { educationApi } from "../../lib/api"
import { prefersReducedMotion } from "../../lib/motion"
import type { Education } from "../../lib/types"

type Fields = Omit<Education, "id">
const EMPTY: Fields = { school: "", degree: null, field: null, start_date: null, end_date: null }

function EducationForm({
  initial,
  onSaved,
  onCancel,
}: {
  initial: Education | null
  onSaved: () => Promise<void>
  onCancel: () => void
}) {
  const [fields, setFields] = useState<Fields>(initial ?? EMPTY)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function set<K extends keyof Fields>(key: K, value: Fields[K]) {
    setFields((f) => ({ ...f, [key]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    try {
      if (initial) await educationApi.update(initial.id, fields)
      else await educationApi.add(fields)
      await onSaved()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save")
    } finally {
      setSaving(false)
    }
  }

  return (
    <form className="form item-card" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="school">School</label>
        <input id="school" value={fields.school} onChange={(e) => set("school", e.target.value)} required />
      </div>
      <div className="form-row">
        <div className="field">
          <label htmlFor="degree">Degree</label>
          <input id="degree" value={fields.degree ?? ""} onChange={(e) => set("degree", e.target.value || null)} />
        </div>
        <div className="field">
          <label htmlFor="field">Field of study</label>
          <input id="field" value={fields.field ?? ""} onChange={(e) => set("field", e.target.value || null)} />
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
          <label htmlFor="end_date">End date</label>
          <input
            id="end_date"
            type="date"
            value={fields.end_date ?? ""}
            onChange={(e) => set("end_date", e.target.value || null)}
          />
        </div>
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

export default function EducationSection({
  items,
  onChange,
}: {
  items: Education[]
  onChange: () => Promise<void>
}) {
  const [editingId, setEditingId] = useState<string | "new" | null>(null)
  const [removingId, setRemovingId] = useState<string | null>(null)

  async function handleDelete(id: string) {
    if (prefersReducedMotion()) {
      await educationApi.remove(id)
      await onChange()
      return
    }
    setRemovingId(id)
    window.setTimeout(async () => {
      await educationApi.remove(id)
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
      <h2>Education</h2>
      {items.length === 0 && editingId !== "new" && <p className="empty-state">No education added yet.</p>}
      {items.map((item) =>
        editingId === item.id ? (
          <EducationForm key={item.id} initial={item} onSaved={handleSaved} onCancel={() => setEditingId(null)} />
        ) : (
          <div className={`item-card ${removingId === item.id ? "item-card-removing" : ""}`} key={item.id}>
            <div className="item-card-head">
              <div>
                <div className="item-title">{item.school}</div>
                <div className="item-subtitle">
                  {[item.degree, item.field].filter(Boolean).join(", ")}
                </div>
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
        <EducationForm initial={null} onSaved={handleSaved} onCancel={() => setEditingId(null)} />
      ) : (
        <button type="button" className="button button-secondary" onClick={() => setEditingId("new")}>
          + Add education
        </button>
      )}
    </div>
  )
}
