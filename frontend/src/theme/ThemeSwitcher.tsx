import { THEMES, useTheme, type Theme } from './ThemeContext'

const THEME_LABELS: Record<Theme, string> = {
  light: 'Light',
  dark: 'Dark',
  sepia: 'Sepia',
  ocean: 'Ocean',
}

export function ThemeSwitcher() {
  const { theme, setTheme } = useTheme()

  return (
    <div className="theme-switcher" role="radiogroup" aria-label="Color theme">
      {THEMES.map((option) => (
        <button
          key={option}
          type="button"
          role="radio"
          aria-checked={theme === option}
          aria-label={THEME_LABELS[option]}
          title={THEME_LABELS[option]}
          className={`theme-swatch theme-swatch--${option}`}
          data-active={theme === option || undefined}
          onClick={() => setTheme(option)}
        />
      ))}
    </div>
  )
}
