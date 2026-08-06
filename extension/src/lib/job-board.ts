// Board detection + extraction dispatch for contents/detect.ts's EXTRACT_JOB
// message flow (the popup's way of pulling job data off the active tab).
// Lives in lib/, not contents/, so importing it never drags in detect.ts's
// onMessage listener as a side effect — Plasmo treats every top-level
// contents/ file as its own content-script entry.
import { extractGreenhouseJob } from "~contents/greenhouse"
import { extractLeverJob } from "~contents/lever"
import { extractLinkedInJob } from "~contents/linkedin"
import type { ExtractedJob } from "~lib/types"

export type Board = "linkedin" | "greenhouse" | "lever" | null

export function detectBoard(): Board {
  const host = window.location.hostname
  if (host.endsWith("linkedin.com")) return "linkedin"
  if (host.endsWith("greenhouse.io")) return "greenhouse"
  if (host.endsWith("lever.co")) return "lever"
  return null
}

export function extractForBoard(board: Board): Promise<ExtractedJob | null> {
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
