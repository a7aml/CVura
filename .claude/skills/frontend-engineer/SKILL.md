---
name: frontend-engineer
description: Use for any Chrome extension work in this repo's extension/ folder — Plasmo config, React popup screens, TypeScript, content scripts, or background scripts. Enforces the mandatory extension folder structure, per-job-board content script separation, centralized API calls via lib/api.ts, and cookie-only JWT storage (never localStorage). Trigger on phrases like "extension", "popup screen", "content script", "scraper for", or work touching extension/src.
---

# Frontend Engineer (Chrome Extension)

Source of truth: `project_rules.md` at the repo root, specifically:
- §7 Folder Structure — Extension section
- §3 Security — JWT/cookie handling
- §8 Build Order — job board sequence (LinkedIn → Greenhouse → Lever)

## Non-negotiable rules

### 1. Mandatory folder structure — do not deviate
```
/extension/src
  /content-scripts
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
```
No new top-level folders under `extension/src`, no files placed outside this structure, without explicit user approval. If a task seems to need a new folder, ask first instead of inventing one.

### 2. Content scripts: one file per job board, no shared scraping logic dumped together
- Scraping/DOM-parsing logic for LinkedIn stays in `content-scripts/linkedin.ts`, Greenhouse in `greenhouse.ts`, Lever in `lever.ts`. Do not merge board-specific selectors/parsing into a shared file or into `detect.ts`.
- `detect.ts` only detects which board the current page belongs to and dispatches to the right scraper — it must not contain board-specific scraping logic itself.
- Per project_rules.md §8, boards are built one at a time in order: LinkedIn → Greenhouse → Lever. If asked to build Greenhouse or Lever scraping before LinkedIn is done, flag it — check with the planner-engineer skill's Build Order logic if sequencing is unclear.
- If scraping logic is genuinely shared across boards (e.g. a generic text-cleanup helper), it belongs in `lib/` (e.g. `lib/types.ts` for shared types, or a new lib helper only after asking — see rule 1), not copy-pasted into each board file, and not merged into one board's file.

### 3. API calls centralized in lib/api.ts
- All `fetch`/HTTP calls to the backend go through `extension/src/lib/api.ts`. No component, screen, background script, or content script may call `fetch(...)` directly against the backend.
- Popup screens (`popup/screens/*.tsx`) and `background/index.ts` import and call functions exported from `lib/api.ts`; they do not construct request URLs, headers, or bodies inline.
- If a new backend endpoint is being wired up, add a typed function to `lib/api.ts` first, then call it from the screen/component.

### 4. JWT / auth storage — cookies only, never localStorage
- Per project_rules.md §3, JWT access and refresh tokens live in HTTP-only, Secure, SameSite cookies set by the backend — the extension must never read/write tokens via `localStorage`, `sessionStorage`, or `chrome.storage` for the purpose of holding the JWT itself.
- `lib/auth.ts` handles auth state/flow (e.g., triggering login, checking auth status via a backend call) without ever persisting the raw token client-side. If existing code stores a token in `localStorage`/`chrome.storage`, flag it as a security violation and fix it to rely on cookie-based auth instead.
- Since Chrome extensions have a different cookie/origin model than a regular web app, requests from `lib/api.ts` to the backend must be configured to send credentials (cookies) correctly (e.g. `credentials: "include"`), and CORS on the backend must allow the extension's origin specifically (never `*` — that's a backend rule but relevant here since a wildcard CORS + credentials combo is invalid/insecure anyway).

## Workflow for new frontend work

1. Identify which structural bucket the task belongs to (content script for a specific board / popup screen / background / lib) — place new code only there.
2. If it needs backend data, add/extend the typed function in `lib/api.ts` first.
3. Build the screen/component/script, importing from `lib/api.ts` and `lib/auth.ts` as needed — no inline fetch, no inline token handling.
4. Check job-board build order (§8) before adding a new board's content script.

## Output format

When implementing or reviewing frontend work, report:
```
### Files touched
- extension/src/<path> — <what changed>

### Structure check
- Folder structure: OK / VIOLATION (<detail>)
- Content-script separation: OK / VIOLATION (<detail>)
- API centralization: OK / VIOLATION (<detail>)
- JWT storage: OK / VIOLATION (<detail>)
```

## What NOT to do

- Do not scatter `fetch` calls in components — always through `lib/api.ts`.
- Do not store JWTs in `localStorage`, `sessionStorage`, or `chrome.storage`.
- Do not merge multiple job boards' scraping logic into one file.
- Do not create new top-level folders under `extension/src` without asking first.
- Do not build a job board's scraper out of the §8 sequence order without flagging it.
