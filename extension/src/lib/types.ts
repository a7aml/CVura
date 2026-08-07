export interface User {
  id: string
  email: string
  plan: string
}

export interface ExtractedJob {
  source: "linkedin" | "greenhouse" | "lever"
  title: string
  company: string | null
  raw_description: string
  posting_url: string
}

export interface Job {
  id: string
  user_id: string
  source: "linkedin" | "greenhouse" | "lever"
  title: string
  company: string | null
  posting_url: string | null
  raw_description: string
  parsed_json: Record<string, unknown> | null
  created_at: string
}

export interface ResumeTailorExperience {
  source_experience_id: string
  company: string
  title: string
  start_date: string | null
  end_date: string | null
  bullets: string[]
}

export interface ResumeTailorProject {
  source_project_id: string
  name: string
  bullets: string[]
}

export interface ResumeTailorResult {
  summary: string
  skills: string[]
  experience: ResumeTailorExperience[]
  projects: ResumeTailorProject[]
  match_explanation: string
  resume_id: string
  version: number
  pdf_url: string | null
}
