import type { PlasmoCSConfig } from "plasmo"

import { detectBoard, extractForBoard } from "~lib/job-board"
import type { ExtractedJob } from "~lib/types"

// Boards are built one at a time per the Build Order (LinkedIn -> Greenhouse
// -> Lever). All three are now done and tested — extend `matches` and the
// dispatch below again only once a genuinely new board is being added.
export const config: PlasmoCSConfig = {
  matches: [
    "https://www.linkedin.com/jobs/*",
    "https://boards.greenhouse.io/*/jobs/*",
    "https://job-boards.greenhouse.io/*/jobs/*",
    "https://jobs.lever.co/*/*"
  ]
}

interface ExtractJobMessage {
  type: "EXTRACT_JOB"
}

function isExtractJobMessage(message: unknown): message is ExtractJobMessage {
  return typeof message === "object" && message !== null && (message as Record<string, unknown>).type === "EXTRACT_JOB"
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Defense-in-depth, same rationale as background/index.ts's listener —
  // only this extension's own contexts should be able to trigger a scrape.
  if (sender.id !== chrome.runtime.id) return undefined
  if (!isExtractJobMessage(message)) return undefined

  extractForBoard(detectBoard())
    .then((job: ExtractedJob | null) => sendResponse(job))
  return true // keep the message channel open for the async response
})
