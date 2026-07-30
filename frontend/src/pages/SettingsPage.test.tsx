import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as profilesApi from '../api/profiles'
import type { FormattingRules } from '../api/types'
import { ThemeProvider } from '../theme/ThemeProvider'
import { SettingsPage } from './SettingsPage'

vi.mock('../api/profiles')

const DEFAULT_RULES: FormattingRules = {
  font_family: 'Times New Roman',
  font_size_pt: 14,
  line_spacing: 1.5,
  margins_mm: { top: 20, bottom: 20, left: 30, right: 15 },
  bold_headings: true,
  italic_headings: false,
  center_headings: true,
  heading_size_bump_pt: 2,
  page_break_before_heading_1: false,
  paragraph_alignment: 'justify',
  paragraph_indent_enabled: true,
  paragraph_indent_mm: 12.5,
  generate_toc: true,
  ai_light_editing_enabled: true,
}

describe('SettingsPage', () => {
  beforeEach(() => {
    vi.mocked(profilesApi.getMyProfile).mockResolvedValue(DEFAULT_RULES)
    vi.mocked(profilesApi.updateMyProfile).mockImplementation(async (rules) => rules)
  })

  it('loads and displays the current settings', async () => {
    render(
      <ThemeProvider>
        <MemoryRouter>
          <SettingsPage />
        </MemoryRouter>
      </ThemeProvider>,
    )

    expect(await screen.findByDisplayValue('Times New Roman')).toBeInTheDocument()
  })

  it('saves edited settings', async () => {
    render(
      <ThemeProvider>
        <MemoryRouter>
          <SettingsPage />
        </MemoryRouter>
      </ThemeProvider>,
    )

    const fontInput = await screen.findByDisplayValue('Times New Roman')
    fireEvent.change(fontInput, { target: { value: 'Arial' } })
    // jsdom doesn't reliably dispatch the implicit form-submit event from a
    // plain click on a `type="submit"` button, so fire the submit event on
    // the form directly rather than relying on that browser behavior.
    fireEvent.submit(fontInput.closest('form')!)

    expect(await screen.findByText('Settings saved.')).toBeInTheDocument()
    expect(profilesApi.updateMyProfile).toHaveBeenCalledWith(
      expect.objectContaining({ font_family: 'Arial' }),
    )
  })

  it('saves the table of contents toggle', async () => {
    render(
      <ThemeProvider>
        <MemoryRouter>
          <SettingsPage />
        </MemoryRouter>
      </ThemeProvider>,
    )

    const tocCheckbox = await screen.findByLabelText(/automatic table of contents/i)
    expect(tocCheckbox).toBeChecked()
    fireEvent.click(tocCheckbox)
    fireEvent.submit(tocCheckbox.closest('form')!)

    expect(await screen.findByText('Settings saved.')).toBeInTheDocument()
    expect(profilesApi.updateMyProfile).toHaveBeenCalledWith(
      expect.objectContaining({ generate_toc: false }),
    )
  })

  it('saves the AI light editing toggle', async () => {
    render(
      <ThemeProvider>
        <MemoryRouter>
          <SettingsPage />
        </MemoryRouter>
      </ThemeProvider>,
    )

    const aiCheckbox = await screen.findByLabelText(/let ai add a missing title/i)
    expect(aiCheckbox).toBeChecked()
    fireEvent.click(aiCheckbox)
    fireEvent.submit(aiCheckbox.closest('form')!)

    expect(await screen.findByText('Settings saved.')).toBeInTheDocument()
    expect(profilesApi.updateMyProfile).toHaveBeenCalledWith(
      expect.objectContaining({ ai_light_editing_enabled: false }),
    )
  })

  it('shows an error message when saving fails', async () => {
    vi.mocked(profilesApi.updateMyProfile).mockRejectedValue(
      new Error('Failed to save settings'),
    )

    render(
      <ThemeProvider>
        <MemoryRouter>
          <SettingsPage />
        </MemoryRouter>
      </ThemeProvider>,
    )

    const fontInput = await screen.findByDisplayValue('Times New Roman')
    fireEvent.submit(fontInput.closest('form')!)

    expect(await screen.findByText('Failed to save settings')).toBeInTheDocument()
  })
})
