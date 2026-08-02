export const WEB_APP_URL = process.env.PLASMO_PUBLIC_WEB_APP_URL ?? "http://localhost:5173"
export const WEB_APP_LOGIN_PATH = "/app/login"

// Boards are built one at a time per the Build Order (LinkedIn -> Greenhouse
// -> Lever). All three are now done and tested.
export function matchSupportedJobBoard(url: string): "linkedin" | "greenhouse" | "lever" | null {
  try {
    const { hostname, pathname } = new URL(url)
    if (hostname.endsWith("linkedin.com") && pathname.startsWith("/jobs/")) return "linkedin"
    if (hostname.endsWith("greenhouse.io") && pathname.includes("/jobs/")) return "greenhouse"
    if (hostname.endsWith("lever.co") && pathname.split("/").filter(Boolean).length >= 2) return "lever"
    return null
  } catch {
    return null
  }
}
