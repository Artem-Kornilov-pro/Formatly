import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it } from 'vitest'
import App from './App'
import { AuthProvider } from './auth/AuthContext'

describe('App', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('redirects an unauthenticated visitor from / to the login page', async () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AuthProvider>
          <App />
        </AuthProvider>
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Log in' })).toBeInTheDocument()
  })
})
