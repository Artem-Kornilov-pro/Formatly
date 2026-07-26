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

export interface MarginsMm {
  top: number
  bottom: number
  left: number
  right: number
}

export type ParagraphAlignment = 'left' | 'center' | 'right' | 'justify'

export interface FormattingRules {
  font_family: string
  font_size_pt: number
  line_spacing: number
  margins_mm: MarginsMm
  bold_headings: boolean
  italic_headings: boolean
  center_headings: boolean
  heading_size_bump_pt: number
  page_break_before_heading_1: boolean
  paragraph_alignment: ParagraphAlignment
  paragraph_indent_enabled: boolean
  paragraph_indent_mm: number
  generate_toc: boolean
}
