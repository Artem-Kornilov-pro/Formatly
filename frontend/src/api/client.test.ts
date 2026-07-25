import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { apiFetch } from './client'
import { clearTokens, getAccessToken, getRefreshToken, setTokens } from './tokenStorage'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('apiFetch', () => {
  beforeEach(() => {
    clearTokens()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('attaches the access token to the request', async () => {
    setTokens('access-1', 'refresh-1')
    const fetchMock = vi.fn(async (_url: string, _options?: RequestInit) =>
      jsonResponse(200, { ok: true }),
    )
    vi.stubGlobal('fetch', fetchMock)

    const response = await apiFetch('/jobs')

    expect(response.status).toBe(200)
    const [, options] = fetchMock.mock.calls[0]
    expect(new Headers(options?.headers).get('Authorization')).toBe('Bearer access-1')
  })

  it('refreshes once and retries the request after a 401', async () => {
    setTokens('expired-access', 'refresh-1')
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (url.endsWith('/auth/refresh')) {
        return jsonResponse(200, { access_token: 'new-access', refresh_token: 'new-refresh' })
      }
      const headers = new Headers(options?.headers)
      return headers.get('Authorization') === 'Bearer new-access'
        ? jsonResponse(200, { ok: true })
        : jsonResponse(401, { detail: 'expired' })
    })
    vi.stubGlobal('fetch', fetchMock)

    const response = await apiFetch('/jobs')

    expect(response.status).toBe(200)
    expect(getAccessToken()).toBe('new-access')
    expect(getRefreshToken()).toBe('new-refresh')
    expect(fetchMock).toHaveBeenCalledTimes(3) // original, refresh, retry
  })

  it('clears tokens and gives up when refresh also fails', async () => {
    setTokens('expired-access', 'expired-refresh')
    const fetchMock = vi.fn(async (url: string) => {
      if (url.endsWith('/auth/refresh')) {
        return jsonResponse(401, { detail: 'invalid refresh token' })
      }
      return jsonResponse(401, { detail: 'expired' })
    })
    vi.stubGlobal('fetch', fetchMock)

    const response = await apiFetch('/jobs')

    expect(response.status).toBe(401)
    expect(getAccessToken()).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })

  it('does not attempt a refresh when there was no access token to begin with', async () => {
    const fetchMock = vi.fn(async () => jsonResponse(401, { detail: 'unauthenticated' }))
    vi.stubGlobal('fetch', fetchMock)

    const response = await apiFetch('/jobs')

    expect(response.status).toBe(401)
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('shares a single in-flight refresh across concurrent 401s', async () => {
    setTokens('expired-access', 'refresh-1')
    let refreshCalls = 0
    const fetchMock = vi.fn(async (url: string, options?: RequestInit) => {
      if (url.endsWith('/auth/refresh')) {
        refreshCalls += 1
        await new Promise((resolve) => setTimeout(resolve, 5))
        return jsonResponse(200, { access_token: 'new-access', refresh_token: 'new-refresh' })
      }
      const headers = new Headers(options?.headers)
      return headers.get('Authorization') === 'Bearer new-access'
        ? jsonResponse(200, { ok: true })
        : jsonResponse(401, { detail: 'expired' })
    })
    vi.stubGlobal('fetch', fetchMock)

    const [first, second] = await Promise.all([apiFetch('/jobs'), apiFetch('/profiles')])

    expect(first.status).toBe(200)
    expect(second.status).toBe(200)
    expect(refreshCalls).toBe(1)
  })
})
