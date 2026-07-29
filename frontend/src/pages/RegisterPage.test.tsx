import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as authApi from '../api/auth'
import { AuthProvider } from '../auth/AuthContext'
import { ThemeProvider } from '../theme/ThemeContext'
import { RegisterPage } from './RegisterPage'

vi.mock('../api/auth')

describe('RegisterPage', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.mocked(authApi.register).mockReset()
    vi.mocked(authApi.fetchCurrentUser).mockReset()
  })

  it('shows a hint describing the password requirements', () => {
    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/register']}>
          <AuthProvider>
            <RegisterPage />
          </AuthProvider>
        </MemoryRouter>
      </ThemeProvider>,
    )

    expect(
      screen.getByText('At least 8 characters, including one special character.'),
    ).toBeInTheDocument()

    const passwordInput = screen.getByLabelText('Password')
    expect(passwordInput).toHaveAttribute('minlength', '8')
    expect(passwordInput).toHaveAttribute('pattern', '.*[^A-Za-z0-9].*')
  })

  it('registers and navigates to the dashboard on success', async () => {
    vi.mocked(authApi.register).mockResolvedValue(undefined)
    vi.mocked(authApi.fetchCurrentUser).mockResolvedValue({
      id: '1',
      email: 'student@example.com',
    })

    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/register']}>
          <AuthProvider>
            <Routes>
              <Route path="/register" element={<RegisterPage />} />
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
      target: { value: 'letters!8chars' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Register' }))

    expect(await screen.findByText('Dashboard')).toBeInTheDocument()
    expect(authApi.register).toHaveBeenCalledWith('student@example.com', 'letters!8chars')
  })

  it('shows an error message when registration fails', async () => {
    vi.mocked(authApi.register).mockRejectedValue(new Error('Email already registered'))

    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/register']}>
          <AuthProvider>
            <RegisterPage />
          </AuthProvider>
        </MemoryRouter>
      </ThemeProvider>,
    )

    fireEvent.change(screen.getByLabelText('Email'), {
      target: { value: 'student@example.com' },
    })
    fireEvent.change(screen.getByLabelText('Password'), {
      target: { value: 'letters!8chars' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Register' }))

    expect(await screen.findByText('Email already registered')).toBeInTheDocument()
  })
})
