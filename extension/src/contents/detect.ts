import type { PlasmoCSConfig } from "plasmo"

import type { ExtractedJob } from "~lib/types"
import { extractGreenhouseJob } from "./greenhouse"
import { extractLeverJob } from "./lever"
import { extractLinkedInJob } from "./linkedin"

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

type Board = "linkedin" | "greenhouse" | "lever" | null

interface ExtractJobMessage {
  type: "EXTRACT_JOB"
}

function isExtractJobMessage(message: unknown): message is ExtractJobMessage {
  return typeof message === "object" && message !== null && (message as Record<string, unknown>).type === "EXTRACT_JOB"
}

// Detection only — no scraping logic belongs in this file. Each board's own
// module (linkedin.ts, greenhouse.ts, lever.ts) owns its extraction.
function detectBoard(): Board {
  const host = window.location.hostname
  if (host.endsWith("linkedin.com")) return "linkedin"
  if (host.endsWith("greenhouse.io")) return "greenhouse"
  if (host.endsWith("lever.co")) return "lever"
  return null
}

function extractForBoard(board: Board): Promise<ExtractedJob | null> {
  switch (board) {
    case "linkedin":
      return extractLinkedInJob()
    case "greenhouse":
      return extractGreenhouseJob()
    case "lever":
      return extractLeverJob()
    case null:
      return Promise.resolve(null)
  }
}

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (!isExtractJobMessage(message)) return undefined

  extractForBoard(detectBoard()).then(sendResponse)
  return true // keep the message channel open for the async response
})
