// chrome.tabs and chrome.downloads are unavailable to content scripts, so
// Login/ResumeResult route through the background script for them here
// rather than calling the chrome.* APIs directly.

export interface OpenTabMessage {
  type: "OPEN_TAB"
  url: string
}

export interface DownloadFileMessage {
  type: "DOWNLOAD_FILE"
  url: string
  filename: string
}

type RuntimeActionMessage = OpenTabMessage | DownloadFileMessage

// The background script always calls sendResponse with one of these — never
// leaves a caller's chrome.runtime.sendMessage promise unresolved, even when
// the underlying chrome.tabs/chrome.downloads call rejects (a rejection with
// no matching sendResponse used to hang the caller forever instead of
// surfacing an error).
export interface RuntimeActionResponse {
  ok: boolean
  error?: string
}

export function isOpenTabMessage(message: unknown): message is OpenTabMessage {
  return isRuntimeActionMessage(message) && message.type === "OPEN_TAB"
}

export function isDownloadFileMessage(message: unknown): message is DownloadFileMessage {
  return isRuntimeActionMessage(message) && message.type === "DOWNLOAD_FILE"
}

function isRuntimeActionMessage(message: unknown): message is RuntimeActionMessage {
  return typeof message === "object" && message !== null && "type" in message
}

async function sendRuntimeAction(message: RuntimeActionMessage): Promise<void> {
  const response: RuntimeActionResponse = await chrome.runtime.sendMessage(message)
  if (!response?.ok) throw new Error(response?.error ?? `${message.type} failed`)
}

export function openTab(url: string): Promise<void> {
  return sendRuntimeAction({ type: "OPEN_TAB", url })
}

export function downloadFile(url: string, filename: string): Promise<void> {
  return sendRuntimeAction({ type: "DOWNLOAD_FILE", url, filename })
}
