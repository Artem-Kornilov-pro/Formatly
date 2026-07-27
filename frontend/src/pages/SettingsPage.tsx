import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { getMyProfile, updateMyProfile } from '../api/profiles'
import { ThemeSwitcher } from '../theme/ThemeSwitcher'
import type { FormattingRules, MarginsMm } from '../api/types'

export function SettingsPage() {
  const [rules, setRules] = useState<FormattingRules | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    getMyProfile()
      .then(setRules)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load settings'))
      .finally(() => setIsLoading(false))
  }, [])

  function update<K extends keyof FormattingRules>(key: K, value: FormattingRules[K]) {
    setRules((prev) => (prev ? { ...prev, [key]: value } : prev))
    setSaved(false)
  }

  function updateMargin(side: keyof MarginsMm, value: number) {
    setRules((prev) =>
      prev ? { ...prev, margins_mm: { ...prev.margins_mm, [side]: value } } : prev,
    )
    setSaved(false)
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!rules) return

    setError(null)
    setSaved(false)
    setIsSaving(true)
    try {
      setRules(await updateMyProfile(rules))
      setSaved(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save settings')
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return <p className="loading">Loading…</p>
  }

  if (!rules) {
    return <p className="form-error">{error ?? 'Failed to load settings'}</p>
  }

  return (
    <div className="settings-page">
      <div className="settings-header">
        <h1>Formatting settings</h1>
        <div className="site-header-actions">
          <ThemeSwitcher />
          <Link to="/dashboard">Back to dashboard</Link>
        </div>
      </div>

      <form className="settings-form" onSubmit={handleSubmit}>
        {error && <p className="form-error">{error}</p>}
        {saved && <p className="form-success">Settings saved.</p>}

        <fieldset>
          <legend>Font</legend>
          <label>
            Font family
            <input
              type="text"
              value={rules.font_family}
              onChange={(event) => update('font_family', event.target.value)}
            />
          </label>
          <label>
            Font size (pt)
            <input
              type="number"
              min={1}
              value={rules.font_size_pt}
              onChange={(event) => update('font_size_pt', Number(event.target.value))}
            />
          </label>
          <label>
            Line spacing
            <input
              type="number"
              min={1}
              step={0.1}
              value={rules.line_spacing}
              onChange={(event) => update('line_spacing', Number(event.target.value))}
            />
          </label>
        </fieldset>

        <fieldset>
          <legend>Page margins (mm)</legend>
          <label>
            Top
            <input
              type="number"
              min={0}
              step="any"
              value={rules.margins_mm.top}
              onChange={(event) => updateMargin('top', Number(event.target.value))}
            />
          </label>
          <label>
            Bottom
            <input
              type="number"
              min={0}
              step="any"
              value={rules.margins_mm.bottom}
              onChange={(event) => updateMargin('bottom', Number(event.target.value))}
            />
          </label>
          <label>
            Left
            <input
              type="number"
              min={0}
              step="any"
              value={rules.margins_mm.left}
              onChange={(event) => updateMargin('left', Number(event.target.value))}
            />
          </label>
          <label>
            Right
            <input
              type="number"
              min={0}
              step="any"
              value={rules.margins_mm.right}
              onChange={(event) => updateMargin('right', Number(event.target.value))}
            />
          </label>
        </fieldset>

        <fieldset>
          <legend>Headings</legend>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={rules.bold_headings}
              onChange={(event) => update('bold_headings', event.target.checked)}
            />
            Bold
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={rules.italic_headings}
              onChange={(event) => update('italic_headings', event.target.checked)}
            />
            Italic
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={rules.center_headings}
              onChange={(event) => update('center_headings', event.target.checked)}
            />
            Centered
          </label>
          <label>
            Size increase over body text (pt)
            <input
              type="number"
              min={0}
              value={rules.heading_size_bump_pt}
              onChange={(event) => update('heading_size_bump_pt', Number(event.target.value))}
            />
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={rules.page_break_before_heading_1}
              onChange={(event) =>
                update('page_break_before_heading_1', event.target.checked)
              }
            />
            Start each chapter (level-1 heading) on a new page
          </label>
        </fieldset>

        <fieldset>
          <legend>Body paragraphs</legend>
          <label>
            Alignment
            <select
              value={rules.paragraph_alignment}
              onChange={(event) =>
                update(
                  'paragraph_alignment',
                  event.target.value as FormattingRules['paragraph_alignment'],
                )
              }
            >
              <option value="left">Left</option>
              <option value="center">Center</option>
              <option value="right">Right</option>
              <option value="justify">Justify</option>
            </select>
          </label>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={rules.paragraph_indent_enabled}
              onChange={(event) => update('paragraph_indent_enabled', event.target.checked)}
            />
            Indent the first line of each paragraph
          </label>
          <label>
            First-line indent (mm)
            <input
              type="number"
              min={0}
              step="any"
              disabled={!rules.paragraph_indent_enabled}
              value={rules.paragraph_indent_mm}
              onChange={(event) => update('paragraph_indent_mm', Number(event.target.value))}
            />
          </label>
        </fieldset>

        <fieldset>
          <legend>Table of contents</legend>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={rules.generate_toc}
              onChange={(event) => update('generate_toc', event.target.checked)}
            />
            Insert an automatic table of contents ("СОДЕРЖАНИЕ")
          </label>
        </fieldset>

        <fieldset>
          <legend>AI assistance</legend>
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={rules.ai_light_editing_enabled}
              onChange={(event) => update('ai_light_editing_enabled', event.target.checked)}
            />
            Let AI add a missing title or complete obviously cut-off sentences
          </label>
        </fieldset>

        <button type="submit" disabled={isSaving}>
          {isSaving ? 'Saving…' : 'Save settings'}
        </button>
      </form>
    </div>
  )
}
