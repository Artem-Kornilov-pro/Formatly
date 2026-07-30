import { createContext, useContext } from 'react'

export const THEMES = ['light', 'dark', 'sepia', 'ocean'] as const
export type Theme = (typeof THEMES)[number]

export const THEME_STORAGE_KEY = 'formatly-theme'

function isTheme(value: string | null): value is Theme {
  return THEMES.includes(value as Theme)
}

export function getInitialTheme(): Theme {
  const stored = localStorage.getItem(THEME_STORAGE_KEY)
  if (isTheme(stored)) return stored
  return window.matchMedia?.('(prefers-color-scheme: dark)')?.matches ? 'dark' : 'light'
}

export interface ThemeContextValue {
  theme: Theme
  setTheme: (theme: Theme) => void
}

export const ThemeContext = createContext<ThemeContextValue | undefined>(undefined)

export function useTheme(): ThemeContextValue {
  const context = useContext(ThemeContext)
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
