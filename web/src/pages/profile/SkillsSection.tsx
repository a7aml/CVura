import { useState } from "react"

import { skillApi } from "../../lib/api"
import { prefersReducedMotion } from "../../lib/motion"
import type { Skill } from "../../lib/types"

type Fields = Omit<Skill, "id">
const EMPTY: Fields = { name: "", category: null }

function SkillForm({
  initial,
  onSaved,
  onCancel,
}: {
  initial: Skill | null
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
      if (initial) await skillApi.update(initial.id, fields)
      else await skillApi.add(fields)
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
          <label htmlFor="name">Skill</label>
          <input id="name" value={fields.name} onChange={(e) => set("name", e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="category">Category (technical / soft / tool)</label>
          <input id="category" value={fields.category ?? ""} onChange={(e) => set("category", e.target.value || null)} />
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

export default function SkillsSection({ items, onChange }: { items: Skill[]; onChange: () => Promise<void> }) {
  const [editingId, setEditingId] = useState<string | "new" | null>(null)
  const [removingId, setRemovingId] = useState<string | null>(null)

  async function handleDelete(id: string) {
    if (prefersReducedMotion()) {
      await skillApi.remove(id)
      await onChange()
      return
    }
    setRemovingId(id)
    window.setTimeout(async () => {
      await skillApi.remove(id)
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
      <h2>Skills</h2>
      {items.length === 0 && editingId !== "new" && <p className="empty-state">No skills added yet.</p>}
      {items.map((item) =>
        editingId === item.id ? (
          <SkillForm key={item.id} initial={item} onSaved={handleSaved} onCancel={() => setEditingId(null)} />
        ) : (
          <div className={`item-card ${removingId === item.id ? "item-card-removing" : ""}`} key={item.id}>
            <div className="item-card-head">
              <div>
                <div className="item-title">{item.name}</div>
                {item.category && <div className="item-subtitle">{item.category}</div>}
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
        <SkillForm initial={null} onSaved={handleSaved} onCancel={() => setEditingId(null)} />
      ) : (
        <button type="button" className="button button-secondary" onClick={() => setEditingId("new")}>
          + Add skill
        </button>
      )}
    </div>
  )
}
