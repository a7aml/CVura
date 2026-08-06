import type { PlasmoCSConfig } from "plasmo"

import type { ExtractedJob } from "~lib/types"

// Plasmo treats every non-empty top-level file in `contents/` as its own
// content-script entry point, not just detect.ts's import of this module —
// without an explicit `matches`, it defaults to injecting on every site the
// user visits. Scope it to LinkedIn so a standalone injection (this file
// exports no top-level side effects, so it's a no-op if that happens) can't
// run anywhere else.
export const config: PlasmoCSConfig = {
  matches: ["https://www.linkedin.com/jobs/*"]
}

// Candidate selectors are tried in order, first match wins. LinkedIn's class
// names churn often (some are build-hashed), so this list is a resilience
// layer, not a guarantee — it's the fallback path behind JSON-LD, not the
// primary source of truth. The plain "h1" at the end is a last-resort catch:
// JSON-LD is typically only embedded on canonical /jobs/view/<id> pages, not
// the /jobs/search-results/?currentJobId=<id> panel view reached by browsing
// search results, so that flow depends entirely on this fallback list.
//
// Confirmed 2026-08-06 on a real authenticated session (a /jobs/view/ page,
// the "canonical" case this list is supposed to cover best): LinkedIn can
// render the title as a plain <p> with fully CSS-module-hashed classes (e.g.
// "_9c87fdd9") and no heading tag or semantic hook at all. None of the
// selectors below — including the "h1" catch-all — can ever match that
// variant. This is not a one-time fix: expect this list to periodically stop
// matching again as LinkedIn re-deploys or A/B-tests its markup. Treat
// JSON-LD (parseJsonLdJobPosting, below) and og:title (OG_TITLE_SELECTOR) as
// the resilient sources — neither depends on class names or tag choice — and
// this selector list as a bonus, not the thing to keep patching first.
const TITLE_SELECTORS = [
  "h1.job-details-jobs-unified-top-card__job-title",
  ".job-details-jobs-unified-top-card__job-title h1",
  "h1.jobs-unified-top-card__job-title",
  ".jobs-unified-top-card__job-title h1",
  "h1"
]

// LinkedIn renders this server-side for link-preview unfurling (Slack,
// Twitter, iMessage, etc.), so — unlike TITLE_SELECTORS — it doesn't depend
// on hydration, class names, or which tag LinkedIn's frontend happens to use
// for the title this month.
const OG_TITLE_SELECTOR = 'meta[property="og:title"]'

const COMPANY_SELECTORS = [
  ".job-details-jobs-unified-top-card__company-name a",
  ".job-details-jobs-unified-top-card__company-name",
  ".jobs-unified-top-card__company-name a",
  ".jobs-unified-top-card__company-name"
]

// Same hashed-classname problem as the title (see TITLE_SELECTORS), confirmed
// on the same real posting: COMPANY_SELECTORS didn't match, but the link's
// href did — every LinkedIn company page lives at /company/<slug>/, a
// site-wide URL convention that doesn't depend on class names or markup
// churn. Anchored to a leading "/" and excluded from header/nav/footer so it
// can't pick up an unrelated "/company/setup" nav link or a sidebar
// "similar companies" module ahead of the real one in DOM order.
const COMPANY_LINK_PATH_PATTERN = /^\/company\/[^/]+\/?(life\/)?$/

function findCompanyByLink(): string | null {
  const links = document.querySelectorAll<HTMLAnchorElement>('a[href*="/company/"]')
  for (const link of links) {
    if (link.closest("header, nav, footer")) continue
    let pathname: string
    try {
      pathname = new URL(link.href, window.location.href).pathname
    } catch {
      continue
    }
    if (!COMPANY_LINK_PATH_PATTERN.test(pathname)) continue
    const text = link.textContent?.trim()
    if (text) return text
  }
  return null
}

const DESCRIPTION_SELECTORS = [
  ".jobs-description__content .jobs-box__html-content",
  ".jobs-description-content__text",
  ".jobs-box__html-content",
  ".jobs-description__content"
]

// `data-testid` values are strings LinkedIn's own engineers author for their
// automated tests, not build-hashed CSS-module output — confirmed via real
// DevTools inspection (2026-08-06) on the same posting where every selector
// above missed: the whole "About the role" body (multiple paragraphs + bullet
// lists) lives inside a single `<span data-testid="expandable-text-box">`.
// This testid may not be unique to the job description on every page layout
// (e.g. a shorter "About the company" blurb could plausibly reuse the same
// expandable-text component) — picking the longest match favors the actual
// description over a short blurb without needing to know the page structure.
const DESCRIPTION_TESTID_SELECTOR = '[data-testid="expandable-text-box"]'

function findDescriptionByTestId(): string | null {
  const candidates = Array.from(document.querySelectorAll<HTMLElement>(DESCRIPTION_TESTID_SELECTOR))
    .map((el) => el.textContent?.trim() ?? "")
    .filter(Boolean)
  if (candidates.length === 0) return null
  return candidates.reduce((longest, current) => (current.length > longest.length ? current : longest))
}

function queryText(selectors: string[]): string | null {
  for (const selector of selectors) {
    const text = document.querySelector(selector)?.textContent?.trim()
    if (text) return text
  }
  return null
}

// LinkedIn's job pane is a client-rendered SPA region, so a content script
// injected at document_idle can still run before it exists. Poll the DOM via
// MutationObserver instead of a fixed sleep.
function waitForElement(selectors: string[], timeoutMs = 8000): Promise<void> {
  return new Promise((resolve) => {
    if (queryText(selectors)) {
      resolve()
      return
    }

    const observer = new MutationObserver(() => {
      if (queryText(selectors)) {
        observer.disconnect()
        clearTimeout(timer)
        resolve()
      }
    })
    observer.observe(document.body, { childList: true, subtree: true })

    const timer = setTimeout(() => {
      observer.disconnect()
      resolve()
    }, timeoutMs)
  })
}

function getStringField(obj: Record<string, unknown>, key: string): string | null {
  const value = obj[key]
  return typeof value === "string" && value.trim() ? value.trim() : null
}

function getNestedStringField(obj: Record<string, unknown>, key: string, nestedKey: string): string | null {
  const nested = obj[key]
  if (typeof nested !== "object" || nested === null) return null
  return getStringField(nested as Record<string, unknown>, nestedKey)
}

function stripHtml(html: string): string {
  const parsed = new DOMParser().parseFromString(html, "text/html")
  return (parsed.body.textContent ?? "").trim()
}

function isJobPosting(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && (value as Record<string, unknown>)["@type"] === "JobPosting"
}

interface JsonLdJob {
  title: string
  company: string | null
  description: string
}

// LinkedIn embeds a schema.org JobPosting block for SEO/Google for Jobs —
// stable and structured, so it's the preferred source over CSS selectors.
function parseJsonLdJobPosting(): JsonLdJob | null {
  const scripts = document.querySelectorAll('script[type="application/ld+json"]')
  for (const script of scripts) {
    let data: unknown
    try {
      data = JSON.parse(script.textContent ?? "")
    } catch {
      continue
    }

    const candidates = Array.isArray(data) ? data : [data]
    for (const candidate of candidates) {
      if (!isJobPosting(candidate)) continue
      const title = getStringField(candidate, "title")
      const descriptionHtml = getStringField(candidate, "description")
      if (!title || !descriptionHtml) continue
      return {
        title,
        company: getNestedStringField(candidate, "hiringOrganization", "name"),
        description: stripHtml(descriptionHtml)
      }
    }
  }
  return null
}

function normalizeTitle(title: string): string {
  return title.toLowerCase().replace(/\s+/g, " ").trim()
}

function getMetaContent(selector: string): string | null {
  const content = document.querySelector<HTMLMetaElement>(selector)?.content
  return content?.trim() || null
}

// og:title commonly carries a " | LinkedIn" suffix that the CSS-selector and
// JSON-LD sources never include — strip it so all three sources agree on
// shape.
function normalizeOgTitle(title: string): string {
  return title.replace(/\s*\|\s*LinkedIn\s*$/i, "").trim()
}

// Confirmed via view-source on a real authenticated posting (2026-08-06,
// jobs/view/4446278442) that neither JSON-LD nor og:title exist in <head> on
// this session/locale — but <title> always does, browsers require it. LinkedIn
// renders it as "{job title} | {company} | LinkedIn", so it's a two-for-one:
// classname- and hydration-independent, and gives both fields when the
// authoritative sources (JSON-LD, then CSS selectors, then og:title) all miss.
// Split on "|" rather than " | " — this real title contains a slash ("Software
// Developer / Junior Software Developer"), and being permissive about
// surrounding whitespace is safer than assuming an exact " | " spacing holds
// across locales. The raw <title> on this real (Arabic-locale) posting was
// wrapped in U+200F right-to-left marks around every segment — invisible
// bidi formatting, not real text, and not something String#trim() strips —
// so those are stripped explicitly before anything else.
function parseDocumentTitle(): { title: string; company: string | null } | null {
  const segments = document.title
    .replace(/[\u200e\u200f]/g, "")
    .split("|")
    .map((segment) => segment.trim())
    .filter(Boolean)
  if (segments.length === 0) return null

  const withoutBrand =
    segments[segments.length - 1].toLowerCase() === "linkedin" ? segments.slice(0, -1) : segments
  if (withoutBrand.length === 0) return null

  return {
    title: withoutBrand[0],
    company: withoutBrand.length > 1 ? withoutBrand[1] : null
  }
}

function toExtractedJob(job: JsonLdJob): ExtractedJob {
  return {
    source: "linkedin",
    title: job.title,
    company: job.company,
    raw_description: job.description,
    posting_url: window.location.href
  }
}

// LinkedIn's search view swaps job details via client-side navigation without
// a full reload, which can leave a stale JSON-LD block from the previously
// viewed posting. Cross-check against the live DOM title before trusting it.
function isJsonLdFresh(jsonLd: JsonLdJob): boolean {
  const domTitle = queryText(TITLE_SELECTORS)
  if (!domTitle) return true
  return normalizeTitle(domTitle) === normalizeTitle(jsonLd.title)
}

export async function extractLinkedInJob(): Promise<ExtractedJob | null> {
  // JSON-LD is server-rendered into the initial HTML for SEO, so it's worth
  // checking before waiting on anything — no need to burn the waitForElement
  // budget below when it's already there. This also matters because that
  // wait was previously gating JSON-LD entirely: on pages where the CSS
  // selector fallback can never match (see TITLE_SELECTORS comment), it used
  // to stall for the full timeout before JSON-LD was even attempted.
  const earlyJsonLd = parseJsonLdJobPosting()
  if (earlyJsonLd && isJsonLdFresh(earlyJsonLd)) {
    return toExtractedJob(earlyJsonLd)
  }

  // No usable JSON-LD yet — give the CSS-selector fallback path (and a
  // JSON-LD block that hasn't hydrated in yet) time to show up.
  await waitForElement([...TITLE_SELECTORS, ...DESCRIPTION_SELECTORS, DESCRIPTION_TESTID_SELECTOR])

  const jsonLd = parseJsonLdJobPosting()
  if (jsonLd && isJsonLdFresh(jsonLd)) {
    return toExtractedJob(jsonLd)
  }

  const docTitle = parseDocumentTitle()
  const domTitle = queryText(TITLE_SELECTORS)
  const ogTitle = getMetaContent(OG_TITLE_SELECTOR)
  const title = domTitle ?? (ogTitle ? normalizeOgTitle(ogTitle) : null) ?? docTitle?.title ?? null
  const rawDescription = queryText(DESCRIPTION_SELECTORS) ?? findDescriptionByTestId()
  if (!title || !rawDescription) return null

  return {
    source: "linkedin",
    title,
    company: queryText(COMPANY_SELECTORS) ?? findCompanyByLink() ?? docTitle?.company ?? null,
    raw_description: rawDescription,
    posting_url: window.location.href
  }
}
