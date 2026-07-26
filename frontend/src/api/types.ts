export interface UserOut {
  id: string
  email: string
}

export interface TokenPair {
  access_token: string
  refresh_token: string
  token_type: string
}

export type JobStatus = 'pending' | 'processing' | 'done' | 'failed'

export interface Job {
  id: string
  status: JobStatus
  profile_id: string
  input_file: string
  output_file: string | null
  error_message: string | null
  created_at: string
}

export interface ValidationReport {
  id: string
  job_id: string
  issues_found: string[]
  issues_fixed: string[]
  created_at: string
}
