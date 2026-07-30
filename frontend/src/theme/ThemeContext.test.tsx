import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { THEME_STORAGE_KEY } from './ThemeContext'
import { ThemeProvider } from './ThemeProvider'
import { ThemeSwitcher } from './ThemeSwitcher'

function renderSwitcher() {
  return render(
    <ThemeProvider>
      <ThemeSwitcher />
    </ThemeProvider>,
  )
}

describe('ThemeProvider', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  it('defaults to light when nothing is stored and there is no OS dark preference', () => {
    renderSwitcher()

    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(screen.getByRole('radio', { name: 'Light' })).toHaveAttribute('aria-checked', 'true')
  })

  it('restores a previously selected theme from localStorage', () => {
    localStorage.setItem(THEME_STORAGE_KEY, 'sepia')

    renderSwitcher()

    expect(document.documentElement.getAttribute('data-theme')).toBe('sepia')
    expect(screen.getByRole('radio', { name: 'Sepia' })).toHaveAttribute('aria-checked', 'true')
  })

  it('switches theme, updates the DOM attribute, and persists the choice', () => {
    renderSwitcher()

    fireEvent.click(screen.getByRole('radio', { name: 'Ocean' }))

    expect(document.documentElement.getAttribute('data-theme')).toBe('ocean')
    expect(localStorage.getItem(THEME_STORAGE_KEY)).toBe('ocean')
    expect(screen.getByRole('radio', { name: 'Ocean' })).toHaveAttribute('aria-checked', 'true')
    expect(screen.getByRole('radio', { name: 'Light' })).toHaveAttribute('aria-checked', 'false')
  })

  it('falls back to dark when the OS prefers dark and nothing is stored', () => {
    vi.stubGlobal(
      'matchMedia',
      vi.fn().mockReturnValue({ matches: true }),
    )

    renderSwitcher()

    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')

    vi.unstubAllGlobals()
  })
})
