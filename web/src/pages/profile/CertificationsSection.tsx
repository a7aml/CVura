import { useState } from "react"

import { certificationApi } from "../../lib/api"
import { prefersReducedMotion } from "../../lib/motion"
import type { Certification } from "../../lib/types"

type Fields = Omit<Certification, "id">
const EMPTY: Fields = { name: "", issuer: null, date_earned: null }

function CertificationForm({
  initial,
  onSaved,
  onCancel,
}: {
  initial: Certification | null
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
      if (initial) await certificationApi.update(initial.id, fields)
      else await certificationApi.add(fields)
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
        <label htmlFor="name">Certification name</label>
        <input id="name" value={fields.name} onChange={(e) => set("name", e.target.value)} required />
      </div>
      <div className="form-row">
        <div className="field">
          <label htmlFor="issuer">Issuer</label>
          <input id="issuer" value={fields.issuer ?? ""} onChange={(e) => set("issuer", e.target.value || null)} />
        </div>
        <div className="field">
          <label htmlFor="date_earned">Date earned</label>
          <input
            id="date_earned"
            type="date"
            value={fields.date_earned ?? ""}
            onChange={(e) => set("date_earned", e.target.value || null)}
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

export default function CertificationsSection({
  items,
  onChange,
}: {
  items: Certification[]
  onChange: () => Promise<void>
}) {
  const [editingId, setEditingId] = useState<string | "new" | null>(null)
  const [removingId, setRemovingId] = useState<string | null>(null)

  async function handleDelete(id: string) {
    if (prefersReducedMotion()) {
      await certificationApi.remove(id)
      await onChange()
      return
    }
    setRemovingId(id)
    window.setTimeout(async () => {
      await certificationApi.remove(id)
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
      <h2>Certifications</h2>
      {items.length === 0 && editingId !== "new" && <p className="empty-state">No certifications added yet.</p>}
      {items.map((item) =>
        editingId === item.id ? (
          <CertificationForm
            key={item.id}
            initial={item}
            onSaved={handleSaved}
            onCancel={() => setEditingId(null)}
          />
        ) : (
          <div className={`item-card ${removingId === item.id ? "item-card-removing" : ""}`} key={item.id}>
            <div className="item-card-head">
              <div>
                <div className="item-title">{item.name}</div>
                <div className="item-subtitle">{item.issuer}</div>
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
        <CertificationForm initial={null} onSaved={handleSaved} onCancel={() => setEditingId(null)} />
      ) : (
        <button type="button" className="button button-secondary" onClick={() => setEditingId("new")}>
          + Add certification
        </button>
      )}
    </div>
  )
}
