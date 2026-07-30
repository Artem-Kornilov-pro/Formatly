import { useEffect, useState, type ReactNode } from 'react'
import * as authApi from '../api/auth'
import { getAccessToken, getRefreshToken } from '../api/tokenStorage'
import type { UserOut } from '../api/types'
import { AuthContext } from './AuthContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function restoreSession() {
      if (getAccessToken() && getRefreshToken()) {
        setUser(await authApi.fetchCurrentUser())
      }
      setIsLoading(false)
    }
    void restoreSession()
  }, [])

  async function login(email: string, password: string) {
    await authApi.login(email, password)
    setUser(await authApi.fetchCurrentUser())
  }

  async function register(email: string, password: string) {
    await authApi.register(email, password)
    await login(email, password)
  }

  async function logout() {
    await authApi.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isLoading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}
