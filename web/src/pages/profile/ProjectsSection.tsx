import { useState } from "react"

import { projectApi } from "../../lib/api"
import { prefersReducedMotion } from "../../lib/motion"
import type { Project } from "../../lib/types"

type Fields = Omit<Project, "id">
const EMPTY: Fields = { name: "", description: null, tech_stack: [], link: null }

function ProjectForm({
  initial,
  onSaved,
  onCancel,
}: {
  initial: Project | null
  onSaved: () => Promise<void>
  onCancel: () => void
}) {
  const [fields, setFields] = useState<Fields>(initial ?? EMPTY)
  const [techText, setTechText] = useState((initial?.tech_stack ?? []).join(", "))
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function set<K extends keyof Fields>(key: K, value: Fields[K]) {
    setFields((f) => ({ ...f, [key]: value }))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setError(null)
    const tech_stack = techText.split(",").map((t) => t.trim()).filter(Boolean)
    const payload = { ...fields, tech_stack }
    try {
      if (initial) await projectApi.update(initial.id, payload)
      else await projectApi.add(payload)
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
        <label htmlFor="name">Project name</label>
        <input id="name" value={fields.name} onChange={(e) => set("name", e.target.value)} required />
      </div>
      <div className="field">
        <label htmlFor="description">Description</label>
        <textarea
          id="description"
          value={fields.description ?? ""}
          onChange={(e) => set("description", e.target.value || null)}
        />
      </div>
      <div className="form-row">
        <div className="field">
          <label htmlFor="tech_stack">Tech stack (comma-separated)</label>
          <input id="tech_stack" value={techText} onChange={(e) => setTechText(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="link">Link</label>
          <input id="link" value={fields.link ?? ""} onChange={(e) => set("link", e.target.value || null)} />
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

export default function ProjectsSection({ items, onChange }: { items: Project[]; onChange: () => Promise<void> }) {
  const [editingId, setEditingId] = useState<string | "new" | null>(null)
  const [removingId, setRemovingId] = useState<string | null>(null)

  async function handleDelete(id: string) {
    if (prefersReducedMotion()) {
      await projectApi.remove(id)
      await onChange()
      return
    }
    setRemovingId(id)
    window.setTimeout(async () => {
      await projectApi.remove(id)
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
      <h2>Projects</h2>
      {items.length === 0 && editingId !== "new" && <p className="empty-state">No projects added yet.</p>}
      {items.map((item) =>
        editingId === item.id ? (
          <ProjectForm key={item.id} initial={item} onSaved={handleSaved} onCancel={() => setEditingId(null)} />
        ) : (
          <div className={`item-card ${removingId === item.id ? "item-card-removing" : ""}`} key={item.id}>
            <div className="item-card-head">
              <div>
                <div className="item-title">{item.name}</div>
                <div className="item-subtitle">{item.tech_stack.join(", ")}</div>
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
        <ProjectForm initial={null} onSaved={handleSaved} onCancel={() => setEditingId(null)} />
      ) : (
        <button type="button" className="button button-secondary" onClick={() => setEditingId("new")}>
          + Add project
        </button>
      )}
    </div>
  )
}
