import { useRef, useState } from 'react'
import { ArrowDown, ArrowUpRight, Check, ChevronRight, CircleHelp, FileText, LoaderCircle, Plus, Sparkles, Upload, Users } from 'lucide-react'
import { addContext, answerClarifications, analyzeMeeting } from './api'
import type { Meeting } from './types'

const sampleTranscript = `Maya: We need to ship the onboarding refresh by the end of October.
Jordan: I can own the new welcome email and have a draft ready by Friday.
Maya: Great. Let's use the new analytics events that Priya proposed last week.
Sam: I'll look into the mobile bug before the next check-in.
Maya: Someone should follow up with the customer team about the rollout plan.
Jordan: We should also revisit the activation target after we see the first week of data.`

function App() {
  const [title, setTitle] = useState('Product sync — September 24')
  const [transcript, setTranscript] = useState('')
  const [meeting, setMeeting] = useState<Meeting | null>(null)
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [contextTitle, setContextTitle] = useState('')
  const [contextText, setContextText] = useState('')
  const [contextNotice, setContextNotice] = useState('')
  const fileInput = useRef<HTMLInputElement>(null)

  async function runAnalysis() {
    if (transcript.trim().length < 20) {
      setError('Add a transcript with at least a few sentences to get started.')
      return
    }
    setBusy(true)
    setError('')
    setMeeting(null)
    try {
      setMeeting(await analyzeMeeting(title.trim() || 'Meeting notes', transcript))
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : 'Something went wrong.')
    } finally {
      setBusy(false)
    }
  }

  async function submitAnswers() {
    if (!meeting) return
    setBusy(true)
    setError('')
    try {
      setMeeting(await answerClarifications(meeting.id, answers))
      setAnswers({})
    } catch (problem) {
      setError(problem instanceof Error ? problem.message : 'Could not save your answers.')
    } finally {
      setBusy(false)
    }
  }

  async function loadFile(file?: File) {
    if (!file) return
    try {
      setTranscript(await file.text())
      setTitle((current) => current || file.name.replace(/\.[^.]+$/, ''))
      setError('')
    } catch {
      setError('Could not read that file. Choose a plain-text transcript.')
    }
  }

  async function saveContext() {
    if (!contextTitle.trim() || contextText.trim().length < 10) {
      setContextNotice('Add a document name and at least a few words of context.')
      return
    }
    setBusy(true)
    setContextNotice('')
    try {
      await addContext(contextTitle.trim(), contextText.trim())
      setContextNotice('Context indexed. It will be retrieved for relevant meetings.')
      setContextTitle('')
      setContextText('')
    } catch (problem) {
      setContextNotice(problem instanceof Error ? problem.message : 'Could not index this context.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#top"><span className="brand-mark"><Sparkles size={18} /></span><span>meetwise<span className="brand-period">.</span></span></a>
        <div className="workspace-label">WORKSPACE</div>
        <button className="workspace-switch"><span className="workspace-avatar">S</span><span><strong>Studio North</strong><small>Free workspace</small></span><ChevronRight size={16} /></button>
        <div className="nav-label">YOUR SPACE</div>
        <button className="nav-item active"><FileText size={17} /> Meetings <span className="nav-count">1</span></button>
        <button className="nav-item" onClick={() => document.getElementById('context')?.scrollIntoView({ behavior: 'smooth' })}><Users size={17} /> Team context</button>
        <div className="sidebar-bottom"><div className="help-card"><div className="help-icon"><CircleHelp size={16} /></div><strong>Make every meeting count</strong><p>Clear notes, decisions, and next steps in one place.</p><a href="#how-it-works">How it works <ArrowUpRight size={13} /></a></div><div className="profile"><span className="profile-avatar">S</span><span><strong>Workspace owner</strong><small>Local prototype</small></span><span className="profile-dots">···</span></div></div>
      </aside>

      <main id="top" className="main-content">
        <header className="topbar"><div className="breadcrumbs">Workspace <ChevronRight size={14} /> <span>Meetings</span></div><div className="topbar-right"><span className="privacy-pill"><span /> Private workspace</span><button className="avatar-small">S</button></div></header>
        <div className="page-wrap">
          <section className="page-heading"><div><div className="eyebrow"><span className="eyebrow-line" /> YOUR MEETING DESK</div><h1>Good notes make<br /><span>great follow-through.</span></h1><p>Turn the conversation into a plan your whole team can move on.</p></div><div className="heading-art"><div className="art-orbit orbit-one" /><div className="art-orbit orbit-two" /><div className="art-core"><Sparkles size={23} /></div><span className="art-dot dot-a" /><span className="art-dot dot-b" /></div></section>

          <section className="composer-card">
            <div className="section-kicker"><span className="step-number">01</span> NEW MEETING <span className="kicker-rule" /><span className="quiet-label">Draft · private</span></div>
            <label className="field-label" htmlFor="meeting-title">Meeting name</label>
            <input id="meeting-title" className="title-input" value={title} onChange={(event) => setTitle(event.target.value)} placeholder="e.g. Weekly product sync" />
            <div className="transcript-head"><label className="field-label" htmlFor="transcript">Transcript</label><button className="upload-link" onClick={() => fileInput.current?.click()}><Upload size={14} /> Upload .txt</button><input ref={fileInput} type="file" accept=".txt,text/plain" hidden onChange={(event) => void loadFile(event.target.files?.[0])} /></div>
            <div className="transcript-wrap"><textarea id="transcript" value={transcript} onChange={(event) => setTranscript(event.target.value)} placeholder="Paste your meeting transcript here…&#10;&#10;Speaker labels help us assign action items accurately." /><div className="textarea-footer"><span>{transcript.trim() ? `${transcript.trim().split(/\s+/).length} words` : 'Plain text · speaker labels recommended'}</span><button className="sample-link" onClick={() => setTranscript(sampleTranscript)}><Plus size={13} /> Try sample</button></div></div>
            {error && <div className="error-banner" role="alert">{error}</div>}
            <div className="composer-footer"><span className="privacy-note"><span className="privacy-check"><Check size={11} /></span> Your transcript stays in your workspace</span><button className="primary-button" disabled={busy} onClick={() => void runAnalysis()}>{busy ? <><LoaderCircle className="spin" size={16} /> Working…</> : <><Sparkles size={16} /> Create meeting notes <ArrowDown size={14} /></>}</button></div>
          </section>

          {meeting && <Results meeting={meeting} answers={answers} setAnswers={setAnswers} onSubmit={() => void submitAnswers()} busy={busy} />}

          <section id="context" className="context-callout"><div className="context-icon"><Users size={17} /></div><div className="context-content"><strong>Project &amp; team context</strong><p>Index a team directory, glossary, or project brief. Relevant passages are retrieved during meeting analysis.</p><div className="context-form"><input aria-label="Context document name" value={contextTitle} onChange={(event) => setContextTitle(event.target.value)} placeholder="Document name, e.g. Team directory" /><textarea aria-label="Context document text" value={contextText} onChange={(event) => setContextText(event.target.value)} placeholder="Paste team members, roles, project terms, or background…" /><button className="context-submit" disabled={busy} onClick={() => void saveContext()}>{busy ? <LoaderCircle className="spin" size={13} /> : <Plus size={13} />} Index context</button></div>{contextNotice && <span className="context-notice" role="status">{contextNotice}</span>}</div></section>
          <footer id="how-it-works" className="page-footer"><span>MEETWISE <b>·</b> MEETING INTELLIGENCE</span><span>AI drafts, people decide.</span></footer>
        </div>
      </main>
    </div>
  )
}

function Results({ meeting, answers, setAnswers, onSubmit, busy }: { meeting: Meeting; answers: Record<string, string>; setAnswers: (value: Record<string, string>) => void; onSubmit: () => void; busy: boolean }) {
  return <section className="results-section"><div className="section-kicker"><span className="step-number">02</span> MEETING BRIEF <span className="kicker-rule" /><span className={`status-pill ${meeting.status === 'complete' ? 'done' : ''}`}>{meeting.status === 'complete' ? <><Check size={12} /> Ready to review</> : <><CircleHelp size={12} /> Needs your input</>}</span></div><div className="results-card"><div className="results-title"><div><span className="result-label">THE RECAP</span><h2>{meeting.title}</h2></div><span className="sparkle-badge"><Sparkles size={16} /></span></div><p className="summary-text">{meeting.summary || 'No summary returned.'}</p>
    <div className="result-columns"><div className="result-block"><div className="block-heading"><span className="block-icon decision"><Check size={14} /></span><h3>Decisions</h3><span className="block-count">{meeting.decisions.length}</span></div>{meeting.decisions.length ? meeting.decisions.map((decision, index) => <article className="decision-row" key={index}><p>{decision.description}</p><small>“{decision.evidence}”</small></article>) : <p className="empty-note">No explicit decisions identified.</p>}</div>
      <div className="result-block"><div className="block-heading"><span className="block-icon action"><ArrowDown size={14} /></span><h3>Action items</h3><span className="block-count">{meeting.action_items.length}</span></div>{meeting.action_items.length ? meeting.action_items.map((item, index) => <article className="action-row" key={index}><div className="action-main"><p>{item.description}</p><div className="action-meta"><span className={!item.owner ? 'unassigned' : ''}>{item.owner || 'Owner needed'}</span><i />{item.due_date || 'No due date'}</div></div>{item.needs_clarification && <span className="ambiguous-tag">Clarify</span>}</article>) : <p className="empty-note">No action items identified.</p>}</div></div>
    {meeting.clarifications.length > 0 && <div className="clarify-panel"><div className="clarify-heading"><div><span className="result-label">A QUICK CHECK-IN</span><h3>Help us get this right</h3><p>A few details were unclear in the conversation. Add what you know.</p></div><span className="question-mark">?</span></div><div className="question-list">{meeting.clarifications.map((question) => <label className="question-row" key={question.id}><span>{question.question}<small>Based on: “{question.evidence}”</small></span><input value={answers[question.id] ?? ''} onChange={(event) => setAnswers({ ...answers, [question.id]: event.target.value })} placeholder="Your answer…" /></label>)}</div><div className="clarify-actions"><span>Leave unknown details blank; review unassigned or flagged items before sharing.</span><button className="primary-button small" disabled={busy} onClick={onSubmit}>{busy ? <LoaderCircle className="spin" size={15} /> : <><Check size={14} /> Save and finish</>}</button></div></div>}
    {meeting.status === 'complete' && <div className="complete-note"><span className="complete-check"><Check size={13} /></span> Draft ready. Review flagged or unassigned details before sharing.</div>}
    <div className="evidence-footnote"><span className="evidence-mark">“</span> Every item includes transcript evidence so your team can verify the details.</div></div></section>
}

export default App
