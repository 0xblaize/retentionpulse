import { useEffect, useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { ArrowUpRight, CheckCircle2, CircleAlert, LogOut, Upload, X } from 'lucide-react'
import { analyzeVideo, authRoutes, bootstrapCsrf, getSession, logout } from './api'

const VIDEO_URL = 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260517_222138_3e3205be-3364-417b-a64a-bfe087acbec4.mp4'
const navItems = ['Story', 'Analysis', 'Workflow', 'Feedback']
const stats = [['0.5s', 'FRAME\nSAMPLING'], ['6s', 'DEAD-AIR\nTHRESHOLD'], ['250MB', 'UPLOAD\nLIMIT']]
const ease = [0.22, 1, 0.36, 1]
const fadeDown = { hidden: { opacity: 0, y: -20 }, visible: (index) => ({ opacity: 1, y: 0, transition: { delay: index * 0.1, duration: 0.5, ease } }) }
const fadeUp = { hidden: { opacity: 0, y: 32 }, visible: (index) => ({ opacity: 1, y: 0, transition: { delay: index * 0.12, duration: 0.6, ease } }) }
const headingReveal = { hidden: { y: '110%' }, visible: (index) => ({ y: 0, transition: { delay: 0.4 + index * 0.14, duration: 0.7, ease } }) }

function Logo({ compact = false }) {
  return <img src={compact ? '/retentionpulse-mark.svg' : '/retentionpulse-logo.svg'} alt={compact ? '' : 'RetentionPulse AI'} className={compact ? 'h-9 w-9 shrink-0' : 'h-10 w-auto max-w-[220px]'} aria-hidden={compact ? 'true' : undefined} />
}

function Hamburger({ onClick, label = 'Open menu' }) {
  return <button type="button" onClick={onClick} aria-label={label} className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-black focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"><span className="flex flex-col gap-1"><span className="h-0.5 w-4 bg-white" /><span className="h-0.5 w-4 bg-white" /><span className="h-0.5 w-4 bg-white" /></span></button>
}

function Landing() {
  const [menuOpen, setMenuOpen] = useState(false)
  const [videoLoaded, setVideoLoaded] = useState(false)
  const reduceMotion = useReducedMotion()
  const initial = reduceMotion ? false : 'hidden'

  useEffect(() => {
    const start = () => setVideoLoaded(true)
    if (window.requestIdleCallback) {
      const idleId = window.requestIdleCallback(start, { timeout: 1800 })
      return () => window.cancelIdleCallback(idleId)
    }
    const timeoutId = window.setTimeout(start, 900)
    return () => window.clearTimeout(timeoutId)
  }, [])

  return <main className="relative flex min-h-[100svh] flex-col overflow-x-clip bg-[#c9c8c6] font-sans uppercase tracking-widest text-black">
    {videoLoaded && <video className="absolute inset-0 h-full w-full object-cover" src={VIDEO_URL} autoPlay muted loop playsInline preload="none" aria-hidden="true" />}
    <div className="relative z-10 flex min-h-screen flex-col px-5 pt-5 sm:px-8 md:px-12 md:pt-6">
      <nav className="flex h-9 shrink-0 items-center justify-between" aria-label="Primary navigation">
        <motion.a custom={0} variants={fadeDown} initial={initial} animate="visible" href="/" aria-label="RetentionPulse home" className="flex items-center gap-2 rounded-full focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"><Logo compact /><span className="text-sm font-semibold tracking-widest">RP</span></motion.a>
        <div className="hidden items-center gap-7 lg:flex">{navItems.map((item, index) => <motion.a key={item} custom={index + 1} variants={fadeDown} initial={initial} animate="visible" href={`#${item.toLowerCase()}`} className="text-sm font-semibold tracking-widest focus:outline-none focus:ring-2 focus:ring-accent">{item}</motion.a>)}</div>
        <motion.div custom={5} variants={fadeDown} initial={initial} animate="visible" className="lg:hidden"><Hamburger onClick={() => setMenuOpen(true)} /></motion.div>
      </nav>
      <section className="flex flex-1 items-center justify-end py-8 md:py-0" aria-label="Selected work statistics"><div className="grid w-full max-w-xl grid-cols-3 gap-3 text-right sm:gap-8 md:gap-10">{stats.map(([number, label], index) => <motion.div key={label} custom={index + 2} variants={fadeUp} initial={initial} animate="visible" className="text-right"><p className="font-semibold leading-none" style={{ fontSize: 'clamp(1.5rem, 5vw, 3.5rem)' }}><span className="text-[0.5em] text-accent">•</span>{number}</p><p className="whitespace-pre-line text-[10px] font-semibold leading-tight tracking-widest sm:text-xs md:text-sm">{label}</p></motion.div>)}</div></section>
      <section className="flex shrink-0 flex-col gap-6 pb-8 md:gap-8 md:pb-10"><div className="flex flex-wrap items-center justify-between gap-4"><motion.p custom={5} variants={fadeUp} initial={initial} animate="visible" className="max-w-[130px] text-[10px] font-semibold leading-tight tracking-widest sm:max-w-[160px] sm:text-xs md:max-w-xs md:text-sm">Make Every<br />Second Matter<br />For Your Audience</motion.p><motion.a custom={6} variants={fadeUp} initial={initial} animate="visible" href={authRoutes.login} className="inline-flex shrink-0 items-center gap-2 whitespace-nowrap text-base font-semibold tracking-wide text-accent focus:outline-none focus:ring-2 focus:ring-accent sm:text-xl md:text-2xl">Analyze Your video<ArrowUpRight size={18} className="sm:h-[22px] sm:w-[22px]" /></motion.a></div><div className="grid grid-cols-[minmax(0,0.8fr)_minmax(0,2fr)] items-end gap-6 sm:gap-8"><motion.div custom={7} variants={fadeUp} initial={initial} animate="visible" className="w-auto min-w-0 text-left md:text-right"><p className="text-[9px] font-semibold leading-tight tracking-widest sm:text-xs md:text-sm">AI-Powered Visual Retention Analysis Built For Editors And Creators</p></motion.div><h1 className="ml-2 max-w-[calc(100%-0.5rem)] justify-self-end text-right font-semibold leading-[0.88] tracking-[-0.08em] sm:ml-3 sm:max-w-[calc(100%-0.75rem)]" style={{ fontSize: 'clamp(2.35rem, 9vw, 8rem)' }}>{['Detect', 'Dead Air', 'Early'].map((word, index) => <span key={word} className="block overflow-hidden"><motion.span custom={index} variants={headingReveal} initial={initial} animate="visible" className="block">{word}</motion.span></span>)}</h1></div></section>
    </div>
    <AnimatePresence>{menuOpen && <motion.div className="fixed inset-0 z-50 flex min-h-screen flex-col bg-white px-5 pb-8 pt-5 sm:px-8 md:px-12" initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: reduceMotion ? 0 : 0.25 }}><div className="flex items-center justify-between"><a href="/" onClick={() => setMenuOpen(false)} aria-label="RetentionPulse home" className="flex items-center gap-2"><Logo compact /><span className="text-sm font-semibold tracking-widest">RP</span></a><button type="button" onClick={() => setMenuOpen(false)} aria-label="Close menu" className="flex h-9 w-9 items-center justify-center rounded-full bg-black text-white"><X size={20} /></button></div><nav className="mt-16 flex flex-col gap-8" aria-label="Mobile navigation">{navItems.map((item, index) => <motion.a key={item} href={`#${item.toLowerCase()}`} onClick={() => setMenuOpen(false)} className="text-3xl font-semibold tracking-widest" initial={reduceMotion ? false : { opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: reduceMotion ? 0 : index * 0.08, duration: reduceMotion ? 0 : 0.35, ease }}>{item}</motion.a>)}</nav><a href={authRoutes.login} className="mt-auto inline-flex items-center gap-2 text-xl font-semibold tracking-wide text-accent">Analyze Your Edit <ArrowUpRight size={22} /></a></motion.div>}</AnimatePresence>
  </main>
}

function Metric({ label, value, detail }) { return <div className="rounded-2xl border border-black/10 bg-white/70 p-4 sm:p-5"><p className="text-xs font-semibold tracking-[0.18em] text-black/55">{label}</p><p className="mt-2 break-words text-[clamp(1.5rem,7vw,1.875rem)] font-semibold tracking-tight">{value}</p>{detail && <p className="mt-1 text-sm normal-case tracking-normal text-black/60">{detail}</p>}</div> }

function formatTime(seconds) { if (!Number.isFinite(seconds)) return '0:00'; const minutes = Math.floor(seconds / 60); return `${minutes}:${String(Math.floor(seconds % 60)).padStart(2, '0')}` }

function zoneLabel(zone) {
  return zone === 'red' ? 'High risk' : zone === 'yellow' ? 'Watch' : 'Healthy attention'
}

function zoneClass(zone) {
  return zone === 'red' ? 'bg-risk' : zone === 'yellow' ? 'bg-warning' : 'bg-safe'
}

function Timeline({ analysis }) {
  const points = analysis.timeline || []
  const zones = analysis.timeline_zones || []
  const segments = analysis.segments || []
  const duration = analysis.duration || 1
  const [selectedZone, setSelectedZone] = useState(zones[0] || null)
  const hasZones = zones.length > 0

  useEffect(() => { setSelectedZone(zones[0] || null) }, [analysis])

  if (!hasZones) {
    return <section className="rounded-3xl border border-black/10 bg-white/80 p-5 sm:p-7" aria-labelledby="timeline-heading"><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><p className="text-xs font-semibold tracking-[0.18em] text-accent">MOTION MAP</p><h2 id="timeline-heading" className="mt-1 text-2xl font-semibold tracking-tight">Retention timeline</h2></div><div className="flex gap-4 text-xs font-semibold tracking-wide"><span className="inline-flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-full bg-safe" />Clear</span><span className="inline-flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-full bg-risk" />Risk</span></div></div><div className="mt-6" role="img" aria-label="Timeline showing clear and risk points"><div className="relative h-16 rounded-xl bg-[#e7e8e3]">{segments.map((segment, index) => <div key={`${segment.start}-${index}`} title={`${formatTime(segment.start)}–${formatTime(segment.end)} risk segment`} className="absolute inset-y-0 rounded-md bg-risk/80" style={{ left: `${(segment.start / duration) * 100}%`, width: `${Math.max(((segment.end - segment.start) / duration) * 100, 0.5)}%` }} />)}<div className="absolute inset-x-0 top-1/2 h-1 -translate-y-1/2 rounded-full bg-black/15" />{points.map((point, index) => <span key={`${point.timestamp}-${index}`} title={`${formatTime(point.timestamp)} · motion ${point.motion_score.toFixed(2)} · ${point.risk ? 'risk' : 'clear'}`} className={`absolute top-1/2 h-4 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full ${point.risk ? 'bg-risk' : 'bg-black/35'}`} style={{ left: `${point.position}%` }} />)}</div><div className="mt-2 flex justify-between text-xs text-black/55"><span>0:00</span><span>{formatTime(duration)}</span></div></div><div className="sr-only"><table><caption>Timeline points</caption><thead><tr><th>Time</th><th>Motion score</th><th>Status</th></tr></thead><tbody>{points.map((point, index) => <tr key={`${point.timestamp}-${index}`}><td>{formatTime(point.timestamp)}</td><td>{point.motion_score.toFixed(2)}</td><td>{point.risk ? 'Risk' : 'Clear'}</td></tr>)}</tbody></table></div></section>
  }

  return <section className="rounded-3xl border border-black/10 bg-white/80 p-5 sm:p-7" aria-labelledby="timeline-heading"><div className="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-start sm:justify-between"><div className="min-w-0"><p className="text-xs font-semibold tracking-[0.18em] text-accent">RETENTION HEATMAP</p><h2 id="timeline-heading" className="mt-1 text-2xl font-semibold tracking-tight">See where attention drops</h2><p className="mt-2 max-w-xl text-sm normal-case tracking-normal text-black/60">Every color is a precise moment from the local motion, audio, and semantic analysis.</p></div><div className="flex flex-wrap gap-3 text-xs font-semibold tracking-wide" aria-label="Retention zone legend"><span className="inline-flex items-center gap-1.5"><i className="status-swatch bg-safe" aria-hidden="true" />Healthy attention</span><span className="inline-flex items-center gap-1.5"><i className="status-swatch bg-warning" aria-hidden="true" />Watch</span><span className="inline-flex items-center gap-1.5"><i className="status-swatch bg-risk" aria-hidden="true" />High risk</span></div></div><div className="mt-6" role="group" aria-label="Retention zones across the video"><div className="flex h-16 overflow-hidden rounded-xl bg-black/10 ring-1 ring-black/10">{zones.map((zone, index) => { const next = zones[index + 1]?.position ?? 100; const width = Math.max(next - zone.position, 0.35); const label = `${formatTime(zone.timestamp)}, ${zoneLabel(zone.zone)}, ${(zone.attention_risk * 100).toFixed(0)} percent attention risk, ${zone.reasons?.length ? zone.reasons.join(', ') : 'No issue detected'}`; return <button key={`${zone.timestamp}-${index}`} type="button" aria-label={label} onMouseEnter={() => setSelectedZone(zone)} onFocus={() => setSelectedZone(zone)} className={`heatmap-zone ${zoneClass(zone.zone)}`} data-zone={zone.zone} style={{ width: `${width}%` }} /> })}</div><div className="mt-2 flex justify-between text-xs text-black/55"><span>0:00</span><span>{formatTime(duration)}</span></div></div>{selectedZone && <div className="mt-5 rounded-2xl border border-black/10 bg-[#f4f1ed] p-4" aria-live="polite"><div className="flex flex-wrap items-center gap-3"><span className={`status-swatch ${zoneClass(selectedZone.zone)}`} aria-hidden="true" /><strong>{formatTime(selectedZone.timestamp)} · {zoneLabel(selectedZone.zone)}</strong><span className="text-sm text-black/60">{(selectedZone.attention_risk * 100).toFixed(0)}% attention risk</span></div><p className="mt-2 text-sm normal-case tracking-normal text-black/65">{selectedZone.reasons?.length ? selectedZone.reasons.join(', ') : 'No issue detected'}</p></div>}<details className="mt-5"><summary className="cursor-pointer text-sm font-semibold tracking-wide focus:outline-none focus-visible:ring-2 focus-visible:ring-accent">View timeline as a table</summary><div className="mt-3 overflow-x-auto"><table className="w-full min-w-[520px] text-left text-sm"><caption className="sr-only">Retention heatmap timeline</caption><thead className="border-b border-black/10 text-xs uppercase tracking-[0.12em] text-black/55"><tr><th className="pb-3">Time</th><th className="pb-3">Zone</th><th className="pb-3">Risk</th><th className="pb-3">Signals</th></tr></thead><tbody>{zones.map((zone, index) => <tr key={`${zone.timestamp}-${index}`} className="border-b border-black/5"><td className="py-3">{formatTime(zone.timestamp)}</td><td className="py-3"><span className="inline-flex items-center gap-2 font-semibold"><span className={`status-swatch ${zoneClass(zone.zone)}`} aria-hidden="true" />{zoneLabel(zone.zone)}</span></td><td className="py-3">{(zone.attention_risk * 100).toFixed(0)}%</td><td className="py-3 normal-case tracking-normal text-black/60">{zone.reasons?.length ? zone.reasons.join(', ') : 'No issue detected'}</td></tr>)}</tbody></table></div></details></section>
}

function downloadManifest(analysis) {
  const blob = new Blob([JSON.stringify({
    analyzer_version: analysis.analyzer_version,
    mode: analysis.mode,
    duration: analysis.duration,
    capabilities: analysis.capabilities,
    warnings: analysis.warnings,
    timeline_zones: analysis.timeline_zones,
    segments: analysis.segments,
    suggestions: analysis.suggestions,
    remediation_actions: analysis.remediation_actions
  }, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'retentionpulse-remediation.json'
  anchor.click()
  URL.revokeObjectURL(url)
}

function DiagnosticDetails({ analysis }) {
  const metrics = analysis.speech_metrics
  const zones = analysis.timeline_zones || []
  if (!analysis.capabilities) return null
  return <div className="space-y-6"><section className="rounded-3xl border border-black/10 bg-white/80 p-5 sm:p-7" aria-labelledby="diagnostic-heading"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-semibold tracking-[0.18em] text-accent">MULTIMODAL DIAGNOSTICS</p><h2 id="diagnostic-heading" className="mt-1 text-2xl font-semibold tracking-tight">What shaped the risk score</h2></div><button type="button" onClick={() => downloadManifest(analysis)} className="rounded-full border border-black/15 px-4 py-2 text-xs font-semibold tracking-[0.12em] hover:bg-black hover:text-white">Download remediation JSON</button></div><div className="mt-5 flex flex-wrap gap-2 text-xs font-semibold tracking-wide">{Object.entries(analysis.capabilities).map(([name, available]) => <span key={name} className={`rounded-full border px-3 py-1 ${available ? 'border-green-700/30 bg-green-100 text-green-800' : 'border-black/10 bg-black/5 text-black/55'}`}>{available ? 'Available' : 'Unavailable'} · {name}</span>)}</div>{analysis.warnings?.length > 0 && <ul className="mt-4 space-y-1 text-sm normal-case tracking-normal text-black/60">{analysis.warnings.map((warning) => <li key={warning}>• {warning}</li>)}</ul>}{metrics && <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><Metric label="Speech ratio" value={`${(metrics.speech_ratio * 100).toFixed(0)}%`} /><Metric label="Pauses" value={metrics.pause_count} detail={`${metrics.long_pause_count} long pauses`} /><Metric label="Pause density" value={metrics.pause_density.toFixed(2)} /><Metric label="Avg energy" value={metrics.average_energy.toFixed(3)} /></div>}</section>{zones.length > 0 && <section className="rounded-3xl border border-black/10 bg-white/80 p-5 sm:p-7" aria-labelledby="zones-heading"><p className="text-xs font-semibold tracking-[0.18em] text-accent">ATTENTION ZONES</p><h2 id="zones-heading" className="mt-1 text-2xl font-semibold tracking-tight">Green, yellow, and red moments</h2><div className="mt-5 overflow-x-auto"><table className="w-full min-w-[520px] text-left text-sm"><thead className="border-b border-black/10 text-xs uppercase tracking-[0.12em] text-black/55"><tr><th className="pb-3">Time</th><th className="pb-3">Zone</th><th className="pb-3">Risk</th><th className="pb-3">Signals</th></tr></thead><tbody>{zones.filter((zone, index) => index % 4 === 0 || zone.zone !== 'green').map((zone) => <tr key={zone.timestamp} className="border-b border-black/5"><td className="py-3">{formatTime(zone.timestamp)}</td><td className="py-3"><span className={`inline-flex items-center gap-2 font-semibold ${zone.zone === 'red' ? 'text-red-700' : zone.zone === 'yellow' ? 'text-amber-700' : 'text-green-700'}`}><span aria-hidden="true">{zone.zone === 'red' ? '●' : zone.zone === 'yellow' ? '▲' : '●'}</span>{zone.zone}</span></td><td className="py-3">{(zone.attention_risk * 100).toFixed(0)}%</td><td className="py-3 normal-case tracking-normal text-black/60">{zone.reasons.length ? zone.reasons.join(', ') : 'No issue detected'}</td></tr>)}</tbody></table></div></section>}</div>
}

function VideoPreview({ file, src }) {
  if (!file || !src) return null
  return <section className="rounded-3xl border border-black/10 bg-white/80 p-5 sm:p-7" aria-labelledby="preview-heading"><div className="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:justify-between"><div className="min-w-0"><p className="text-xs font-semibold tracking-[0.18em] text-accent">EDIT PREVIEW</p><h2 id="preview-heading" className="mt-1 text-2xl font-semibold tracking-tight">Your video, analyzed in context</h2></div><p className="max-w-full break-words text-sm normal-case tracking-normal text-black/55">{file.name} · {(file.size / (1024 * 1024)).toFixed(1)} MB</p></div><video className="mt-5 max-h-[min(55svh,520px)] min-h-[180px] w-full rounded-2xl bg-black object-contain sm:min-h-0" src={src} controls playsInline preload="metadata" /> </section>
}

function webauthnBytes(value) {
  const padded = value.replace(/-/g, '+').replace(/_/g, '/').padEnd(Math.ceil(value.length / 4) * 4, '=')
  return Uint8Array.from(atob(padded), (character) => character.charCodeAt(0))
}

function webauthnBase64url(buffer) {
  return btoa(String.fromCharCode(...new Uint8Array(buffer))).replace(/\\+/g, '-').replace(/\\//g, '_').replace(/=+$/, '')
}

function webauthnCredentialPayload(credential) {
  return {
    id: credential.id,
    rawId: webauthnBase64url(credential.rawId),
    type: credential.type,
    response: Object.fromEntries(Object.entries(credential.response).map(([key, value]) => [key, value instanceof ArrayBuffer ? webauthnBase64url(value) : value]))
  }
}

function decodeWebAuthnOptions(options) {
  if (options.challenge) options.challenge = webauthnBytes(options.challenge)
  if (options.user?.id) options.user.id = webauthnBytes(options.user.id)
  options.allowCredentials?.forEach((item) => { item.id = webauthnBytes(item.id) })
  options.excludeCredentials?.forEach((item) => { item.id = webauthnBytes(item.id) })
  return options
}

function Login() {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const request = async (path, options = {}) => {
    const csrf = document.cookie.split('; ').find((cookie) => cookie.startsWith('csrftoken='))?.split('=')[1] || ''
    const response = await fetch(path, {
      credentials: 'same-origin',
      ...options,
      headers: { 'X-CSRFToken': decodeURIComponent(csrf), ...(options.headers || {}) }
    })
    const body = await response.text()
    let payload = {}
    try {
      payload = body ? JSON.parse(body) : {}
    } catch {
      throw new Error(`Passkey service returned an invalid response (${response.status}).`)
    }
    if (!response.ok) throw new Error(payload.detail || `Passkey request failed (${response.status}).`)
    return payload
  }

  const run = async (mode) => {
    setBusy(true)
    setError('')
    try {
      if (!window.PublicKeyCredential || !navigator.credentials) throw new Error('This browser does not support passkeys.')
      await fetch('/api/auth/csrf/', { credentials: 'same-origin' })
      const optionsPath = mode === 'register' ? '/api/auth/passkey/register/options/' : '/api/auth/passkey/authenticate/options/'
      const verifyPath = mode === 'register' ? '/api/auth/passkey/register/verify/' : '/api/auth/passkey/authenticate/verify/'
      const options = decodeWebAuthnOptions(await request(optionsPath, { method: 'POST' }))
      const credential = mode === 'register' ? await navigator.credentials.create({ publicKey: options }) : await navigator.credentials.get({ publicKey: options })
      await request(verifyPath, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(webauthnCredentialPayload(credential)) })
      window.location.href = '/dashboard/'
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return <main className="flex min-h-screen items-center justify-center bg-[#f4f1ed] px-5 py-8 text-black sm:px-8"><section className="w-full max-w-lg rounded-3xl border border-black/10 bg-white/85 p-6 shadow-sm sm:p-10" aria-labelledby="login-heading"><a href="/" aria-label="Back to RetentionPulse home"><Logo /></a><p className="mt-10 text-xs font-semibold tracking-[0.2em] text-accent">RETENTIONPULSE / PRIVATE WORKSPACE</p><h1 id="login-heading" className="mt-3 text-4xl font-semibold tracking-[-0.05em] sm:text-5xl">Unlock your pulse.</h1><p className="mt-4 text-base normal-case tracking-normal text-black/65">Create a passkey for this workspace or continue with one already registered on this device.</p>{error && <p className="mt-5 rounded-xl bg-red-50 p-4 text-sm normal-case text-red-700" role="alert">{error}</p>}<div className="mt-8 grid gap-3"><button type="button" disabled={busy} onClick={() => run('authenticate')} className="rounded-full bg-black px-5 py-3 text-sm font-semibold tracking-[0.12em] text-white disabled:cursor-not-allowed disabled:opacity-50">{busy ? 'Waiting for passkey…' : 'Continue with passkey'}</button><button type="button" disabled={busy} onClick={() => run('register')} className="rounded-full border border-black/15 px-5 py-3 text-sm font-semibold tracking-[0.12em] disabled:cursor-not-allowed disabled:opacity-50">Register this device</button></div><p className="mt-5 text-sm normal-case leading-relaxed tracking-normal text-black/55">Passkeys require a supported browser. Registration is available for the first workspace device.</p></section></main>
}

function Dashboard() {
  const [analysis, setAnalysis] = useState(null)
  const [file, setFile] = useState(null)
  const [previewUrl, setPreviewUrl] = useState('')
  const [busy, setBusy] = useState(false)
  const [checking, setChecking] = useState(true)
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)
  useEffect(() => { let active = true; (async () => { try { await bootstrapCsrf(); const session = await getSession(); if (!session.authenticated) { window.location.href = authRoutes.login; return } if (active) setChecking(false) } catch (err) { if (active) { setError(err.message); setChecking(false) } } })(); return () => { active = false } }, [])
  useEffect(() => { if (!file) { setPreviewUrl(''); return undefined } const url = URL.createObjectURL(file); setPreviewUrl(url); return () => URL.revokeObjectURL(url) }, [file])
  const selectFile = (next) => { setError(''); setAnalysis(null); if (!next) return; const valid = ['video/mp4', 'video/quicktime', 'video/x-m4v'].includes(next.type) || /\.(mp4|mov|m4v)$/i.test(next.name); if (!valid) { setFile(null); setError('Choose an MP4, MOV, or M4V video.'); return } if (next.size > 250 * 1024 * 1024) { setFile(null); setError('This video exceeds the 250MB upload limit.'); return } setFile(next) }
  const submit = async (event) => { event.preventDefault(); if (!file || busy) return; setBusy(true); setError(''); try { setAnalysis(await analyzeVideo(file)) } catch (err) { if (err.name !== 'AbortError') setError(err.message) } finally { setBusy(false) } }
  const signOut = async () => { await logout(); window.location.href = '/' }
  if (checking) return <div className="flex min-h-screen items-center justify-center bg-[#f4f1ed] text-sm font-semibold tracking-[0.18em]">Checking workspace…</div>
  const ratio = analysis ? `${(analysis.risk_ratio * 100).toFixed(1)}%` : '—'
  return <main className="min-h-screen bg-[#f4f1ed] px-4 py-4 text-black sm:px-8 sm:py-5 md:px-12"><header className="mx-auto flex max-w-6xl flex-wrap items-center gap-3"><a href="/" aria-label="RetentionPulse home" className="flex min-w-0 items-center gap-2"><Logo /><span className="min-w-0 truncate text-xs font-semibold tracking-widest sm:text-sm">RP / WORKSPACE</span></a><button onClick={signOut} className="ml-auto inline-flex shrink-0 items-center gap-2 rounded-full border border-black/15 px-3 py-2 text-xs font-semibold tracking-[0.14em] hover:bg-black hover:text-white sm:px-4"><LogOut size={15} />Sign out</button></header><div className="mx-auto max-w-6xl py-10 sm:py-14"><div className="max-w-3xl"><p className="text-xs font-semibold tracking-[0.2em] text-accent">RETENTIONPULSE / ANALYSIS</p><h1 className="mt-4 text-[clamp(2.75rem,12vw,4.5rem)] font-semibold leading-[0.95] tracking-[-0.06em]">Find the seconds<br />that lose people.</h1><p className="mt-6 max-w-xl text-base normal-case tracking-normal text-black/65">Upload an edit and get a motion map of visual dead air, flagged moments, and practical repair suggestions.</p></div><form onSubmit={submit} className="mt-8 max-w-3xl sm:mt-10"><label onDragOver={(event) => { event.preventDefault(); setDragging(true) }} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); selectFile(event.dataTransfer.files[0]) }} className={`flex cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed p-6 text-center transition sm:p-12 ${dragging ? 'border-accent bg-accent/10' : 'border-black/20 bg-white/65 hover:border-accent'}`}><Upload className="text-accent" /><span className="mt-4 max-w-full break-words text-sm font-semibold tracking-[0.14em]">{file ? file.name : 'Drop your video here'}</span><span className="mt-2 text-sm normal-case tracking-normal text-black/55">MP4, MOV, or M4V · up to 250MB</span><input type="file" accept="video/mp4,video/quicktime,video/x-m4v,.mp4,.mov,.m4v" className="sr-only" onChange={(event) => selectFile(event.target.files[0])} /></label><button disabled={!file || busy} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-black px-6 py-3 text-sm font-semibold tracking-[0.12em] text-white disabled:cursor-not-allowed disabled:opacity-40 sm:w-auto">{busy ? 'Uploading and analyzing…' : analysis ? 'Analysis ready' : file ? 'Ready to scan this edit' : 'Ready to scan'}<ArrowUpRight size={17} /></button><p className="mt-3 text-sm normal-case tracking-normal text-black/55" aria-live="polite">{busy ? 'Reviewing motion, audio, and attention zones.' : analysis ? 'Your retention heatmap is ready.' : file ? 'Preview the edit, then scan for retention drops.' : 'Choose a video to begin.'}</p>{error && <p className="mt-4 flex items-center gap-2 text-sm text-red-700" role="alert"><CircleAlert size={16} />{error}</p>}</form>{file && !analysis && <div className="mt-8"><VideoPreview file={file} src={previewUrl} /></div>}{analysis && <div className="mt-14 space-y-6"><VideoPreview file={file} src={previewUrl} /><Timeline analysis={analysis} /><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><div className="sm:col-span-2 lg:col-span-4"><p className="text-xs font-semibold tracking-[0.18em] text-accent">SCAN RESULT</p><p className="mt-1 text-2xl font-semibold tracking-tight">Your edit’s retention signal at a glance</p></div><Metric label="Health score" value={`${analysis.health_score}/100`} detail={analysis.health_score >= 80 ? 'Strong visual rhythm' : 'Worth a closer cut'} /><Metric label="Duration" value={formatTime(analysis.duration)} /><Metric label="Risk time" value={formatTime(analysis.risk_seconds)} detail={`${ratio} of the edit`} /><Metric label="Flagged moments" value={analysis.segments.length} detail={analysis.segments.length ? 'Review the segments below' : 'No dead air detected'} /></div><DiagnosticDetails analysis={analysis} /><div className="grid gap-6 lg:grid-cols-2"><section className="rounded-3xl border border-black/10 bg-white/80 p-5 sm:p-7" aria-labelledby="segments-heading"><p className="text-xs font-semibold tracking-[0.18em] text-accent">FLAGGED SEGMENTS</p><h2 id="segments-heading" className="mt-1 text-2xl font-semibold tracking-tight">Where attention drops</h2>{analysis.segments.length ? <ul className="mt-5 space-y-3">{analysis.segments.map((segment, index) => <li key={`${segment.start}-${index}`} className="flex flex-col gap-1 rounded-xl bg-risk/20 px-4 py-3 text-sm sm:flex-row sm:items-center sm:justify-between"><span className="font-semibold">{formatTime(segment.start)}–{formatTime(segment.end)}</span><span className="text-black/60">{segment.duration.toFixed(1)}s · {(segment.confidence * 100).toFixed(0)}% confidence</span></li>)}</ul> : <p className="mt-5 flex items-center gap-2 text-sm text-black/60"><CheckCircle2 size={17} className="text-green-700" />Your edit keeps visual motion throughout.</p>}</section><section className="rounded-3xl border border-black/10 bg-white/80 p-5 sm:p-7" aria-labelledby="suggestions-heading"><p className="text-xs font-semibold tracking-[0.18em] text-accent">REPAIR PLAN</p><h2 id="suggestions-heading" className="mt-1 text-2xl font-semibold tracking-tight">Make the cut sharper</h2>{analysis.ai_repair_plan && <p className="mt-5 rounded-xl bg-accent/10 p-4 text-sm normal-case leading-relaxed tracking-normal">{analysis.ai_repair_plan}</p>}<ul className="mt-5 space-y-4">{analysis.suggestions.map((suggestion, index) => <li key={`${suggestion.timestamp}-${index}`} className="border-l-2 border-accent pl-4"><p className="text-sm font-semibold">{formatTime(suggestion.timestamp)} · {suggestion.action}</p><p className="mt-1 text-sm normal-case leading-relaxed tracking-normal text-black/65">{suggestion.detail}</p></li>)}</ul></section></div></div>}</div></main>
}

export default function App() { const path = window.location.pathname; if (path.startsWith('/dashboard')) return <Dashboard />; if (path.startsWith('/login')) return <Login />; return <Landing /> }
