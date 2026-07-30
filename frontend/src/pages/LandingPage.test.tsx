import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import * as authContext from '../auth/AuthContext'
import { ThemeProvider } from '../theme/ThemeProvider'
import { LandingPage } from './LandingPage'

vi.mock('../auth/AuthContext')

describe('LandingPage', () => {
  it('shows the marketing content and auth links for a logged-out visitor', () => {
    vi.mocked(authContext.useAuth).mockReturnValue({
      user: null,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/']}>
          <LandingPage />
        </MemoryRouter>
      </ThemeProvider>,
    )

    expect(screen.getByText(/GOST-formatted documents/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Get started' })).toHaveAttribute('href', '/register')

    const loginLinks = screen.getAllByRole('link', { name: 'Log in' })
    expect(loginLinks.length).toBeGreaterThan(0)
    for (const link of loginLinks) {
      expect(link).toHaveAttribute('href', '/login')
    }
  })

  it('redirects an already-authenticated visitor to the dashboard', async () => {
    vi.mocked(authContext.useAuth).mockReturnValue({
      user: { id: '1', email: 'student@example.com' },
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })

    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<p>Dashboard</p>} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>,
    )

    expect(await screen.findByText('Dashboard')).toBeInTheDocument()
  })
})
