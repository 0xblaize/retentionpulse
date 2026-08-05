import { useState } from 'react'
import { AnimatePresence, motion, useReducedMotion } from 'framer-motion'
import { ArrowUpRight, X } from 'lucide-react'

const VIDEO_URL = 'https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260517_222138_3e3205be-3364-417b-a64a-bfe087acbec4.mp4'
const navItems = ['Story', 'Expertise', 'Studios', 'Feedback']
const stats = [
  ['300', 'CRAFTED\nBRANDS'],
  ['200', 'DIGITAL\nPRODUCTS'],
  ['100', 'VENTURES\nFUNDED']
]
const ease = [0.22, 1, 0.36, 1]

const fadeDown = {
  hidden: { opacity: 0, y: -20 },
  visible: (index) => ({
    opacity: 1,
    y: 0,
    transition: { delay: index * 0.1, duration: 0.5, ease }
  })
}

const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  visible: (index) => ({
    opacity: 1,
    y: 0,
    transition: { delay: index * 0.12, duration: 0.6, ease }
  })
}

const headingReveal = {
  hidden: { y: '110%' },
  visible: (index) => ({
    y: 0,
    transition: { delay: 0.4 + index * 0.14, duration: 0.7, ease }
  })
}

function Logo() {
  return (
    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 border-accent" aria-hidden="true">
      <span className="h-2.5 w-2.5 rounded-full bg-accent" />
    </span>
  )
}

function Hamburger({ onClick, label = 'Open menu' }) {
  return (
    <button type="button" onClick={onClick} aria-label={label} className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-black focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2">
      <span className="flex flex-col gap-1">
        <span className="h-0.5 w-4 bg-white" />
        <span className="h-0.5 w-4 bg-white" />
        <span className="h-0.5 w-4 bg-white" />
      </span>
    </button>
  )
}

function App() {
  const [menuOpen, setMenuOpen] = useState(false)
  const reduceMotion = useReducedMotion()
  const initial = reduceMotion ? false : 'hidden'
  const animate = 'visible'

  return (
    <main className="relative flex min-h-screen flex-col overflow-hidden bg-[#c9c8c6] font-sans uppercase tracking-widest text-black">
      <video className="absolute inset-0 h-full w-full object-cover" src={VIDEO_URL} autoPlay muted loop playsInline aria-hidden="true" />

      <div className="relative z-10 flex min-h-screen flex-col px-5 pt-5 sm:px-8 md:px-12 md:pt-6">
        <nav className="flex h-9 shrink-0 items-center justify-between" aria-label="Primary navigation">
          <motion.a custom={0} variants={fadeDown} initial={initial} animate={animate} href="/" aria-label="RetentionPulse home" className="rounded-full focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2">
            <Logo />
          </motion.a>

          <div className="hidden items-center gap-9 md:flex">
            {navItems.map((item, index) => (
              <motion.a key={item} custom={index + 1} variants={fadeDown} initial={initial} animate={animate} href={`#${item.toLowerCase()}`} className="text-sm font-semibold tracking-widest focus:outline-none focus:ring-2 focus:ring-accent">
                {item}
              </motion.a>
            ))}
          </div>

          <motion.div custom={5} variants={fadeDown} initial={initial} animate={animate}>
            <Hamburger onClick={() => setMenuOpen(true)} />
          </motion.div>
        </nav>

        <section className="flex flex-1 items-center justify-end py-8 md:py-0" aria-label="Selected work statistics">
          <div className="flex items-start justify-end gap-5 text-right sm:gap-8 md:gap-10">
            {stats.map(([number, label], index) => (
              <motion.div key={label} custom={index + 2} variants={fadeUp} initial={initial} animate={animate} className="text-right">
                <p className="font-semibold leading-none" style={{ fontSize: 'clamp(1.5rem, 5vw, 3.5rem)' }}><span className="text-[0.5em] text-accent">+</span>{number}</p>
                <p className="whitespace-pre-line text-[10px] font-semibold leading-tight tracking-widest sm:text-xs md:text-sm">{label}</p>
              </motion.div>
            ))}
          </div>
        </section>

        <section className="flex shrink-0 flex-col gap-6 pb-8 md:gap-12 md:pb-12">
          <div className="flex items-center justify-between gap-4">
            <motion.p custom={5} variants={fadeUp} initial={initial} animate={animate} className="max-w-[130px] text-[10px] font-semibold leading-tight tracking-widest sm:max-w-[160px] sm:text-xs md:max-w-xs md:text-sm">
              Shaping Bold<br />Visions Into Power<br />For Your Tribe
            </motion.p>
            <motion.a custom={6} variants={fadeUp} initial={initial} animate={animate} href="/login/" className="inline-flex shrink-0 items-center gap-2 whitespace-nowrap text-base font-semibold tracking-wide text-accent focus:outline-none focus:ring-2 focus:ring-accent sm:text-xl md:text-2xl">
              Work With Us <ArrowUpRight size={18} className="sm:h-[22px] sm:w-[22px]" />
            </motion.a>
          </div>

          <div className="flex items-end justify-between gap-3 sm:gap-4">
            <motion.div custom={7} variants={fadeUp} initial={initial} animate={animate} className="w-[120px] shrink-0 text-left sm:w-[180px] sm:text-left md:w-[280px] md:text-right">
              <p className="text-[9px] font-semibold leading-tight tracking-widest sm:text-xs md:text-sm">Creative Studios Built Around Elevating Your Vision Into Striking Reality</p>
            </motion.div>
            <h1 className="text-right font-semibold leading-[0.88] tracking-[-0.08em]" style={{ fontSize: 'clamp(2rem, 9vw, 9rem)' }}>
              {['Fearless', 'Vision', 'Delivered'].map((word, index) => (
                <span key={word} className="block overflow-hidden">
                  <motion.span custom={index} variants={headingReveal} initial={initial} animate={animate} className="block">{word}</motion.span>
                </span>
              ))}
            </h1>
          </div>
        </section>
      </div>

      <AnimatePresence>
        {menuOpen && (
          <motion.div className="fixed inset-0 z-50 flex min-h-screen flex-col bg-white px-5 pb-8 pt-5 sm:px-8 md:px-12" initial={reduceMotion ? false : { opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: reduceMotion ? 0 : 0.25 }}>
            <div className="flex items-center justify-between">
              <a href="/" onClick={() => setMenuOpen(false)} aria-label="RetentionPulse home"><Logo /></a>
              <button type="button" onClick={() => setMenuOpen(false)} aria-label="Close menu" className="flex h-9 w-9 items-center justify-center rounded-full bg-black text-white focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"><X size={20} /></button>
            </div>
            <nav className="mt-16 flex flex-col gap-8" aria-label="Mobile navigation">
              {navItems.map((item, index) => (
                <motion.a key={item} href={`#${item.toLowerCase()}`} onClick={() => setMenuOpen(false)} className="text-3xl font-semibold tracking-widest focus:outline-none focus:ring-2 focus:ring-accent" initial={reduceMotion ? false : { opacity: 0, y: -16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: reduceMotion ? 0 : index * 0.08, duration: reduceMotion ? 0 : 0.35, ease }}>{item}</motion.a>
              ))}
            </nav>
            <a href="/login/" className="mt-auto inline-flex items-center gap-2 text-xl font-semibold tracking-wide text-accent">Work With Us <ArrowUpRight size={22} /></a>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  )
}

export default App
