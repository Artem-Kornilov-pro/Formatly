import { apiFetch, extractErrorMessage } from './client'
import type { FormattingRules } from './types'

export async function getMyProfile(): Promise<FormattingRules> {
  const response = await apiFetch('/profiles/me')
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, 'Failed to load settings'))
  }
  return response.json()
}

export async function updateMyProfile(rules: FormattingRules): Promise<FormattingRules> {
  const response = await apiFetch('/profiles/me', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(rules),
  })
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, 'Failed to save settings'))
  }
  return response.json()
}
