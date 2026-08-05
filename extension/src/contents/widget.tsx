import type { PlasmoCSConfig, PlasmoGetOverlayAnchor, PlasmoGetShadowHostId, PlasmoGetStyle } from "plasmo"

import buttonsCss from "data-text:~buttons.css"
import tokensCss from "data-text:~tokens.css"
import widgetCss from "data-text:~lib/widget/widget.css"

import JobWidget from "~lib/widget/JobWidget"

// Broader than detect.ts's job-URL-only matches: LinkedIn/Greenhouse/Lever
// are SPAs, so a user can navigate from a non-job page (feed) into a job
// posting client-side without a fresh content-script injection. The widget
// itself decides visibility per render via useJobDetection (~lib/widget) —
// same URL patterns as package.json's host_permissions.
export const config: PlasmoCSConfig = {
  matches: [
    "https://www.linkedin.com/*",
    "https://boards.greenhouse.io/*",
    "https://job-boards.greenhouse.io/*",
    "https://jobs.lever.co/*"
  ]
}

// Plasmo only starts its CSUI mount loop when an anchor getter is exported —
// without one, nothing ever mounts. `.cvura-widget-root` is `position: fixed`
// (see widget.css), so it ignores this anchor's position entirely; body just
// needs to exist and be visible for Plasmo to treat the page as ready.
export const getOverlayAnchor: PlasmoGetOverlayAnchor = () => document.body

export const getShadowHostId: PlasmoGetShadowHostId = () => "cvura-job-widget-host"

// tokens.css targets `:root`, which never matches inside a shadow tree (no
// <html> element in there) — swap it for `:host` so the custom properties it
// defines actually cascade to the widget's own elements.
export const getStyle: PlasmoGetStyle = () => {
  const style = document.createElement("style")
  style.textContent = [tokensCss.replace(":root", ":host"), buttonsCss, widgetCss].join("\n")
  return style
}

export default JobWidget
