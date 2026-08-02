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
