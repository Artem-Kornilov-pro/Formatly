import { useCallback, useEffect, useRef, useState, type ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { createJob, downloadJob, getJobReport, listJobs } from '../api/jobs'
import { useAuth } from '../auth/AuthContext'
import { ThemeSwitcher } from '../theme/ThemeSwitcher'
import type { Job, ValidationReport } from '../api/types'

const ACTIVE_STATUSES = new Set<Job['status']>(['pending', 'processing'])
const POLL_INTERVAL_MS = 3000

export function DashboardPage() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [jobs, setJobs] = useState<Job[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null)
  const [reports, setReports] = useState<Record<string, ValidationReport>>({})
  const [reportError, setReportError] = useState<string | null>(null)
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

  async function handleToggleReport(job: Job) {
    if (expandedJobId === job.id) {
      setExpandedJobId(null)
      return
    }

    setReportError(null)
    setExpandedJobId(job.id)
    if (reports[job.id]) return

    try {
      const report = await getJobReport(job)
      setReports((prev) => ({ ...prev, [job.id]: report }))
    } catch (err) {
      setReportError(err instanceof Error ? err.message : 'Failed to load report')
    }
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Formatly</h1>
        <div className="dashboard-account">
          <ThemeSwitcher />
          <span>{user?.email}</span>
          <button
            type="button"
            className="button--secondary"
            onClick={() => navigate('/settings')}
          >
            Settings
          </button>
          <button type="button" className="button--secondary" onClick={() => void logout()}>
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
            {jobs.map((job) => {
              const report = reports[job.id]
              const isExpanded = expandedJobId === job.id

              return (
                <li key={job.id} className="job-row">
                  <span className="job-name">{job.input_file}</span>
                  <span className={`status status--${job.status}`}>{job.status}</span>
                  {job.status === 'done' && (
                    <>
                      <button type="button" onClick={() => void handleDownload(job)}>
                        Download
                      </button>
                      <button
                        type="button"
                        className="button--secondary"
                        onClick={() => void handleToggleReport(job)}
                      >
                        {isExpanded ? 'Hide report' : 'View report'}
                      </button>
                    </>
                  )}
                  {job.status === 'failed' && job.error_message && (
                    <span className="job-error">{job.error_message}</span>
                  )}

                  {isExpanded && (
                    <div className="job-report">
                      {reportError && <p className="form-error">{reportError}</p>}
                      {report && (
                        <>
                          {report.issues_fixed.length > 0 && (
                            <div className="job-report-section">
                              <h3>Fixed</h3>
                              <ul>
                                {report.issues_fixed.map((item) => (
                                  <li key={item}>{item}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {report.issues_found.length > 0 ? (
                            <div className="job-report-section">
                              <h3>Remaining issues</h3>
                              <ul>
                                {report.issues_found.map((item) => (
                                  <li key={item}>{item}</li>
                                ))}
                              </ul>
                            </div>
                          ) : (
                            <p className="job-report-clean">No remaining issues found.</p>
                          )}
                        </>
                      )}
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        )}
      </section>
    </div>
  )
}
