import type { PlasmoCSConfig } from "plasmo"

import { queryText, waitForElement } from "~lib/scrape-utils"
import type { ExtractedJob } from "~lib/types"

// `boards.greenhouse.io` 301-redirects to `job-boards.greenhouse.io` for
// migrated accounts (confirmed against a live posting), but not every
// account is necessarily migrated — match both hosts defensively.
export const config: PlasmoCSConfig = {
  matches: ["https://boards.greenhouse.io/*/jobs/*", "https://job-boards.greenhouse.io/*/jobs/*"]
}

// Unlike LinkedIn/Lever, Greenhouse's job-boards app doesn't embed a
// schema.org JobPosting block — CSS selectors are the only source here.
const TITLE_SELECTORS = ["h1.section-header--large", ".job__header h1", "h1"]

const DESCRIPTION_SELECTORS = [".job__description", "#content"]

// Greenhouse doesn't render the company name as its own text element on the
// job page — pull it from the tab title ("Job Application for X at Acme") or
// fall back to the logo image's alt text ("Acme Logo").
function extractCompanyName(): string | null {
  const titleMatch = document.title.match(/ at (.+)$/)
  if (titleMatch) return titleMatch[1].trim()

  const logoAlt = document.querySelector("img[alt]")?.getAttribute("alt")
  if (logoAlt) return logoAlt.replace(/\s*Logo$/i, "").trim()

  return null
}

export async function extractGreenhouseJob(): Promise<ExtractedJob | null> {
  await waitForElement(TITLE_SELECTORS)

  const title = queryText(TITLE_SELECTORS)
  const rawDescription = queryText(DESCRIPTION_SELECTORS)
  if (!title || !rawDescription) return null

  return {
    source: "greenhouse",
    title,
    company: extractCompanyName(),
    raw_description: rawDescription,
    posting_url: window.location.href
  }
}
