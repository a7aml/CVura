import type { PlasmoCSConfig } from "plasmo"

import {
  getNestedStringField,
  getStringField,
  isJobPosting,
  queryText,
  waitForElement
} from "~lib/scrape-utils"
import type { ExtractedJob } from "~lib/types"

export const config: PlasmoCSConfig = {
  matches: ["https://jobs.lever.co/*/*"]
}

const TITLE_SELECTORS = [".posting-headline h2", "h2"]
const DESCRIPTION_SELECTORS = ['[data-qa="job-description"]']
const REQUIREMENTS_SELECTORS = ['[data-qa="posting-requirements"]']

interface JsonLdJob {
  title: string
  company: string | null
}

// Lever embeds a schema.org JobPosting block with title + company, but not
// the full description — the description always comes from the DOM.
function parseJsonLdJob(): JsonLdJob | null {
  const scripts = document.querySelectorAll('script[type="application/ld+json"]')
  for (const script of scripts) {
    let data: unknown
    try {
      data = JSON.parse(script.textContent ?? "")
    } catch {
      continue
    }
    if (!isJobPosting(data)) continue
    const title = getStringField(data, "title")
    if (!title) continue
    return { title, company: getNestedStringField(data, "hiringOrganization", "name") }
  }
  return null
}

// The intro paragraph and the responsibilities/requirements block are
// separate sections on Lever's posting page — join both for the full JD.
function extractDescription(): string | null {
  const parts = [queryText(DESCRIPTION_SELECTORS), queryText(REQUIREMENTS_SELECTORS)].filter(
    (part): part is string => Boolean(part)
  )
  return parts.length > 0 ? parts.join("\n\n") : null
}

export async function extractLeverJob(): Promise<ExtractedJob | null> {
  await waitForElement(TITLE_SELECTORS)

  const jsonLd = parseJsonLdJob()
  const title = jsonLd?.title ?? queryText(TITLE_SELECTORS)
  const rawDescription = extractDescription()
  if (!title || !rawDescription) return null

  return {
    source: "lever",
    title,
    company: jsonLd?.company ?? null,
    raw_description: rawDescription,
    posting_url: window.location.href
  }
}
