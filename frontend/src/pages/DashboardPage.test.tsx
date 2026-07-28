import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import * as jobsApi from '../api/jobs'
import type { Job } from '../api/types'
import * as authContext from '../auth/AuthContext'
import { ThemeProvider } from '../theme/ThemeContext'
import { DashboardPage } from './DashboardPage'

vi.mock('../api/jobs')
vi.mock('../auth/AuthContext')

const DONE_JOB: Job = {
  id: 'job-1',
  status: 'done',
  profile_id: 'profile-1',
  input_file: 'thesis.docx',
  output_file: 'job-1_output.docx',
  error_message: null,
  created_at: '2026-01-01T00:00:00Z',
}

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.mocked(authContext.useAuth).mockReturnValue({
      user: { id: 'user-1', email: 'student@example.com' },
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    })
    vi.mocked(jobsApi.listJobs).mockResolvedValue([DONE_JOB])
  })

  it('shows the job list with a status badge', async () => {
    render(
      <ThemeProvider>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </ThemeProvider>,
    )

    expect(await screen.findByText('thesis.docx')).toBeInTheDocument()
    expect(screen.getByText('done')).toBeInTheDocument()
  })

  it('fetches and displays the report when "View report" is clicked', async () => {
    vi.mocked(jobsApi.getJobReport).mockResolvedValue({
      id: 'report-1',
      job_id: 'job-1',
      issues_found: [],
      issues_fixed: ['applied Times New Roman 14pt'],
      created_at: '2026-01-01T00:00:00Z',
    })

    render(
      <ThemeProvider>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </ThemeProvider>,
    )

    fireEvent.click(await screen.findByRole('button', { name: 'View report' }))

    expect(await screen.findByText('applied Times New Roman 14pt')).toBeInTheDocument()
    expect(screen.getByText('No remaining issues found.')).toBeInTheDocument()
    expect(jobsApi.getJobReport).toHaveBeenCalledWith(DONE_JOB)
  })

  it('toggles the report panel closed on a second click', async () => {
    vi.mocked(jobsApi.getJobReport).mockResolvedValue({
      id: 'report-1',
      job_id: 'job-1',
      issues_found: ['left margin is 25mm, expected 30mm'],
      issues_fixed: ['applied Times New Roman 14pt'],
      created_at: '2026-01-01T00:00:00Z',
    })

    render(
      <ThemeProvider>
        <MemoryRouter>
          <DashboardPage />
        </MemoryRouter>
      </ThemeProvider>,
    )

    fireEvent.click(await screen.findByRole('button', { name: 'View report' }))
    expect(await screen.findByText('left margin is 25mm, expected 30mm')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: 'Hide report' }))
    expect(screen.queryByText('left margin is 25mm, expected 30mm')).not.toBeInTheDocument()
  })

  it('navigates to /settings when the Settings button is clicked', async () => {
    render(
      <ThemeProvider>
        <MemoryRouter initialEntries={['/dashboard']}>
          <Routes>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/settings" element={<p>Settings page</p>} />
          </Routes>
        </MemoryRouter>
      </ThemeProvider>,
    )

    fireEvent.click(await screen.findByRole('button', { name: 'Settings' }))

    expect(await screen.findByText('Settings page')).toBeInTheDocument()
  })
})
