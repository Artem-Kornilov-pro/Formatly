import { API_URL, apiFetch, extractErrorMessage } from './client'
import { clearTokens, getRefreshToken, setTokens } from './tokenStorage'
import type { TokenPair, UserOut } from './types'

export async function register(email: string, password: string): Promise<void> {
  const response = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, 'Registration failed'))
  }
}

export async function login(email: string, password: string): Promise<void> {
  const response = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  })
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, 'Invalid email or password'))
  }
  const tokens: TokenPair = await response.json()
  setTokens(tokens.access_token, tokens.refresh_token)
}

export async function fetchCurrentUser(): Promise<UserOut | null> {
  const response = await apiFetch('/auth/me')
  if (!response.ok) return null
  return response.json()
}

export async function logout(): Promise<void> {
  const refreshToken = getRefreshToken()
  if (refreshToken) {
    await fetch(`${API_URL}/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    }).catch(() => {
      // best-effort - the tokens are being cleared client-side regardless
    })
  }
  clearTokens()
}
