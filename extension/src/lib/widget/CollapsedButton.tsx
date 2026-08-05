function CvuraMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 12c0-4.4 3.6-8 8-8 3 0 5.6 1.6 7 4.1l-2.6 1.5A5.5 5.5 0 0 0 12 6.5 5.5 5.5 0 0 0 6.5 12 5.5 5.5 0 0 0 12 17.5a5.5 5.5 0 0 0 4.4-2.1l2.6 1.5c-1.4 2.5-4 4.1-7 4.1-4.4 0-8-3.6-8-8Z"
        fill="currentColor"
      />
    </svg>
  )
}

export default function CollapsedButton({ onClick }: { onClick: () => void }) {
  return (
    <button type="button" className="cvura-fab" onClick={onClick} aria-label="Open CVura">
      <CvuraMark />
    </button>
  )
}
