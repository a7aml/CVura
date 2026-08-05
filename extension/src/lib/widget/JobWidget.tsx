import { useRef, useState } from "react"

import CollapsedButton from "~lib/widget/CollapsedButton"
import ExpandedPanel from "~lib/widget/ExpandedPanel"
import { useJobDetection } from "~lib/widget/useJobDetection"
import { useWidgetSession } from "~lib/widget/useWidgetSession"

export default function JobWidget() {
  const detection = useJobDetection()
  const [expanded, setExpanded] = useState(false)
  // Keyed by posting_url so dismissing one posting doesn't hide the widget on
  // the next one — "hidden for this page session", not permanently disabled.
  const [dismissedFor, setDismissedFor] = useState<string | null>(null)
  const enteredForRef = useRef<string | null>(null)

  const postingUrl = detection.status === "job" ? detection.job.posting_url : null
  const user = useWidgetSession(postingUrl)

  if (detection.status !== "job" || dismissedFor === postingUrl) {
    return null
  }

  const isFirstEntrance = enteredForRef.current !== postingUrl
  enteredForRef.current = postingUrl

  return (
    <div className={isFirstEntrance ? "cvura-widget-root cvura-enter" : "cvura-widget-root"}>
      {expanded ? (
        <ExpandedPanel
          user={user}
          onCollapse={() => setExpanded(false)}
          onDismiss={() => {
            setDismissedFor(postingUrl)
            setExpanded(false)
          }}
        />
      ) : (
        <CollapsedButton onClick={() => setExpanded(true)} />
      )}
    </div>
  )
}
