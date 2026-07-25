import { apiFetch, extractErrorMessage } from './client'
import type { Job } from './types'

export async function listJobs(): Promise<Job[]> {
  const response = await apiFetch('/jobs')
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, 'Failed to load jobs'))
  }
  return response.json()
}

export async function createJob(file: File): Promise<Job> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await apiFetch('/jobs', { method: 'POST', body: formData })
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, 'Upload failed'))
  }
  return response.json()
}

function filenameFromContentDisposition(header: string | null): string | null {
  if (!header) return null
  const match = /filename="?([^"]+)"?/.exec(header)
  return match ? match[1] : null
}

export async function downloadJob(job: Job): Promise<void> {
  const response = await apiFetch(`/jobs/${job.id}/download`)
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response, 'Download failed'))
  }

  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download =
    filenameFromContentDisposition(response.headers.get('content-disposition')) ??
    `${job.input_file}_formatted.docx`
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}
