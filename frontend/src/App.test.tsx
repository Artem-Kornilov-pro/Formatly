import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import App from './App'
import { AuthProvider } from './auth/AuthProvider'
import { ThemeProvider } from './theme/ThemeProvider'

describe('App', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('shows the public landing page at / for an unauthenticated visitor', async () => {
    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/']}>
          <AuthProvider>
            <App />
          </AuthProvider>
        </MemoryRouter>
      </ThemeProvider>,
    )

    expect(await screen.findByRole('link', { name: 'Get started' })).toBeInTheDocument()
  })

  it('redirects an unauthenticated visitor from /dashboard to the login page', async () => {
    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/dashboard']}>
          <AuthProvider>
            <App />
          </AuthProvider>
        </MemoryRouter>
      </ThemeProvider>,
    )

    expect(await screen.findByRole('heading', { name: 'Log in' })).toBeInTheDocument()
  })
})
