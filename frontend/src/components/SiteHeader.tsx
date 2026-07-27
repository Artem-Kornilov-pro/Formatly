import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ThemeSwitcher } from '../theme/ThemeSwitcher'

export function SiteHeader({ children }: { children?: ReactNode }) {
  return (
    <header className="site-header">
      <Link to="/" className="site-logo">
        Formatly
      </Link>
      <div className="site-header-actions">
        <ThemeSwitcher />
        {children}
      </div>
    </header>
  )
}
