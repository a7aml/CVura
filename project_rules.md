# Project Rules for Claude Code

These rules are non-negotiable. Follow them on every task, every file, every commit.

## 1. Architecture

- Modular monolith. No microservices. No new services unless explicitly instructed.
- Layers, strict separation, never skip a layer:
  - `routers/` → request/response only. No business logic. No DB queries.
  - `services/` → business logic only. Calls repositories, not DB directly.
  - `repositories/` → DB access only. No business logic.
  - `schemas/` → pydantic validation, input/output shape only.
  - `ai/` → prompt building + model calls, isolated from services logic.
- A router must never import a DB model or session directly.
- A service must never build a raw SQL/ORM query directly — always through a repository.
- No file may exceed ~300 lines. If it grows past that, split it.
- No function may exceed ~40 lines. If it grows past that, split it.
- One responsibility per file, per class, per function. If a function does two things, split it.

## 2. No Spaghetti Code

- No business logic inside routers.
- No copy-pasted logic. If logic repeats twice, extract a shared function.
- No God objects/files (a "utils.py" that does everything is forbidden). Name modules by what they do.
- No implicit magic. No hidden side effects. Functions do what their name says, nothing more.
- Every new feature must fit into the existing folder structure. Do not invent new top-level folders without asking.
- Comment "why," not "what." Do not comment obvious code.

## 3. Security (mandatory, never skip)

- Passwords: Argon2 hash only. Never log, print, or store plaintext passwords.
- Auth: JWT short-lived access token + refresh token. Tokens in HTTP-only, Secure, SameSite cookies. Never in localStorage.
- Rate limit: `/auth/login`, `/auth/signup`, and all AI-calling endpoints.
- Validate and sanitize every input from the extension (scraped job descriptions included) before using it — treat all scraped content as untrusted.
- CORS: restrict to the extension's origin only. Never use `*`.
- No secrets in code. All secrets/keys via environment variables, never committed.
- HTTPS enforced everywhere in deployment config.
- Every DB query must use parameterized queries via the ORM — no raw string-built SQL.
- Any endpoint touching user data must check the authenticated user owns that data (no IDOR).
- Log security-relevant events (login attempts, resume generation) without logging sensitive personal data.

## 4. Scalability

- All endpoints async (`async def`), non-blocking I/O for DB and AI calls.
- Stateless backend — no in-memory session state. Everything needed to serve a request comes from JWT + DB.
- DB: index foreign keys used in lookups (`user_id`, `job_id`, `resume_id`).
- Design AI/PDF generation endpoints so they can be moved behind a queue (Celery/Redis) later without changing the API contract — but do NOT implement the queue now unless asked.
- Cache repeat job-description analysis results by a hash of the JD text before calling AI again.
- PDFs and generated files go to object storage (Cloudflare R2), never local disk.
- Use connection pooling for the DB (SQLAlchemy async engine pool).

## 5. AI Rules

- The AI must never invent experience, skills, tools, or achievements not present in the user's profile.
- Every AI prompt dealing with resume content must explicitly instruct: "Only use facts provided. Do not fabricate. Omit rather than invent."
- AI calls are isolated in `/ai`. Services call `/ai`, never build prompts inline elsewhere.
- Validate AI output against a strict schema before returning it to the client. Reject and retry if malformed.

## 6. Process Rules for Claude Code

- Before adding a new dependency, ask: is it necessary for MVP? If not essential, do not add it.
- Do not build anything from the "Do NOT build yet" list (cover letters, job tracker, LinkedIn import, multiple templates, analytics dashboard, AI chatbot, etc.) unless explicitly told to.
- Do not refactor unrelated code while implementing a feature — stay scoped to the task.
- Write or update tests for any new service/repository logic.
- Every migration goes through Alembic — no manual schema edits.
- If a requested change conflicts with these rules, stop and flag the conflict instead of silently deviating.

## 7. Folder Structure (mandatory, do not deviate)

Backend:
```
/backend
  /app
    main.py
    /core
      config.py
      security.py
      deps.py
    /routers
      auth.py
      profile.py
      jobs.py
      resumes.py
      billing.py
    /services
      job_analysis_service.py
      resume_tailor_service.py
      pdf_service.py
      billing_service.py
    /repositories
      user_repo.py
      profile_repo.py
      job_repo.py
      resume_repo.py
    /models
      user.py
      profile.py
      job.py
      resume.py
    /schemas
      user.py
      profile.py
      job.py
      resume.py
    /ai
      prompts.py
      client.py
      parsers.py
  /alembic
    versions/
  /tests
  Dockerfile
  requirements.txt
```

Extension:
```
/extension
  /src
    /contents
      linkedin.ts
      greenhouse.ts
      lever.ts
      detect.ts
    /popup
      Popup.tsx
      /screens
        Login.tsx
        ProfileBuilder.tsx
        JobAnalyze.tsx
        ResumeResult.tsx
        History.tsx
    /background
      index.ts
    /lib
      api.ts
      auth.ts
      types.ts
  package.json
  plasmo.config.ts
```

No new top-level folders. No files outside this structure without explicit approval.

## 8. Build Order (strict sequence, no skipping ahead)

Features must be built and working in this order. Do not start a feature until the one before it is done and tested:

1. Auth (signup, login, JWT, cookies)
2. Master Career Profile (create, edit, store)
3. Job description extraction (extension scraping, one board at a time: LinkedIn → Greenhouse → Lever)
4. AI job analysis (JD → structured JSON)
5. AI resume tailoring (profile + JD JSON → tailored resume JSON)
6. ATS PDF generation
7. Resume version history
8. Billing / plan limits (free tier count, Pro upgrade)

Do not jump to step 5 if step 3 is unfinished. Do not add polish or extra features mid-sequence — finish the current step's core function first, then move to the next.

## 9. Git & GitHub Workflow

- Repo: `github.com/a7aml/CVura` (main branch).
- After every completed feature/step (see Build Order), commit and push to this repo before moving to the next step.
- Never leave finished work uncommitted.
- Commit messages must be clear and scoped, format: `feat(scope): short description` (e.g. `feat(auth): add signup/login with JWT + argon2`).
  - Use `fix(scope): ...` for bug fixes.
  - Use `chore(scope): ...` for setup/config/deps.
  - Use `docs: ...` for documentation.
- No vague commits ("update", "fix stuff", "wip"). One commit = one clear purpose.
- Do not commit secrets, `.env` files, or credentials. Ensure `.gitignore` covers them.

## 10. MVP Scope Discipline

Build only these features, nothing more:
 Chrome extension, auth, Master Career Profile, manual profile editing, job extraction, AI job analysis, AI resume tailoring, ATS PDF generation, resume version history.

Nothing else, until MVP is validated.