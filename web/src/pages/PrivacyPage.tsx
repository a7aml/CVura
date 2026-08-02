import LegalPageLayout from "./LegalPageLayout"

export default function PrivacyPage() {
  return (
    <LegalPageLayout>
      <div className="placeholder-banner">
        <strong>Placeholder text.</strong> This page is a stub to satisfy the Chrome Web Store
        submission requirement for a Privacy Policy URL. Replace every bracketed section below
        with your actual data-handling practices before launch — do not publish this as-is.
      </div>

      <h1>Privacy Policy</h1>
      <p>Last updated: [date]</p>

      <h2>Information we collect</h2>
      <p>
        [Describe exactly what CVura collects: account email, profile/résumé content, scraped
        job posting text, generated résumé content, usage/plan data. Be specific about what the
        extension reads from job board pages.]
      </p>

      <h2>How we use it</h2>
      <p>
        [Describe the purpose of each category above — e.g., résumé content is used only to
        generate tailored résumés for the account that submitted it; job posting text is
        processed to extract structured requirements and is not shared with third parties.]
      </p>

      <h2>AI processing</h2>
      <p>
        [Name which AI provider(s) process résumé and job posting content, and whether that
        content is retained or used for model training by the provider.]
      </p>

      <h2>Data retention and deletion</h2>
      <p>
        [State how long data is kept and how a user can request deletion of their profile,
        résumés, and account.]
      </p>

      <h2>Third-party sharing</h2>
      <p>[State whether data is sold or shared, and with whom, if anyone.]</p>

      <h2>Contact</h2>
      <p>[Real support email or contact method goes here.]</p>
    </LegalPageLayout>
  )
}
