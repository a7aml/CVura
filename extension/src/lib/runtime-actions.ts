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

export function isOpenTabMessage(message: unknown): message is OpenTabMessage {
  return isRuntimeActionMessage(message) && message.type === "OPEN_TAB"
}

export function isDownloadFileMessage(message: unknown): message is DownloadFileMessage {
  return isRuntimeActionMessage(message) && message.type === "DOWNLOAD_FILE"
}

function isRuntimeActionMessage(message: unknown): message is RuntimeActionMessage {
  return typeof message === "object" && message !== null && "type" in message
}

export function openTab(url: string): Promise<void> {
  const message: OpenTabMessage = { type: "OPEN_TAB", url }
  return chrome.runtime.sendMessage(message)
}

export function downloadFile(url: string, filename: string): Promise<void> {
  const message: DownloadFileMessage = { type: "DOWNLOAD_FILE", url, filename }
  return chrome.runtime.sendMessage(message)
}
