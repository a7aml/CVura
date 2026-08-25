# CVura

**CVura** is a SaaS Chrome extension that generates an ATS-friendly, job-specific resume for any job posting in under a minute — automatically, truthfully, with no invented experience.

Instead of maintaining multiple resume versions, users create a single **Master Career Profile** as their source of truth. When they open a job posting on LinkedIn, Greenhouse, or Lever, CVura analyzes the job description and generates a tailored, ATS-safe PDF resume using only real profile data — the AI is never allowed to fabricate experience, skills, or credentials.

## How it works

1. **Build your profile** — fill in your career history manually, or upload an existing resume and let CVura extract it automatically (AI-assisted, but only ever populates fields with data actually present in your resume — never invented).
2. **Browse job postings** — CVura's extension detects supported job boards (LinkedIn, Greenhouse, Lever) and extracts the job description.
3. **AI analyzes the job** — the description is parsed into structured data: required skills, technologies, seniority, responsibilities, and ATS keywords.
4. **Deterministic selection** — a pure, non-AI scoring algorithm matches your profile's experiences, projects, and skills against the job's requirements — no AI involved in this step, fully explainable and testable.
5. **AI tailors the content** — a single AI call rewrites only the *selected* subset of your profile into resume-ready language. The AI never sees your full profile, which minimizes any risk of it inventing or blending unrelated experience.
6. **Get your PDF** — a clean, ATS-safe, single-column resume (Times New Roman, black on white, no tables/graphics) is generated and ready to download.

## Tech stack

| Layer | Technology |
|---|---|
| Extension | TypeScript, React, [Plasmo](https://www.plasmo.com/) |
| Backend | Python, FastAPI (async) |
| Database | PostgreSQL via [Supabase](https://supabase.com/) |
| ORM / Migrations | SQLAlchemy + Alembic |
| Auth | In-house — JWT + HTTP-only cookies, Argon2 password hashing, Google OAuth |
| AI | OpenAI, structured output / JSON schema mode |
| PDF generation | [Typst](https://typst.app/) |
| File storage | Cloudflare R2 (private bucket, presigned URLs) |
| Web app | React + Vite, hosted on [Vercel](https://vercel.com/) |
| Backend hosting | [Railway](https://railway.app/) |

## Architecture

CVura's backend follows a **modular monolith** with strict layering:

```
routers/        → HTTP layer only, no business logic
services/        → business logic
repositories/     → database access only
schemas/        → Pydantic validation
ai/           → isolated prompt + AI client logic
```

Guiding constraints: no file over ~300 lines, no function over ~40 lines. Full conventions are documented in [`CLAUDE_CODE_RULES.md`](./CLAUDE_CODE_RULES.md).

## Project structure

```
CVura/
├── backend/       # FastAPI backend (routers, services, repositories, schemas, ai/)
├── extension/     # Plasmo + React Chrome extension
├── web/          # React + Vite marketing site and web app (login, profile builder)
├── DB_SCHEMA.md    # Full database schema reference
└── CLAUDE_CODE_RULES.md  # Architecture and coding conventions
```

## Core principles

- **Truthful by design.** The AI tailoring step only ever receives pre-selected, real profile data — it rewrites and reprioritizes, but never invents.
- **Deterministic where possible.** Matching a profile against a job's requirements is plain, testable code — not an AI call. AI is used only where judgment/language generation is genuinely needed.
- **ATS-safe output.** Resumes are generated in a single-column, plain-text-friendly layout designed to parse cleanly through applicant tracking systems.
- **Security-first.** Argon2 password hashing, JWT + HTTP-only cookies, rate limiting on auth and AI-cost-bearing endpoints, ownership checks (IDOR protection) on every user resource, and private object storage with time-limited access links.

## Status

CVura is in active development. Core resume generation (profile → job analysis → tailoring → PDF) is functional end-to-end. Resume version history and billing/subscription management are in progress.

