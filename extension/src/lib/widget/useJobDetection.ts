import { useEffect, useState } from "react"

import { matchSupportedJobBoard } from "~lib/config"
import { detectBoard, extractForBoard } from "~lib/job-board"
import type { ExtractedJob } from "~lib/types"
import { useCurrentUrl } from "~lib/widget/useCurrentUrl"

export type JobDetection = { status: "checking" | "no-job" } | { status: "job"; job: ExtractedJob }

// Reuses the exact detection/extraction the popup's EXTRACT_JOB flow uses
// (~lib/job-board, ~lib/config) rather than re-implementing a lighter check —
// matchSupportedJobBoard is a cheap URL-only gate, so the expensive DOM
// extraction only runs once a URL already looks like a job posting.
export function useJobDetection(): JobDetection {
  const href = useCurrentUrl()
  const [detection, setDetection] = useState<JobDetection>({ status: "checking" })

  useEffect(() => {
    if (!matchSupportedJobBoard(href)) {
      setDetection({ status: "no-job" })
      return
    }

    let cancelled = false
    setDetection({ status: "checking" })
    extractForBoard(detectBoard()).then((job) => {
      if (cancelled) return
      setDetection(job ? { status: "job", job } : { status: "no-job" })
    })
    return () => {
      cancelled = true
    }
  }, [href])

  return detection
}
