import type { ComponentType, SVGProps } from "react"
import { useEffect, useState } from "react"

import { createProfile, getProfile, logout, updateProfile } from "../lib/api"
import { prefersReducedMotion } from "../lib/motion"
import type { FullProfile, User } from "../lib/types"
import "./ProfileBuilderPage.css"
import AwardsSection from "./profile/AwardsSection"
import BasicInfoForm from "./profile/BasicInfoForm"
import CertificationsSection from "./profile/CertificationsSection"
import EducationSection from "./profile/EducationSection"
import ExperienceSection from "./profile/ExperienceSection"
import LanguagesSection from "./profile/LanguagesSection"
import ProjectsSection from "./profile/ProjectsSection"
import SkillsSection from "./profile/SkillsSection"
import {
  AwardIcon,
  BadgeCheckIcon,
  BriefcaseIcon,
  CheckIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ClipboardListIcon,
  FolderCodeIcon,
  GraduationCapIcon,
  LanguagesIcon,
  SparklesIcon,
  UserIcon,
} from "./profile/wizard-icons"

type StepKey =
  | "basics"
  | "education"
  | "experience"
  | "projects"
  | "skills"
  | "certifications"
  | "languages"
  | "awards"
  | "review"

const STEPS: { key: StepKey; label: string; icon: ComponentType<SVGProps<SVGSVGElement>> }[] = [
  { key: "basics", label: "Basic Info", icon: UserIcon },
  { key: "education", label: "Education", icon: GraduationCapIcon },
  { key: "experience", label: "Experience", icon: BriefcaseIcon },
  { key: "projects", label: "Projects", icon: FolderCodeIcon },
  { key: "skills", label: "Skills", icon: SparklesIcon },
  { key: "certifications", label: "Certifications", icon: BadgeCheckIcon },
  { key: "languages", label: "Languages", icon: LanguagesIcon },
  { key: "awards", label: "Awards", icon: AwardIcon },
  { key: "review", label: "Review", icon: ClipboardListIcon },
]

function isStepComplete(key: StepKey, profile: FullProfile | null): boolean {
  if (!profile) return false
  switch (key) {
    case "basics":
      return Boolean(profile.full_name)
    case "education":
      return profile.education.length > 0
    case "experience":
      return profile.experiences.length > 0
    case "projects":
      return profile.projects.length > 0
    case "skills":
      return profile.skills.length > 0
    case "certifications":
      return profile.certifications.length > 0
    case "languages":
      return profile.languages.length > 0
    case "awards":
      return profile.awards.length > 0
    case "review":
      return false
  }
}

export default function ProfileBuilderPage({
  user,
  onLoggedOut,
}: {
  user: User
  onLoggedOut: () => void
}) {
  const [profile, setProfile] = useState<FullProfile | null>(null)
  const [needsCreate, setNeedsCreate] = useState(false)
  const [loading, setLoading] = useState(true)
  const [stepIndex, setStepIndex] = useState(0)
  const [direction, setDirection] = useState<"forward" | "back">("forward")
  const [loggingOut, setLoggingOut] = useState(false)

  async function refresh() {
    try {
      setProfile(await getProfile())
      setNeedsCreate(false)
    } catch {
      setNeedsCreate(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function handleLogout() {
    await logout()
    if (prefersReducedMotion()) {
      onLoggedOut()
      return
    }
    // Let the fade-out play before swapping to the login page.
    setLoggingOut(true)
    window.setTimeout(onLoggedOut, 220)
  }

  if (loading) {
    return (
      <div className="shell center-screen">
        <span className="spinner spinner-dark" />
      </div>
    )
  }

  const hasProfile = !needsCreate && profile !== null
  const step = STEPS[stepIndex]
  const isFirstStep = stepIndex === 0
  const isLastStep = stepIndex === STEPS.length - 1

  const completableSteps = STEPS.filter((s) => s.key !== "review")
  const completedCount = completableSteps.filter((s) => isStepComplete(s.key, profile)).length
  const completenessPct = hasProfile ? Math.round((completedCount / completableSteps.length) * 100) : 0

  function goTo(index: number) {
    if (!hasProfile && index !== 0) return
    const clamped = Math.max(0, Math.min(STEPS.length - 1, index))
    setDirection(clamped >= stepIndex ? "forward" : "back")
    setStepIndex(clamped)
  }

  return (
    <div className={`shell wizard-shell ${loggingOut ? "wizard-shell-leaving" : ""}`}>
      <div className="header-bar">
        <div className="brand">
          <div className="brand-mark">CV</div>
          <div className="brand-name">CVura</div>
        </div>
        <div>
          <span style={{ marginRight: 12, color: "var(--color-text-muted)", fontSize: 13 }}>{user.email}</span>
          <button type="button" className="button button-secondary button-small" onClick={handleLogout}>
            Log out
          </button>
        </div>
      </div>

      {hasProfile && (
        <div className="completeness" title={`${completedCount} of ${completableSteps.length} sections complete`}>
          <span className="completeness-track">
            <span className="completeness-fill" style={{ width: `${completenessPct}%` }} />
          </span>
          <span className="completeness-label">{completenessPct}% profile complete</span>
        </div>
      )}

      {!hasProfile && (
        <>
          <h1>Let's build your profile</h1>
          <p className="hint">This is what CVura tailors into every résumé it generates — nothing here is ever invented.</p>
        </>
      )}

      <div className="wizard-progress">
        <div className="wizard-progress-head">
          <span>
            Step {stepIndex + 1} of {STEPS.length}
          </span>
          <span>{step.label}</span>
        </div>
        <div className="wizard-track">
          <div className="wizard-fill" style={{ width: `${((stepIndex + 1) / STEPS.length) * 100}%` }} />
        </div>
      </div>

      <div className="stepper">
        {STEPS.map((s, i) => {
          const Icon = s.icon
          const complete = isStepComplete(s.key, profile)
          const reachable = hasProfile || i === 0
          return (
            <button
              key={s.key}
              type="button"
              className={`step-btn ${i === stepIndex ? "active" : ""}`}
              disabled={!reachable}
              onClick={() => goTo(i)}>
              <span className="step-icon-wrap">
                <Icon aria-hidden="true" />
                {complete && (
                  <span className="step-check-badge">
                    <CheckIcon aria-hidden="true" />
                  </span>
                )}
              </span>
              <span className="step-btn-label">{s.label}</span>
            </button>
          )
        })}
      </div>

      <div className="wizard-panel">
        <div key={step.key} className={`wizard-panel-inner ${direction === "back" ? "dir-back" : ""}`}>
          {step.key === "basics" && (
            <BasicInfoForm
              initial={profile}
              submitLabel={hasProfile ? "Save changes" : "Create profile & continue"}
              onSubmit={async (fields) => {
                if (hasProfile) {
                  await updateProfile(fields)
                  await refresh()
                } else {
                  await createProfile(fields)
                  await refresh()
                  setStepIndex(1)
                }
              }}
            />
          )}
          {step.key === "education" && profile && <EducationSection items={profile.education} onChange={refresh} />}
          {step.key === "experience" && profile && (
            <ExperienceSection items={profile.experiences} onChange={refresh} />
          )}
          {step.key === "projects" && profile && <ProjectsSection items={profile.projects} onChange={refresh} />}
          {step.key === "skills" && profile && <SkillsSection items={profile.skills} onChange={refresh} />}
          {step.key === "certifications" && profile && (
            <CertificationsSection items={profile.certifications} onChange={refresh} />
          )}
          {step.key === "languages" && profile && <LanguagesSection items={profile.languages} onChange={refresh} />}
          {step.key === "awards" && profile && <AwardsSection items={profile.awards} onChange={refresh} />}
          {step.key === "review" && profile && <ReviewStep profile={profile} onEditStep={goTo} />}
        </div>
      </div>

      <div className="wizard-nav">
        <button
          type="button"
          className="button button-secondary"
          onClick={() => goTo(stepIndex - 1)}
          disabled={isFirstStep}>
          <ChevronLeftIcon aria-hidden="true" />
          Back
        </button>
        {!isLastStep && (
          <button
            type="button"
            className="button button-primary"
            onClick={() => goTo(stepIndex + 1)}
            disabled={!hasProfile}>
            Next
            <ChevronRightIcon aria-hidden="true" />
          </button>
        )}
      </div>
    </div>
  )
}

function ReviewStep({ profile, onEditStep }: { profile: FullProfile; onEditStep: (index: number) => void }) {
  const sections = [
    { label: "Education", index: 1, items: profile.education.map((e) => e.school) },
    { label: "Experience", index: 2, items: profile.experiences.map((e) => `${e.title} · ${e.company}`) },
    { label: "Projects", index: 3, items: profile.projects.map((p) => p.name) },
    { label: "Skills", index: 4, items: profile.skills.map((s) => s.name) },
    { label: "Certifications", index: 5, items: profile.certifications.map((c) => c.name) },
    { label: "Languages", index: 6, items: profile.languages.map((l) => l.name) },
    { label: "Awards", index: 7, items: profile.awards.map((a) => a.title) },
  ]

  return (
    <div className="section-block">
      <h2>Review your profile</h2>
      <p className="hint">This is everything CVura can pull from when it tailors a résumé to a posting.</p>

      <div className="item-card">
        <div className="item-card-head">
          <div>
            <div className="item-title">{profile.full_name}</div>
            <div className="item-subtitle">{profile.desired_title || "No desired title set"}</div>
          </div>
          <button type="button" className="button button-secondary button-small" onClick={() => onEditStep(0)}>
            Edit
          </button>
        </div>
      </div>

      <div className="review-grid">
        {sections.map((s) => (
          <div className="item-card" key={s.label}>
            <div className="item-card-head">
              <div>
                <div className="item-title">{s.label}</div>
                <div className="item-subtitle">{s.items.length === 0 ? "Not added yet" : `${s.items.length} added`}</div>
              </div>
              <button
                type="button"
                className="button button-secondary button-small"
                onClick={() => onEditStep(s.index)}>
                Edit
              </button>
            </div>
            {s.items.length > 0 && (
              <ul className="bullets-list">
                {s.items.slice(0, 3).map((item, i) => (
                  <li key={i}>{item}</li>
                ))}
                {s.items.length > 3 && <li>+{s.items.length - 3} more</li>}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
