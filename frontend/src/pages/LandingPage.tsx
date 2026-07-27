import { Navigate, Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { SiteHeader } from '../components/SiteHeader'

const FEATURES = [
  {
    icon: '📐',
    title: 'GOST-compliant formatting',
    description:
      'Margins, fonts, line spacing, and heading styles applied to match Russian academic standards - fully configurable, sensible by default.',
  },
  {
    icon: '🤖',
    title: 'AI-assisted classification',
    description:
      'An AI model reads each paragraph and identifies titles, headings, captions, and body text, so formatting rules apply to the right places automatically.',
  },
  {
    icon: '📑',
    title: 'Automatic table of contents',
    description:
      'A real, working table of contents is generated from your headings and kept up to date whenever the document is opened in Word.',
  },
  {
    icon: '✍️',
    title: 'Light AI touch-ups',
    description:
      'Optionally let AI fill in a missing title or finish an obviously cut-off sentence - additive only, your existing text is never rewritten or removed.',
  },
]

const STEPS = [
  {
    title: 'Upload your document',
    description: 'Drop in a .docx file exactly as you wrote it.',
  },
  {
    title: 'Formatly does the formatting',
    description: 'Paragraphs are classified, formatting rules applied, and the result validated.',
  },
  {
    title: 'Download the result',
    description: 'Get back a properly formatted document, plus a report of what changed.',
  },
]

export function LandingPage() {
  const { user, isLoading } = useAuth()

  if (!isLoading && user) {
    return <Navigate to="/dashboard" replace />
  }

  return (
    <div>
      <SiteHeader>
        <Link to="/login">Log in</Link>
      </SiteHeader>

      <div className="landing">
        <section className="landing-hero">
          <h1>GOST-formatted documents, without the manual labor</h1>
          <p>
            Upload a .docx file and Formatly classifies its content with AI, applies GOST-standard
            formatting rules, builds a table of contents, and hands back a document ready to
            submit - while leaving your actual writing untouched.
          </p>
          <div className="landing-cta">
            <Link to="/register" className="landing-cta--primary">
              Get started
            </Link>
            <Link to="/login" className="landing-cta--secondary">
              Log in
            </Link>
          </div>
        </section>

        <section className="landing-features">
          {FEATURES.map((feature) => (
            <article className="landing-feature" key={feature.title}>
              <div className="landing-feature-icon" aria-hidden="true">
                {feature.icon}
              </div>
              <h3>{feature.title}</h3>
              <p>{feature.description}</p>
            </article>
          ))}
        </section>

        <section className="landing-steps">
          <h2>How it works</h2>
          <ol>
            {STEPS.map((step) => (
              <li key={step.title}>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
              </li>
            ))}
          </ol>
        </section>
      </div>

      <footer className="landing-footer">Formatly - AI-assisted GOST document formatting</footer>
    </div>
  )
}
