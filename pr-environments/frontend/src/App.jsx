import { useState, useEffect } from 'react'
import './App.css'

const API = (import.meta.env.VITE_BACKEND_URL || '').replace(/\/$/, '')

const EMPTY_FORM = { name: '', route: '', description: '', color: '', top_speed: '' }

export default function App() {
  const [trains, setTrains] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState(null)
  const [dark, setDark] = useState(false)

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
  }, [dark])

  async function loadTrains() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API}/trains`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      setTrains(await res.json())
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadTrains() }, [])

  function openModal() { setForm(EMPTY_FORM); setSubmitError(null); setModalOpen(true) }
  function closeModal() { setModalOpen(false) }

  async function handleSubmit(e) {
    e.preventDefault()
    setSubmitting(true)
    setSubmitError(null)
    const body = { name: form.name, route: form.route }
    if (form.description) body.description = form.description
    if (form.color)     body.color     = form.color
    if (form.top_speed) body.top_speed = parseInt(form.top_speed, 10)
    try {
      const res = await fetch(`${API}/trains`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      closeModal()
      loadTrains()
    } catch (e) {
      setSubmitError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <header>
        <h1>Trains</h1>
        <div className="header-actions">
          <button className="btn-toggle" onClick={() => setDark(d => !d)} title="Toggle dark mode">
            {dark ? '☀️' : '🌙'}
          </button>
          <button className="btn-primary" onClick={openModal}>+ Add Train</button>
        </div>
      </header>

      <main>
        {loading && <p className="status">Loading…</p>}
        {error && <p className="status error">Failed to load trains: {error}</p>}
        {!loading && !error && trains.length === 0 && (
          <p className="status">No trains yet — add one!</p>
        )}
        {!loading && trains.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Route</th>
                <th>Description</th>
                <th>Color</th>
                <th>Top Speed</th>
              </tr>
            </thead>
            <tbody>
              {trains.map(t => (
                <tr key={t.id}>
                  <td>{t.name}</td>
                  <td>{t.route}</td>
                  <td>{t.description || '—'}</td>
                  <td>
                    {t.color
                      ? <><span className="swatch" style={{ background: t.color }} />{t.color}</>
                      : '—'}
                  </td>
                  <td>{t.top_speed != null ? `${t.top_speed} mph` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </main>

      {modalOpen && (
        <div className="overlay" onClick={e => e.target === e.currentTarget && closeModal()}>
          <div className="modal">
            <h2>Add Train</h2>
            <form onSubmit={handleSubmit}>
              <Field label="Name" required>
                <input value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} placeholder="Acela" required />
              </Field>
              <Field label="Route" required>
                <input value={form.route} onChange={e => setForm(f => ({ ...f, route: e.target.value }))} placeholder="Boston → New York" required />
              </Field>
              <Field label="Description">
                <input value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="Optional" />
              </Field>
              <Field label="Color">
                <input value={form.color} onChange={e => setForm(f => ({ ...f, color: e.target.value }))} placeholder="#cc0000" />
              </Field>
              <Field label="Top Speed (mph)">
                <input type="number" value={form.top_speed} onChange={e => setForm(f => ({ ...f, top_speed: e.target.value }))} placeholder="150" min="0" />
              </Field>
              {submitError && <p className="submit-error">{submitError}</p>}
              <div className="modal-actions">
                <button type="button" className="btn-ghost" onClick={closeModal}>Cancel</button>
                <button type="submit" className="btn-primary" disabled={submitting}>
                  {submitting ? 'Adding…' : 'Add Train'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}

function Field({ label, required, children }) {
  return (
    <div className="field">
      <label>{label}{required && <span className="req"> *</span>}</label>
      {children}
    </div>
  )
}
