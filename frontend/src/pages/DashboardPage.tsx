import { useCallback, useEffect, useRef, useState, type ChangeEvent } from 'react'
import { createJob, downloadJob, listJobs } from '../api/jobs'
import { useAuth } from '../auth/AuthContext'
import type { Job } from '../api/types'

const ACTIVE_STATUSES = new Set<Job['status']>(['pending', 'processing'])
const POLL_INTERVAL_MS = 3000

export function DashboardPage() {
  const { user, logout } = useAuth()
  const [jobs, setJobs] = useState<Job[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const refreshJobs = useCallback(async () => {
    try {
      setJobs(await listJobs())
    } catch {
      // a poll tick failing is not worth surfacing - the next tick retries
    }
  }, [])

  useEffect(() => {
    void refreshJobs()
  }, [refreshJobs])

  useEffect(() => {
    if (!jobs.some((job) => ACTIVE_STATUSES.has(job.status))) return

    const interval = setInterval(() => void refreshJobs(), POLL_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [jobs, refreshJobs])

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return

    setError(null)
    setIsUploading(true)
    try {
      await createJob(file)
      await refreshJobs()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) fileInputRef.current.value = ''
    }
  }

  async function handleDownload(job: Job) {
    try {
      await downloadJob(job)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed')
    }
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Formatly</h1>
        <div className="dashboard-account">
          <span>{user?.email}</span>
          <button type="button" onClick={() => void logout()}>
            Log out
          </button>
        </div>
      </header>

      <section className="upload-section">
        <label className="upload-button">
          {isUploading ? 'Uploading…' : 'Upload .docx'}
          <input
            ref={fileInputRef}
            type="file"
            accept=".docx"
            onChange={(event) => void handleFileChange(event)}
            disabled={isUploading}
            hidden
          />
        </label>
        {error && <p className="form-error">{error}</p>}
      </section>

      <section className="jobs-section">
        <h2>Your jobs</h2>
        {jobs.length === 0 ? (
          <p className="jobs-empty">No jobs yet — upload a document to get started.</p>
        ) : (
          <ul className="job-list">
            {jobs.map((job) => (
              <li key={job.id} className="job-row">
                <span className="job-name">{job.input_file}</span>
                <span className={`status status--${job.status}`}>{job.status}</span>
                {job.status === 'done' && (
                  <button type="button" onClick={() => void handleDownload(job)}>
                    Download
                  </button>
                )}
                {job.status === 'failed' && job.error_message && (
                  <span className="job-error">{job.error_message}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
