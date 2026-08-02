export interface User {
  id: string
  email: string
  plan: string
}

export interface Education {
  id: string
  school: string
  degree: string | null
  field: string | null
  start_date: string | null
  end_date: string | null
}

export interface Experience {
  id: string
  title: string
  company: string
  start_date: string | null
  end_date: string | null
  bullets: string[]
}

export interface Project {
  id: string
  name: string
  description: string | null
  tech_stack: string[]
  link: string | null
}

export interface Skill {
  id: string
  name: string
  category: string | null
}

export interface Certification {
  id: string
  name: string
  issuer: string | null
  date_earned: string | null
}

export interface Language {
  id: string
  name: string
  proficiency: string | null
}

export interface Award {
  id: string
  title: string
  issuer: string | null
  date: string | null
}

export interface Profile {
  id: string
  user_id: string
  full_name: string
  phone: string | null
  location: string | null
  linkedin_url: string | null
  github_url: string | null
  portfolio_url: string | null
  desired_title: string | null
  summary: string | null
  career_objective: string | null
}

export interface FullProfile extends Profile {
  education: Education[]
  experiences: Experience[]
  projects: Project[]
  skills: Skill[]
  certifications: Certification[]
  languages: Language[]
  awards: Award[]
}

export type ProfileFields = Omit<Profile, "id" | "user_id">
