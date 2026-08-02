import LegalPageLayout from "./LegalPageLayout"

export default function TermsPage() {
  return (
    <LegalPageLayout>
      <div className="placeholder-banner">
        <strong>Placeholder text.</strong> This page is a stub to satisfy the Chrome Web Store
        submission requirement for a Terms of Service URL. Replace every bracketed section below
        with real terms (ideally reviewed by counsel) before launch — do not publish this as-is.
      </div>

      <h1>Terms of Service</h1>
      <p>Last updated: [date]</p>

      <h2>The service</h2>
      <p>
        [Describe what CVura is: a browser extension and backend service that helps users
        tailor résumé content to job postings they view.]
      </p>

      <h2>Your account</h2>
      <p>[Eligibility, account security responsibilities, one account per person, etc.]</p>

      <h2>Plans and billing</h2>
      <p>
        [Free tier limits, Pro subscription price/billing cycle, cancellation policy, refund
        policy.]
      </p>

      <h2>Accuracy of generated content</h2>
      <p>
        [State plainly that CVura only reorganizes information the user provided and does not
        verify its accuracy — the user is responsible for the truthfulness of their own profile
        content and for reviewing generated résumés before submitting them to employers.]
      </p>

      <h2>Acceptable use</h2>
      <p>[Prohibited uses — e.g., submitting false information for another person, scraping at scale, reselling access.]</p>

      <h2>Termination</h2>
      <p>[Conditions under which an account may be suspended or terminated.]</p>

      <h2>Contact</h2>
      <p>[Real support email or contact method goes here.]</p>
    </LegalPageLayout>
  )
}
