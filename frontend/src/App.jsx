import { useEffect, useRef, useState } from 'react'
import {
  Activity, ArrowRight, Check, ChevronDown, CircleHelp, Flag,
  Globe2, LoaderCircle, Play, RotateCcw, ShieldCheck, Sparkles, Square, Trophy,
} from 'lucide-react'
import { applyEvent, runPrediction } from './prediction.js'

const sample = {
  europe: 'Justin Rose',
  usa: 'Cameron Young',
  europeScore: '11.5',
  usaScore: '4.5',
  context: '',
}

const stages = [
  { author: 'PlayerProfilerAgent', title: 'Player profiles', detail: 'True Strokes Gained data' },
  { author: 'RecentFormAnalyst', title: 'Recent form', detail: 'Last three months' },
  { author: 'BaselineSkillAnalyst', title: 'Baseline skill', detail: 'Two-year performance' },
  { author: 'MatchupSynthesizerAgent', title: 'Matchup synthesis', detail: 'Win probabilities' },
  { author: 'MonteCarloSimulationAgent', title: 'Outcome simulation', detail: 'Match projection' },
]

function App() {
  const [input, setInput] = useState(sample)
  const [status, setStatus] = useState('idle')
  const [entries, setEntries] = useState([])
  const [seenAuthors, setSeenAuthors] = useState([])
  const [error, setError] = useState('')
  const controller = useRef(null)

  useEffect(() => () => controller.current?.abort(), [])

  function change(field, value) {
    setInput((current) => ({ ...current, [field]: value }))
  }

  async function submit(event) {
    event.preventDefault()
    const abortController = new AbortController()
    controller.current = abortController
    setStatus('running')
    setError('')
    setEntries([])
    setSeenAuthors([])

    try {
      let received = []
      for await (const agentEvent of runPrediction(input, abortController.signal)) {
        if (agentEvent?.author && agentEvent.author !== 'user') {
          setSeenAuthors((current) => current.includes(agentEvent.author)
            ? current : [...current, agentEvent.author])
        }
        received = applyEvent(received, agentEvent)
        setEntries(received)
      }
      if (!received.length) throw new Error('The agent finished without a text response.')
      setStatus('complete')
    } catch (failure) {
      if (abortController.signal.aborted) {
        setStatus('stopped')
      } else {
        setError(failure instanceof Error ? failure.message : 'The prediction could not be completed.')
        setStatus('error')
      }
    } finally {
      if (controller.current === abortController) controller.current = null
    }
  }

  function stop() {
    controller.current?.abort()
  }

  const isRunning = status === 'running'
  const activeStage = stages.findIndex((stage) => !seenAuthors.includes(stage.author))
  const result = entries.at(-1)

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark"><Flag size={21} strokeWidth={2.2} /></div><span>MATCHROOM<span className="brand-dot">.</span></span></div>
        <div className="sidebar-caption">THE RYDER CUP / 2025</div>
        <nav aria-label="Main navigation">
          <div className="nav-item selected"><Activity size={18} /> Match analysis <span className="nav-indicator" /></div>
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-rule" />
          <div className="sidebar-meta"><span className="sidebar-meta-icon"><ShieldCheck size={17} /></span><span>Powered by<br /><strong>Google ADK + MCP</strong></span></div>
          <div className="sidebar-foot">BUILT FOR THE LOVE OF THE GAME</div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar"><div className="breadcrumb">THE MATCHROOM <span>/</span> SUNDAY SINGLES</div><div className="topbar-right"><span className="connection-dot" /> LOCAL WORKSPACE</div></header>

        <div className="page-content">
          <div className="hero">
            <div className="eyebrow"><span className="eyebrow-line" /> RYDER CUP 2025 <span className="eyebrow-separator">·</span> SUNDAY SINGLES</div>
            <h1>Every match has <em>a story.</em><br />Find out how it ends.</h1>
            <p>Put two players head to head. Our five-stage agent looks at the numbers, reads the form, and builds a match prediction.</p>
          </div>

          <div className="workspace">
            <section className="setup-panel" aria-labelledby="setup-title">
              <div className="panel-heading"><div><div className="section-number">01 / THE SETUP</div><h2 id="setup-title">Set the stage</h2></div><span className="panel-icon"><Flag size={19} /></span></div>
              <form onSubmit={submit}>
                <div className="field-label-row"><span className="field-label">THE PAIRING</span><span className="field-hint">Europe listed first</span></div>
                <div className="pairing">
                  <label className="player-field"><span className="team-label"><span className="team-dot europe" /> TEAM EUROPE</span><input required aria-label="Europe player" value={input.europe} onChange={(event) => change('europe', event.target.value)} placeholder="Europe player" disabled={isRunning} /></label>
                  <div className="versus">VS</div>
                  <label className="player-field"><span className="team-label"><span className="team-dot usa" /> TEAM USA</span><input required aria-label="USA player" value={input.usa} onChange={(event) => change('usa', event.target.value)} placeholder="USA player" disabled={isRunning} /></label>
                </div>

                <div className="divider" />
                <div className="field-label-row"><span className="field-label">SATURDAY SCORE</span><span className="field-hint">Before singles</span></div>
                <div className="score-fields">
                  <label className="score-field"><span>EUROPE</span><input aria-label="Europe score" type="number" min="0" max="28" step="0.5" required value={input.europeScore} onChange={(event) => change('europeScore', event.target.value)} disabled={isRunning} /></label>
                  <span className="score-dash">—</span>
                  <label className="score-field"><span>USA</span><input aria-label="USA score" type="number" min="0" max="28" step="0.5" required value={input.usaScore} onChange={(event) => change('usaScore', event.target.value)} disabled={isRunning} /></label>
                </div>

                <div className="divider" />
                <div className="field-label-row"><label className="field-label" htmlFor="context">MATCH CONTEXT <span className="optional">(OPTIONAL)</span></label><CircleHelp size={15} className="help-icon" /></div>
                <textarea id="context" rows="3" placeholder="Add course conditions, player notes, or anything else the agent should consider..." value={input.context} onChange={(event) => change('context', event.target.value)} disabled={isRunning} />
                <div className="form-actions">
                  {isRunning
                    ? <button type="button" className="run-button stop-button" onClick={stop}><Square size={15} fill="currentColor" /> Stop analysis</button>
                    : <button type="submit" className="run-button"><Play size={16} fill="currentColor" /> Run prediction <ArrowRight size={18} className="button-arrow" /></button>}
                  <button type="button" className="reset-button" disabled={isRunning} onClick={() => setInput(sample)}><RotateCcw size={15} /> Reset to sample</button>
                </div>
              </form>
            </section>

            <section className="analysis-panel" aria-labelledby="analysis-title">
              <div className="panel-heading analysis-heading"><div><div className="section-number">02 / THE ANALYSIS</div><h2 id="analysis-title">The forecast</h2></div><span className={`status-pill ${status}`}><span />{status === 'idle' ? 'READY TO RUN' : status === 'running' ? 'LIVE ANALYSIS' : status === 'complete' ? 'COMPLETE' : status === 'stopped' ? 'STOPPED' : 'ERROR'}</span></div>

              {status === 'idle' ? (
                <div className="empty-state">
                  <div className="empty-illustration"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><Trophy size={48} strokeWidth={1.3} /><span className="spark spark-one">✦</span><span className="spark spark-two">✧</span></div>
                  <h3>The next match starts here.</h3><p>Set your pairing, then run a prediction to watch the analysis unfold in real time.</p>
                  <div className="empty-step"><span>01</span> Choose your players <ArrowRight size={14} /></div>
                </div>
              ) : (
                <div className="analysis-content" aria-live="polite">
                  <div className="pipeline-header"><span>ANALYSIS PIPELINE</span><span>{seenAuthors.filter((author) => stages.some((stage) => stage.author === author)).length} / 5 STAGES</span></div>
                  <div className="pipeline">
                    {stages.map((stage, index) => {
                      const seen = seenAuthors.includes(stage.author)
                      const active = isRunning && seen && (activeStage === -1 || index === activeStage - 1)
                      return <div className={`stage ${seen ? 'seen' : ''} ${active ? 'active' : ''}`} key={stage.author}><span className="stage-marker">{seen ? <Check size={13} strokeWidth={3} /> : String(index + 1).padStart(2, '0')}</span><div><strong>{stage.title}</strong><small>{stage.detail}</small></div>{active && <LoaderCircle size={15} className="spin" />}</div>
                    })}
                  </div>
                  {result && <div className="result-card"><div className="result-header"><span><Sparkles size={16} /> {result.author === 'RyderCupCoordinator' ? 'MATCH FORECAST' : result.author.replace(/([a-z])([A-Z])/g, '$1 $2').toUpperCase()}</span>{isRunning && <span className="streaming-tag">STREAMING <span className="connection-dot" /></span>}</div><div className="result-text">{result.text}</div></div>}
                  {entries.length > 1 && <details className="event-log"><summary>Earlier agent output ({entries.length - 1})</summary>{entries.slice(0, -1).map((entry, index) => <div className="event-entry" key={index}><strong>{entry.author}</strong><pre>{entry.text}</pre></div>)}</details>}
                  {isRunning && !result && <p className="waiting-text"><LoaderCircle size={15} className="spin" /> Connecting to the analysis team…</p>}
                  {status === 'error' && <div className="feedback error-message" role="alert"><strong>Analysis interrupted</strong><span>{error}</span></div>}
                  {status === 'stopped' && <div className="feedback" role="status">Analysis stopped. You can adjust the pairing and try again.</div>}
                  {status === 'complete' && <div className="feedback success-message" role="status"><Check size={16} /> Analysis complete. The forecast above is generated by the agent.</div>}
                </div>
              )}
            </section>
          </div>
          <footer className="page-footer"><div><Globe2 size={15} /> RYDER CUP 2025 <span>·</span> SUNDAY SINGLES</div><div>ANALYSIS, NOT CERTAINTY <ChevronDown size={14} /></div></footer>
        </div>
      </main>
    </div>
  )
}

export default App
