# CVura — Full Database Schema

PostgreSQL. Types shown are Postgres types. All `id` columns are UUID (or BIGSERIAL if preferred — pick one and stay consistent).

---

## users
| column | type | constraints |
|---|---|---|
| id | UUID | PK, default gen_random_uuid() |
| email | TEXT | UNIQUE, NOT NULL |
| password_hash | TEXT | NOT NULL |
| plan | TEXT | NOT NULL, DEFAULT 'free' — enum: free / pro / comped |
| is_admin | BOOLEAN | NOT NULL, DEFAULT false |
| comped_reason | TEXT | NULLABLE |
| comped_by | UUID | NULLABLE, FK → users.id |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

---

## profiles
1-to-1 with users.

| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | UNIQUE, NOT NULL, FK → users.id |
| full_name | TEXT | NOT NULL |
| phone | TEXT | NULLABLE |
| location | TEXT | NULLABLE |
| linkedin_url | TEXT | NULLABLE |
| github_url | TEXT | NULLABLE |
| portfolio_url | TEXT | NULLABLE |
| desired_title | TEXT | NULLABLE |
| summary | TEXT | NULLABLE |
| career_objective | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

---

## education
| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| profile_id | UUID | NOT NULL, FK → profiles.id, INDEX |
| school | TEXT | NOT NULL |
| degree | TEXT | NULLABLE |
| field | TEXT | NULLABLE |
| start_date | DATE | NULLABLE |
| end_date | DATE | NULLABLE |

---

## experiences
| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| profile_id | UUID | NOT NULL, FK → profiles.id, INDEX |
| title | TEXT | NOT NULL |
| company | TEXT | NOT NULL |
| start_date | DATE | NULLABLE |
| end_date | DATE | NULLABLE, NULL = current |
| bullets | JSONB | NOT NULL, DEFAULT '[]' — array of strings |

---

## projects
| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| profile_id | UUID | NOT NULL, FK → profiles.id, INDEX |
| name | TEXT | NOT NULL |
| description | TEXT | NULLABLE |
| tech_stack | JSONB | DEFAULT '[]' — array of strings |
| link | TEXT | NULLABLE |

---

## skills
| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| profile_id | UUID | NOT NULL, FK → profiles.id, INDEX |
| name | TEXT | NOT NULL |
| category | TEXT | NULLABLE — technical / soft / tool |

---

## certifications
| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| profile_id | UUID | NOT NULL, FK → profiles.id, INDEX |
| name | TEXT | NOT NULL |
| issuer | TEXT | NULLABLE |
| date_earned | DATE | NULLABLE |

---

## languages
| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| profile_id | UUID | NOT NULL, FK → profiles.id, INDEX |
| name | TEXT | NOT NULL |
| proficiency | TEXT | NULLABLE — e.g. native/fluent/intermediate |

---

## awards (optional)
| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| profile_id | UUID | NOT NULL, FK → profiles.id, INDEX |
| title | TEXT | NOT NULL |
| issuer | TEXT | NULLABLE |
| date | DATE | NULLABLE |

---

## jobs
Scraped job posting.

| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | NOT NULL, FK → users.id, INDEX |
| source | TEXT | NOT NULL — linkedin / greenhouse / lever |
| title | TEXT | NOT NULL |
| company | TEXT | NULLABLE |
| raw_description | TEXT | NOT NULL |
| parsed_json | JSONB | NULLABLE — AI-extracted keywords/skills/seniority |
| created_at | TIMESTAMPTZ | DEFAULT now() |

---

## resumes
| column | type | constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | NOT NULL, FK → users.id, INDEX |
| job_id | UUID | NOT NULL, FK → jobs.id, INDEX |
| version | INTEGER | NOT NULL, DEFAULT 1 — UNIQUE with (user_id, job_id); incremented per tailor call, rows are never overwritten |
| content_json | JSONB | NOT NULL — tailored resume content |
| pdf_url | TEXT | NULLABLE — Cloudflare R2 object URL |
| match_explanation | TEXT | NULLABLE |
| created_at | TIMESTAMPTZ | DEFAULT now() |

---

## usage
1-to-1 with users. Tracks free-tier limits.

| column | type | constraints |
|---|---|---|
| user_id | UUID | PK, FK → users.id |
| resumes_generated_count | INTEGER | NOT NULL, DEFAULT 0 |
| plan_limit | INTEGER | NOT NULL, DEFAULT 3 |
| reset_at | TIMESTAMPTZ | NULLABLE — null = lifetime limit, not monthly |

---

## Relationships summary
- users 1→1 profiles
- users 1→1 usage
- users 1→N jobs
- users 1→N resumes
- profiles 1→N education, experiences, projects, skills, certifications, languages, awards
- jobs 1→N resumes (user can regenerate same job)
- users.comped_by → users.id (self-referencing, nullable)

## Indexing rules
- Index every FK column used in lookups: `profile_id`, `user_id`, `job_id`.
- Unique index on `users.email`.
- Unique index on `profiles.user_id`.

## Migration rule
All of the above created and changed only via Alembic migrations. No manual schema edits (per CLAUDE_CODE_RULES.md).