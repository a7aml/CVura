import type { SVGProps } from "react"

/**
 * Small, consistent hand-authored icon set (lucide-style: 24px grid, 1.75 stroke,
 * round caps/joins) used across the landing page. Kept local + dependency-free
 * rather than pulling in an icon package for a handful of glyphs.
 */
type IconProps = SVGProps<SVGSVGElement>

const base = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
}

export function FileTextIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <path d="M14 2v6h6" />
      <path d="M8 13h8M8 17h8M8 9h2" />
    </svg>
  )
}

export function PenLineIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
  )
}

export function ListChecksIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="m3 6 1.5 1.5L7.5 4.5" />
      <path d="m3 13 1.5 1.5L7.5 11.5" />
      <path d="m3 20 1.5 1.5L7.5 18.5" />
      <path d="M12 6h9M12 13h9M12 20h9" />
    </svg>
  )
}

export function DownloadIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3v12" />
      <path d="m7 10 5 5 5-5" />
      <path d="M4 19.5h16" />
    </svg>
  )
}

export function UserRoundIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
    </svg>
  )
}

export function SearchIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3-3" />
    </svg>
  )
}

export function SparklesIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4" />
      <path d="m6.5 6.5 2 2M15.5 15.5l2 2M6.5 17.5l2-2M15.5 8.5l2-2" />
    </svg>
  )
}

export function ShieldCheckIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 3 4.5 6v6c0 4.7 3.2 8.4 7.5 9 4.3-.6 7.5-4.3 7.5-9V6Z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  )
}

export function CheckCircleIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12.5 2.3 2.3L16 10" />
    </svg>
  )
}

export function ZapIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M13 2 4 14h7l-1 8 9-12h-7z" />
    </svg>
  )
}

export function BadgeCheckIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="m12 2 2.2 1.3 2.5-.4 1.2 2.2 2.2 1.2-.4 2.5L21 11l-1.3 2.2.4 2.5-2.2 1.2-1.2 2.2-2.5-.4L12 20l-2.2-1.3-2.5.4-1.2-2.2-2.2-1.2.4-2.5L3 11l1.3-2.2-.4-2.5 2.2-1.2 1.2-2.2 2.5.4Z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  )
}
