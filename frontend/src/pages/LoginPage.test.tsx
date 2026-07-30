import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as authApi from '../api/auth'
import { AuthProvider } from '../auth/AuthProvider'
import { ThemeProvider } from '../theme/ThemeProvider'
import { LoginPage } from './LoginPage'

vi.mock('../api/auth')

describe('LoginPage', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.mocked(authApi.login).mockReset()
    vi.mocked(authApi.fetchCurrentUser).mockReset()
  })

  it('logs in and navigates to the dashboard on success', async () => {
    vi.mocked(authApi.login).mockResolvedValue(undefined)
    vi.mocked(authApi.fetchCurrentUser).mockResolvedValue({
      id: '1',
      email: 'student@example.com',
    })

    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/login']}>
          <AuthProvider>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/dashboard" element={<p>Dashboard</p>} />
            </Routes>
          </AuthProvider>
        </MemoryRouter>
      </ThemeProvider>,
    )

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'student@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'correct-horse-battery-staple' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Log in' }))

    expect(await screen.findByText('Dashboard')).toBeInTheDocument()
    expect(authApi.login).toHaveBeenCalledWith('student@example.com', 'correct-horse-battery-staple')
  })

  it('shows an error message when login fails', async () => {
    vi.mocked(authApi.login).mockRejectedValue(new Error('Invalid email or password'))

    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/login']}>
          <AuthProvider>
            <LoginPage />
          </AuthProvider>
        </MemoryRouter>
      </ThemeProvider>,
    )

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'student@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'wrong-password' } })
    fireEvent.click(screen.getByRole('button', { name: 'Log in' }))

    expect(await screen.findByText('Invalid email or password')).toBeInTheDocument()
  })
})
