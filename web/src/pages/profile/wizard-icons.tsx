import type { SVGProps } from "react"

/** Small stroke-based icon set for the profile wizard stepper. */
type IconProps = SVGProps<SVGSVGElement>

const base = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.75,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
}

export function UserIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="8" r="4" />
      <path d="M4.5 20a7.5 7.5 0 0 1 15 0" />
    </svg>
  )
}

export function GraduationCapIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="m2 9 10-4 10 4-10 4-10-4Z" />
      <path d="M6 11v5c0 1.1 2.7 2 6 2s6-.9 6-2v-5" />
      <path d="M22 9v6" />
    </svg>
  )
}

export function BriefcaseIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="2.5" y="7" width="19" height="13" rx="2" />
      <path d="M8 7V5.5A1.5 1.5 0 0 1 9.5 4h5A1.5 1.5 0 0 1 16 5.5V7" />
      <path d="M2.5 12.5h19" />
    </svg>
  )
}

export function FolderCodeIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M3 6.5A1.5 1.5 0 0 1 4.5 5H9l2 2h8.5A1.5 1.5 0 0 1 21 8.5v9A1.5 1.5 0 0 1 19.5 19h-15A1.5 1.5 0 0 1 3 17.5Z" />
      <path d="m10.5 10.5-2 2 2 2M13.5 10.5l2 2-2 2" />
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

export function BadgeCheckIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="m12 2 2.2 1.3 2.5-.4 1.2 2.2 2.2 1.2-.4 2.5L21 11l-1.3 2.2.4 2.5-2.2 1.2-1.2 2.2-2.5-.4L12 20l-2.2-1.3-2.5.4-1.2-2.2-2.2-1.2.4-2.5L3 11l1.3-2.2-.4-2.5 2.2-1.2 1.2-2.2 2.5.4Z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  )
}

export function LanguagesIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 3a13 13 0 0 1 0 18M12 3a13 13 0 0 0 0 18M3 12h18" />
    </svg>
  )
}

export function AwardIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <circle cx="12" cy="8" r="5.5" />
      <path d="m8.5 12.8-1.7 7.2 5.2-2.6 5.2 2.6-1.7-7.2" />
    </svg>
  )
}

export function ClipboardListIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <rect x="5" y="4" width="14" height="17" rx="2" />
      <path d="M9 4V3a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v1" />
      <path d="M8.5 11h7M8.5 15h7M8.5 11.01v0M8.5 15.01v0" />
    </svg>
  )
}

export function CheckIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M4 12.5 9 17l11-11" />
    </svg>
  )
}

export function ChevronLeftIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="m14.5 5-7 7 7 7" />
    </svg>
  )
}

export function ChevronRightIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="m9.5 5 7 7-7 7" />
    </svg>
  )
}

export function UploadIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 16V4" />
      <path d="m7 9 5-5 5 5" />
      <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
    </svg>
  )
}

export function EditIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
  )
}

export function FileTextIcon(props: IconProps) {
  return (
    <svg {...base} {...props}>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
      <path d="M14 2v6h6" />
      <path d="M8 13h8" />
      <path d="M8 17h8" />
    </svg>
  )
}
