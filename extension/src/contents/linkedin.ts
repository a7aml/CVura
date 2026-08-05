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
const TITLE_SELECTORS = [
  "h1.job-details-jobs-unified-top-card__job-title",
  ".job-details-jobs-unified-top-card__job-title h1",
  "h1.jobs-unified-top-card__job-title",
  ".jobs-unified-top-card__job-title h1",
  "h1"
]

const COMPANY_SELECTORS = [
  ".job-details-jobs-unified-top-card__company-name a",
  ".job-details-jobs-unified-top-card__company-name",
  ".jobs-unified-top-card__company-name a",
  ".jobs-unified-top-card__company-name"
]

const DESCRIPTION_SELECTORS = [
  ".jobs-description__content .jobs-box__html-content",
  ".jobs-description-content__text",
  ".jobs-box__html-content",
  ".jobs-description__content"
]

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

// LinkedIn's search view swaps job details via client-side navigation without
// a full reload, which can leave a stale JSON-LD block from the previously
// viewed posting. Cross-check against the live DOM title before trusting it.
function isJsonLdFresh(jsonLd: JsonLdJob): boolean {
  const domTitle = queryText(TITLE_SELECTORS)
  if (!domTitle) return true
  return normalizeTitle(domTitle) === normalizeTitle(jsonLd.title)
}

export async function extractLinkedInJob(): Promise<ExtractedJob | null> {
  await waitForElement(TITLE_SELECTORS)

  const jsonLd = parseJsonLdJobPosting()
  if (jsonLd && isJsonLdFresh(jsonLd)) {
    return {
      source: "linkedin",
      title: jsonLd.title,
      company: jsonLd.company,
      raw_description: jsonLd.description,
      posting_url: window.location.href
    }
  }

  const title = queryText(TITLE_SELECTORS)
  const rawDescription = queryText(DESCRIPTION_SELECTORS)
  if (!title || !rawDescription) return null

  return {
    source: "linkedin",
    title,
    company: queryText(COMPANY_SELECTORS),
    raw_description: rawDescription,
    posting_url: window.location.href
  }
}
