import { clearTokens, getAccessToken, getRefreshToken, setTokens } from './tokenStorage'

export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

function withAuth(headers: HeadersInit | undefined, accessToken: string | null): Headers {
  const merged = new Headers(headers)
  if (accessToken) {
    merged.set('Authorization', `Bearer ${accessToken}`)
  }
  return merged
}

// Concurrent 401s (e.g. a poll tick racing a user action) must share a single
// refresh attempt - each refresh call rotates the token pair server-side, so
// firing more than one at a time would have the second invalidate the first.
let refreshInFlight: Promise<boolean> | null = null

async function refreshTokens(): Promise<boolean> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return false

  if (!refreshInFlight) {
    refreshInFlight = (async () => {
      try {
        const response = await fetch(`${API_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken }),
        })
        if (!response.ok) return false

        const data: { access_token: string; refresh_token: string } = await response.json()
        setTokens(data.access_token, data.refresh_token)
        return true
      } catch {
        return false
      } finally {
        refreshInFlight = null
      }
    })()
  }

  return refreshInFlight
}

/** Fetch wrapper that attaches the access token and retries once via
 * refresh on a 401. Clears stored tokens if the refresh itself fails,
 * leaving the caller to notice the still-401 response. */
export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const accessToken = getAccessToken()
  const request = () =>
    fetch(`${API_URL}${path}`, { ...options, headers: withAuth(options.headers, getAccessToken()) })

  let response = await request()

  if (response.status === 401 && accessToken) {
    const refreshed = await refreshTokens()
    if (refreshed) {
      response = await request()
    } else {
      clearTokens()
    }
  }

  return response
}

export async function extractErrorMessage(response: Response, fallback: string): Promise<string> {
  try {
    const body: unknown = await response.json()
    if (body && typeof body === 'object' && 'detail' in body && typeof body.detail === 'string') {
      return body.detail
    }
  } catch {
    // response wasn't JSON - fall through to the generic message
  }
  return fallback
}
