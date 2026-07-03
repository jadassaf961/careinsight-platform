# Marketing Landing Page Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cuberto-style monochrome marketing landing page at `/` inside the existing React app — oversized type, italic-serif accents, motion-first (Framer Motion + Lenis).

**Architecture:** A lazy-loaded `Landing` page composed from isolated components in `src/components/landing/`. Landing never imports app components; shared surface is the router, Tailwind tokens, and fonts. Motion utilities (`motion.ts`, `useMagnetic.ts`) are shared across landing components only.

**Tech Stack:** React 18, framer-motion v11, lenis v1, Tailwind 3.4, Archivo + Instrument Serif (Google Fonts), vitest + @testing-library/react (jsdom) for the smoke test.

**Spec:** `docs/superpowers/specs/2026-07-03-landing-page-design.md`

**Deliberate deviation from spec:** product screenshots are implemented as **hand-built CSS "vignettes"** (miniature recreations of the board / WhatsApp phone / escalation queue), not PNG captures. Reasons: no headless-capture tooling in this environment, vector UI stays crisp at every DPI, and vignettes can animate (rows stagger in, a message "arrives") which serves the motion-first direction better than static images. `src/assets/landing/` is therefore not created.

**All commands from `frontend/` unless noted. Windows PowerShell.**

---

## File structure

| File | Responsibility |
|---|---|
| `src/pages/Landing.tsx` | Composition + Lenis lifecycle only |
| `src/components/landing/motion.ts` | Shared eases, viewport config, `fadeUp`/`maskUp` variants |
| `src/components/landing/useMagnetic.ts` | Magnetic-button hook (spring toward cursor) |
| `src/components/landing/PillButton.tsx` | Bordered pill CTA with fill-sweep hover + magnetic |
| `src/components/landing/LandingNav.tsx` | Fixed nav, transparent→solid on scroll |
| `src/components/landing/Hero.tsx` | Masked-line headline reveal, round magnetic CTA |
| `src/components/landing/Marquee.tsx` | Velocity-modulated infinite text band |
| `src/components/landing/vignettes.tsx` | `BoardVignette`, `PhoneVignette`, `QueueVignette` (pure CSS product miniatures) |
| `src/components/landing/ProductShowcase.tsx` | Dark section: heading + parallax main vignette + 3 cards |
| `src/components/landing/HowItWorks.tsx` | 01–04 rows with divider-draw reveals |
| `src/components/landing/Numbers.tsx` | Oversized count-up stats |
| `src/components/landing/Pricing.tsx` | Single $12/bed card |
| `src/components/landing/LandingFooter.tsx` | Ink footer, big closing headline, mailto CTA |
| `src/pages/Landing.test.tsx` | jsdom smoke test (all section headings render) |

**Modified:** `src/App.tsx` (routes), `index.html` (fonts + meta), `tailwind.config.ts` (tokens), `package.json` (deps).

---

### Task 1: Dependencies, tokens, fonts, routing scaffold

**Files:**
- Modify: `frontend/package.json` (via npm install)
- Modify: `frontend/tailwind.config.ts`
- Modify: `frontend/index.html`
- Modify: `frontend/src/App.tsx`
- Create: `frontend/src/pages/Landing.tsx` (placeholder, fleshed out in Task 3)

- [ ] **Step 1: Install dependencies**

```powershell
npm install framer-motion lenis
npm install -D jsdom @testing-library/react
```

- [ ] **Step 2: Add Tailwind tokens** — in `tailwind.config.ts`, inside `theme.extend.colors` add:

```ts
        ink:      "#0f0f0f",
        paper:    "#ffffff",
        tint:     "#f5f5f3",
        hairline: "#e5e5e5",
```

and inside `theme.extend.fontFamily` add (do NOT touch the existing `display` token — the app uses it):

```ts
        hero:    ["Archivo", "system-ui", "sans-serif"],
        serifit: ["Instrument Serif", "Georgia", "serif"],
```

- [ ] **Step 3: Fonts + meta in `index.html`** — replace the existing Google Fonts `<link href=...>` line with one that also loads Archivo and Instrument Serif italic:

```html
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600;9..40,700&family=Josefin+Sans:wght@300;400;600;700&family=IBM+Plex+Mono:wght@400;500&family=Archivo:wght@500;600;700;800&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
```

and below `<title>` add:

```html
    <meta name="description" content="CareInsight runs your hospital's discharge process and follows every patient for 30 days — predicting who comes back before they do." />
```

- [ ] **Step 4: Placeholder page** — create `frontend/src/pages/Landing.tsx`:

```tsx
export function Landing() {
  return <div className="min-h-screen bg-paper" />;
}

export default Landing;
```

- [ ] **Step 5: Routing** — in `frontend/src/App.tsx`:

Replace the imports block additions and component with:

```tsx
import { Suspense, lazy } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "@/auth/AuthContext";
import { RequireAuth } from "@/auth/RequireAuth";
import { AppShell } from "@/components/AppShell";
import { Login } from "@/pages/Login";
import { PatientSearch } from "@/pages/PatientSearch";
import { PatientChart } from "@/pages/PatientChart";
import { ClinicianDashboard } from "@/pages/ClinicianDashboard";
import { CaseManagerDashboard } from "@/pages/CaseManagerDashboard";
import { AdminDashboard } from "@/pages/AdminDashboard";
import { ModelLab } from "@/pages/ModelLab";
import { WardView } from "@/pages/WardView";

const Landing = lazy(() => import("@/pages/Landing"));

function PublicHome() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/ward" replace />;
  return (
    <Suspense fallback={null}>
      <Landing />
    </Suspense>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/" element={<PublicHome />} />
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <RequireAuth>
              <AppShell />
            </RequireAuth>
          }
        >
          <Route path="/patients" element={<PatientSearch />} />
          <Route path="/patients/:id" element={<PatientChart />} />
          <Route path="/dashboard/clinician" element={<ClinicianDashboard />} />
          <Route path="/dashboard/case-manager" element={<CaseManagerDashboard />} />
          <Route path="/dashboard/admin" element={<AdminDashboard />} />
          <Route path="/model-lab" element={<ModelLab />} />
          <Route path="/ward" element={<WardView />} />
        </Route>
        <Route path="*" element={<Navigate to="/ward" replace />} />
      </Routes>
    </AuthProvider>
  );
}
```

(The old `<Route index element={<Navigate to="/ward" replace />} />` inside the layout is removed — the new top-level `/` route replaces it. Authed users hitting `/` are redirected by `PublicHome`.)

- [ ] **Step 6: Verify**

Run: `npm run lint` → clean. `npm run build` → succeeds.
In the running app: `/` shows a blank white page (placeholder) when logged out; when logged in, `/` redirects to `/ward`; `/login` still works.

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/tailwind.config.ts frontend/index.html frontend/src/App.tsx frontend/src/pages/Landing.tsx
git commit -m "feat(landing): deps, ink/paper tokens, fonts, public / route scaffold"
```

---

### Task 2: Motion utilities

**Files:**
- Create: `frontend/src/components/landing/motion.ts`
- Create: `frontend/src/components/landing/useMagnetic.ts`
- Create: `frontend/src/components/landing/PillButton.tsx`

- [ ] **Step 1: Create `motion.ts`**

```ts
/** Shared motion vocabulary for the landing page. */
export const EASE = [0.16, 1, 0.3, 1] as const;

export const VIEWPORT = { once: true, amount: 0.25 } as const;

/** Standard scroll reveal: fade + rise. Pass a custom index for stagger. */
export const fadeUp = {
  hidden: { opacity: 0, y: 48 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.9, ease: EASE, delay: i * 0.08 },
  }),
};

/** Text mask reveal: parent needs overflow-hidden. */
export const maskUp = {
  hidden: { y: "110%" },
  visible: (i: number = 0) => ({
    y: "0%",
    transition: { duration: 1, ease: EASE, delay: 0.15 + i * 0.09 },
  }),
};
```

- [ ] **Step 2: Create `useMagnetic.ts`**

```ts
import { useRef } from "react";
import { useMotionValue, useSpring } from "framer-motion";

/** Element translates toward the cursor while hovered, springs back on leave.
 * Spread the returned handlers/style onto a motion element. */
export function useMagnetic<T extends HTMLElement>(strength = 0.35) {
  const ref = useRef<T>(null);
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const x = useSpring(mx, { stiffness: 180, damping: 12, mass: 0.2 });
  const y = useSpring(my, { stiffness: 180, damping: 12, mass: 0.2 });

  function onMouseMove(e: React.MouseEvent) {
    const el = ref.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    mx.set((e.clientX - (r.left + r.width / 2)) * strength);
    my.set((e.clientY - (r.top + r.height / 2)) * strength);
  }

  function onMouseLeave() {
    mx.set(0);
    my.set(0);
  }

  return { ref, style: { x, y }, onMouseMove, onMouseLeave };
}
```

- [ ] **Step 3: Create `PillButton.tsx`**

```tsx
import { motion } from "framer-motion";
import { EASE } from "./motion";
import { useMagnetic } from "./useMagnetic";

interface PillButtonProps {
  children: React.ReactNode;
  href: string;
  /** "ink" = dark border on light bg; "paper" = light border on dark bg */
  tone?: "ink" | "paper";
  className?: string;
}

/** Bordered pill CTA: magnetic, with a fill-sweep hover. */
export function PillButton({ children, href, tone = "ink", className = "" }: PillButtonProps) {
  const m = useMagnetic<HTMLAnchorElement>(0.25);
  const border = tone === "ink" ? "border-ink text-ink" : "border-paper text-paper";
  const fill = tone === "ink" ? "bg-ink" : "bg-paper";
  const hoverText = tone === "ink" ? "group-hover:text-paper" : "group-hover:text-ink";

  return (
    <motion.a
      ref={m.ref}
      style={m.style}
      onMouseMove={m.onMouseMove}
      onMouseLeave={m.onMouseLeave}
      href={href}
      initial="rest"
      whileHover="hover"
      animate="rest"
      className={`group relative inline-flex items-center gap-2 overflow-hidden rounded-full border-[1.5px] px-7 py-3 font-hero text-sm font-semibold tracking-tight ${border} ${className}`}
    >
      <motion.span
        aria-hidden
        variants={{ rest: { y: "101%" }, hover: { y: "0%" } }}
        transition={{ duration: 0.35, ease: EASE }}
        className={`absolute inset-0 ${fill}`}
      />
      <span className={`relative z-10 transition-colors duration-300 ${hoverText}`}>
        {children}
      </span>
    </motion.a>
  );
}
```

- [ ] **Step 4: Verify** — `npm run lint` → clean.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/landing/motion.ts frontend/src/components/landing/useMagnetic.ts frontend/src/components/landing/PillButton.tsx
git commit -m "feat(landing): motion vocabulary, magnetic hook, pill button"
```

---

### Task 3: Nav, Hero, Marquee + page composition

**Files:**
- Create: `frontend/src/components/landing/LandingNav.tsx`
- Create: `frontend/src/components/landing/Hero.tsx`
- Create: `frontend/src/components/landing/Marquee.tsx`
- Modify: `frontend/src/pages/Landing.tsx`

- [ ] **Step 1: Create `LandingNav.tsx`**

```tsx
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PillButton } from "./PillButton";

const LINKS = [
  { label: "product", href: "#product" },
  { label: "outcomes", href: "#outcomes" },
  { label: "pricing", href: "#pricing" },
];

export function LandingNav() {
  const [solid, setSolid] = useState(false);

  useEffect(() => {
    const onScroll = () => setSolid(window.scrollY > 80);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  function jump(e: React.MouseEvent<HTMLAnchorElement>, href: string) {
    e.preventDefault();
    document.querySelector(href)?.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-all duration-300 ${
        solid ? "bg-paper/95 shadow-[0_1px_0_0_#e5e5e5] backdrop-blur" : "bg-transparent"
      }`}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 md:px-10">
        <a href="#top" onClick={(e) => jump(e, "#top")} className="font-hero text-lg font-800 font-bold tracking-tight text-ink">
          careinsight
        </a>
        <div className="flex items-center gap-8">
          <div className="hidden items-center gap-8 md:flex">
            {LINKS.map((l) => (
              <a
                key={l.href}
                href={l.href}
                onClick={(e) => jump(e, l.href)}
                className="font-hero text-sm font-medium text-ink/70 transition-colors hover:text-ink"
              >
                {l.label}
              </a>
            ))}
            <Link to="/login" className="font-hero text-sm font-medium text-ink/70 transition-colors hover:text-ink">
              sign in
            </Link>
          </div>
          <PillButton href="mailto:jadassaf6000@gmail.com?subject=CareInsight%20demo%20request">
            book a demo
          </PillButton>
        </div>
      </nav>
    </header>
  );
}
```

- [ ] **Step 2: Create `Hero.tsx`**

```tsx
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { EASE, maskUp } from "./motion";
import { useMagnetic } from "./useMagnetic";

export function Hero() {
  const navigate = useNavigate();
  const m = useMagnetic<HTMLButtonElement>(0.45);

  return (
    <section id="top" className="mx-auto max-w-7xl px-6 pb-20 pt-40 md:px-10 md:pb-28 md:pt-52">
      <h1 className="font-hero text-[clamp(3.2rem,9.5vw,8.5rem)] font-bold leading-[0.98] tracking-[-0.04em] text-ink">
        <span className="block overflow-hidden">
          <motion.span className="block" variants={maskUp} initial="hidden" animate="visible" custom={0}>
            Every patient,
          </motion.span>
        </span>
        <span className="block overflow-hidden">
          <motion.span className="block" variants={maskUp} initial="hidden" animate="visible" custom={1}>
            <em className="font-serifit font-normal not-italic italic">followed home.</em>
          </motion.span>
        </span>
      </h1>

      <div className="mt-12 flex flex-col items-start justify-between gap-10 md:flex-row md:items-end">
        <motion.p
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, ease: EASE, delay: 0.55 }}
          className="max-w-md text-base leading-relaxed text-ink/60 md:text-lg"
        >
          CareInsight runs your hospital's discharge process and follows every
          patient for 30 days — predicting who comes back before they do.
        </motion.p>

        <motion.button
          ref={m.ref}
          style={m.style}
          onMouseMove={m.onMouseMove}
          onMouseLeave={m.onMouseLeave}
          onClick={() => navigate("/login")}
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, ease: EASE, delay: 0.7 }}
          className="flex h-32 w-32 shrink-0 items-center justify-center rounded-full bg-ink font-hero text-sm font-semibold text-paper transition-transform hover:scale-105 md:h-40 md:w-40"
        >
          see it live
        </motion.button>
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Create `Marquee.tsx`** — the velocity-modulated infinite band:

```tsx
import { useRef, useState } from "react";
import {
  motion, useAnimationFrame, useMotionValue, useScroll,
  useSpring, useTransform, useVelocity,
} from "framer-motion";

const ITEMS = ["predict", "plan", "discharge", "follow up"];
const BASE_SPEED = 4; // percent of half-width per second

export function Marquee() {
  const baseX = useMotionValue(0);
  const { scrollY } = useScroll();
  const velocity = useVelocity(scrollY);
  const smooth = useSpring(velocity, { damping: 50, stiffness: 400 });
  const factor = useTransform(smooth, [0, 1200], [0, 4], { clamp: false });
  const [paused, setPaused] = useState(false);
  const pausedRef = useRef(paused);
  pausedRef.current = paused;

  useAnimationFrame((_, delta) => {
    if (pausedRef.current) return;
    let moveBy = -BASE_SPEED * (delta / 1000);
    moveBy *= 1 + Math.abs(factor.get());
    let next = baseX.get() + moveBy;
    if (next <= -50) next += 50;
    if (next > 0) next -= 50;
    baseX.set(next);
  });

  const x = useTransform(baseX, (v) => `${v}%`);
  const half = [...ITEMS, ...ITEMS, ...ITEMS, ...ITEMS];

  return (
    <div
      className="overflow-hidden border-y border-ink py-4"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      aria-hidden
    >
      <motion.div style={{ x }} className="flex w-max whitespace-nowrap">
        {[0, 1].map((copy) => (
          <div key={copy} className="flex shrink-0">
            {half.map((item, i) => (
              <span
                key={`${copy}-${i}`}
                className="px-6 font-hero text-2xl font-bold tracking-tight text-ink md:text-3xl"
              >
                {item} <span className="px-4 text-ink/30">·</span>
              </span>
            ))}
          </div>
        ))}
      </motion.div>
    </div>
  );
}
```

- [ ] **Step 4: Compose in `Landing.tsx`** (replace placeholder; sections added in later tasks stay commented in until built):

```tsx
import { useEffect } from "react";
import Lenis from "lenis";
import { LandingNav } from "@/components/landing/LandingNav";
import { Hero } from "@/components/landing/Hero";
import { Marquee } from "@/components/landing/Marquee";

export function Landing() {
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const lenis = new Lenis({ duration: 1.15 });
    let raf = 0;
    const loop = (t: number) => {
      lenis.raf(t);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => {
      cancelAnimationFrame(raf);
      lenis.destroy();
    };
  }, []);

  return (
    <div className="min-h-screen bg-paper font-sans text-ink antialiased">
      <LandingNav />
      <Hero />
      <Marquee />
    </div>
  );
}

export default Landing;
```

- [ ] **Step 5: Verify in browser**

`npm run lint` → clean. In the preview (logged out, `/`): headline lines rise from masks on load; round button follows the cursor and springs back; marquee scrolls continuously, accelerates while scrolling, pauses on hover; nav turns solid after scrolling; "see it live" reaches `/login`.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/landing/LandingNav.tsx frontend/src/components/landing/Hero.tsx frontend/src/components/landing/Marquee.tsx frontend/src/pages/Landing.tsx
git commit -m "feat(landing): nav, masked hero reveal, velocity marquee, lenis smooth scroll"
```

---

### Task 4: Product showcase with animated vignettes

**Files:**
- Create: `frontend/src/components/landing/vignettes.tsx`
- Create: `frontend/src/components/landing/ProductShowcase.tsx`
- Modify: `frontend/src/pages/Landing.tsx`

- [ ] **Step 1: Create `vignettes.tsx`** — pure-CSS product miniatures, children stagger in when visible:

```tsx
import { motion } from "framer-motion";
import { EASE } from "./motion";

const item = {
  hidden: { opacity: 0, y: 14 },
  visible: (i: number = 0) => ({
    opacity: 1, y: 0,
    transition: { duration: 0.6, ease: EASE, delay: 0.2 + i * 0.12 },
  }),
};

const stagger = {
  hidden: {},
  visible: { transition: { staggerChildren: 0 } },
};

function Frame({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <motion.div
      variants={stagger}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, amount: 0.4 }}
      className="rounded-2xl border border-white/10 bg-[#181818] p-4"
    >
      <div className="mb-3 font-hero text-[0.6rem] font-semibold uppercase tracking-[0.2em] text-white/40">
        {label}
      </div>
      {children}
    </motion.div>
  );
}

export function BoardVignette() {
  const rows = [
    { name: "Hassan, Layla", pct: "78%", dot: "#f87171", tasks: "3 open · pharmacist" },
    { name: "Patel, Marcus", pct: "72%", dot: "#f87171", tasks: "2 open · case manager" },
    { name: "Farhat, May", pct: "59%", dot: "#fbbf24", tasks: "all tasks done" },
  ];
  return (
    <Frame label="Discharge readiness board">
      <div className="mb-3 flex gap-2">
        {[["Blocked", "3"], ["On track", "14"], ["Response", "94%"]].map(([k, v], i) => (
          <motion.div key={k} custom={i} variants={item} className="flex-1 rounded-lg bg-white/5 p-2.5">
            <div className="text-[0.55rem] uppercase tracking-wider text-white/40">{k}</div>
            <div className="font-hero text-lg font-bold text-white">{v}</div>
          </motion.div>
        ))}
      </div>
      <div className="space-y-1.5">
        {rows.map((r, i) => (
          <motion.div key={r.name} custom={i + 3} variants={item}
            className="flex items-center justify-between rounded-lg bg-white/[0.03] px-3 py-2">
            <span className="flex items-center gap-2 text-xs text-white/80">
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: r.dot }} />
              {r.name}
            </span>
            <span className="font-mono text-[0.65rem] text-white/50">{r.pct} · {r.tasks}</span>
          </motion.div>
        ))}
      </div>
    </Frame>
  );
}

export function PhoneVignette() {
  return (
    <Frame label="Day-7 WhatsApp check-in">
      <div className="space-y-2">
        <motion.div custom={0} variants={item}
          className="max-w-[85%] rounded-xl rounded-tl-sm bg-white/8 p-2.5 text-[0.65rem] leading-relaxed text-white/75">
          مرحباً ليلى، معك مستشفى رزق للاطمئنان عليك — اليوم ٧ بعد الخروج. هل تناولت جميع أدويتك؟
        </motion.div>
        <motion.div custom={1} variants={item}
          className="ml-auto max-w-[85%] rounded-xl rounded-tr-sm bg-emerald-400/15 p-2.5 text-[0.65rem] text-emerald-100">
          نعم الحمدلله، كل شيء تمام
        </motion.div>
        <motion.div custom={2} variants={item}
          className="flex items-center gap-1.5 pt-1 text-[0.6rem] font-medium text-emerald-300">
          <span className="h-1 w-1 rounded-full bg-emerald-300" /> Responded — no concerns
        </motion.div>
      </div>
    </Frame>
  );
}

export function QueueVignette() {
  return (
    <Frame label="Escalation queue">
      <div className="space-y-1.5">
        <motion.div custom={0} variants={item} className="rounded-lg bg-red-500/10 px-3 py-2">
          <div className="flex items-center justify-between">
            <span className="text-[0.6rem] font-bold uppercase tracking-wider text-red-300">high</span>
            <span className="text-[0.6rem] text-white/40">today</span>
          </div>
          <div className="mt-0.5 text-xs text-white/80">Chest pain reported on day-2 check-in</div>
        </motion.div>
        <motion.div custom={1} variants={item} className="rounded-lg bg-white/[0.04] px-3 py-2">
          <div className="flex items-center justify-between">
            <span className="text-[0.6rem] font-bold uppercase tracking-wider text-amber-300">medium</span>
            <span className="text-[0.6rem] text-white/40">1d</span>
          </div>
          <div className="mt-0.5 text-xs text-white/80">No reply to two consecutive check-ins</div>
        </motion.div>
        <motion.div custom={2} variants={item}
          className="pt-1 text-[0.6rem] font-medium text-white/40">
          Resolved this week: 12 — every one a call that happened in time
        </motion.div>
      </div>
    </Frame>
  );
}
```

- [ ] **Step 2: Create `ProductShowcase.tsx`**

```tsx
import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { fadeUp, VIEWPORT } from "./motion";
import { BoardVignette, PhoneVignette, QueueVignette } from "./vignettes";

export function ProductShowcase() {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });
  const parallax = useTransform(scrollYProgress, [0, 1], ["4%", "-4%"]);

  return (
    <section id="product" ref={ref} className="bg-ink py-24 text-paper md:py-32">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <motion.div variants={fadeUp} initial="hidden" whileInView="visible" viewport={VIEWPORT}>
          <div className="mb-4 font-hero text-xs font-semibold uppercase tracking-[0.25em] text-white/40">
            The platform
          </div>
          <h2 className="max-w-3xl font-hero text-4xl font-bold leading-[1.05] tracking-[-0.03em] md:text-6xl">
            The discharge board your ward opens{" "}
            <em className="font-serifit font-normal italic">every morning.</em>
          </h2>
        </motion.div>

        <motion.div style={{ y: parallax }} className="mt-14">
          <motion.div variants={fadeUp} initial="hidden" whileInView="visible" viewport={VIEWPORT} custom={1}>
            <BoardVignette />
          </motion.div>
        </motion.div>

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          <motion.div variants={fadeUp} initial="hidden" whileInView="visible" viewport={VIEWPORT} custom={2}>
            <PhoneVignette />
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-white/50">
              Automated WhatsApp check-ins on days 2, 7, 14 and 30 — in Arabic
              and English. Concerning answers escalate to a human within minutes.
            </p>
          </motion.div>
          <motion.div variants={fadeUp} initial="hidden" whileInView="visible" viewport={VIEWPORT} custom={3}>
            <QueueVignette />
            <p className="mt-4 max-w-sm text-sm leading-relaxed text-white/50">
              Case managers work one priority-sorted queue. Nothing is silently
              dropped — unreachable patients become phone calls, not statistics.
            </p>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Add to `Landing.tsx`** — import and render `<ProductShowcase />` directly after `<Marquee />`.

- [ ] **Step 4: Verify in browser** — dark section reveals on scroll; the main board vignette drifts slower than the page (parallax); vignette rows stagger in; Arabic text renders correctly.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/landing/vignettes.tsx frontend/src/components/landing/ProductShowcase.tsx frontend/src/pages/Landing.tsx
git commit -m "feat(landing): dark product showcase with animated CSS vignettes and parallax"
```

---

### Task 5: How it works, Numbers, Pricing

**Files:**
- Create: `frontend/src/components/landing/HowItWorks.tsx`
- Create: `frontend/src/components/landing/Numbers.tsx`
- Create: `frontend/src/components/landing/Pricing.tsx`
- Modify: `frontend/src/pages/Landing.tsx`

- [ ] **Step 1: Create `HowItWorks.tsx`**

```tsx
import { motion } from "framer-motion";
import { EASE, fadeUp, VIEWPORT } from "./motion";

const STEPS = [
  ["01", "Predict", "Readmission risk scored at admission — explained factor by factor, not a black box."],
  ["02", "Plan", "Risk factors become discharge tasks, each assigned to the right role automatically."],
  ["03", "Discharge", "The checklist clears, the patient leaves — with a 30-day follow-up plan already scheduled."],
  ["04", "Follow up", "WhatsApp check-ins track recovery. A concerning answer reaches a case manager in minutes."],
] as const;

export function HowItWorks() {
  return (
    <section className="mx-auto max-w-7xl px-6 py-24 md:px-10 md:py-32">
      <motion.h2
        variants={fadeUp} initial="hidden" whileInView="visible" viewport={VIEWPORT}
        className="mb-16 font-hero text-4xl font-bold tracking-[-0.03em] text-ink md:text-6xl"
      >
        How it <em className="font-serifit font-normal italic">works.</em>
      </motion.h2>

      <div>
        {STEPS.map(([num, title, body], i) => (
          <motion.div
            key={num}
            initial="hidden" whileInView="visible" viewport={VIEWPORT}
            className="relative py-10 md:py-12"
          >
            <motion.span
              variants={{ hidden: { scaleX: 0 }, visible: { scaleX: 1, transition: { duration: 1, ease: EASE } } }}
              className="absolute inset-x-0 top-0 h-px origin-left bg-ink/15"
            />
            <motion.div variants={fadeUp} custom={i * 0.5}
              className="flex flex-col gap-4 md:flex-row md:items-baseline md:gap-16">
              <span className="font-hero text-2xl font-bold text-ink/25 md:w-24">{num}</span>
              <span className="font-hero text-3xl font-bold tracking-tight text-ink md:w-72 md:text-4xl">
                {title}
              </span>
              <span className="max-w-xl text-base leading-relaxed text-ink/60">{body}</span>
            </motion.div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Create `Numbers.tsx`**

```tsx
import { useEffect, useRef } from "react";
import { animate, motion, useInView } from "framer-motion";
import { EASE, fadeUp, VIEWPORT } from "./motion";

function Counter({ to }: { to: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.6 });

  useEffect(() => {
    if (!inView || !ref.current) return;
    const controls = animate(0, to, {
      duration: 1.6,
      ease: EASE as unknown as [number, number, number, number],
      onUpdate: (v) => {
        if (ref.current) ref.current.textContent = String(Math.round(v));
      },
    });
    return () => controls.stop();
  }, [inView, to]);

  return <span ref={ref}>0</span>;
}

const STATS = [
  { value: 30, suffix: "days", body: "of automated follow-up after every discharge — Arabic and English" },
  { value: 4, suffix: "roles", body: "physicians, nurses, pharmacists and case managers on one checklist" },
  { value: 94, suffix: "% response", body: "pilot check-in response rate — patients actually answer WhatsApp" },
] as const;

export function Numbers() {
  return (
    <section id="outcomes" className="border-y border-hairline bg-tint">
      <div className="mx-auto grid max-w-7xl gap-12 px-6 py-20 md:grid-cols-3 md:px-10 md:py-28">
        {STATS.map((s, i) => (
          <motion.div key={s.suffix} variants={fadeUp} initial="hidden" whileInView="visible"
            viewport={VIEWPORT} custom={i}>
            <div className="font-hero text-6xl font-bold tracking-[-0.04em] text-ink md:text-7xl">
              <Counter to={s.value} />
              <em className="ml-2 font-serifit text-4xl font-normal italic md:text-5xl">{s.suffix}</em>
            </div>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-ink/55">{s.body}</p>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Create `Pricing.tsx`**

```tsx
import { motion } from "framer-motion";
import { fadeUp, VIEWPORT } from "./motion";
import { PillButton } from "./PillButton";

export function Pricing() {
  return (
    <section id="pricing" className="mx-auto max-w-7xl px-6 py-24 md:px-10 md:py-32">
      <motion.div variants={fadeUp} initial="hidden" whileInView="visible" viewport={VIEWPORT}
        className="mx-auto max-w-3xl text-center">
        <div className="mb-4 font-hero text-xs font-semibold uppercase tracking-[0.25em] text-ink/40">
          Pricing
        </div>
        <h2 className="font-hero text-6xl font-bold tracking-[-0.04em] text-ink md:text-8xl">
          $12<em className="font-serifit text-4xl font-normal italic md:text-6xl">/bed/month.</em>
        </h2>
        <p className="mx-auto mt-6 max-w-md text-base leading-relaxed text-ink/60">
          Every module. Every role. No seat licenses, no surprises. Works
          alongside any hospital information system — no EHR migration required.
        </p>
        <div className="mt-10">
          <PillButton href="mailto:jadassaf6000@gmail.com?subject=CareInsight%20demo%20request">
            book a demo
          </PillButton>
        </div>
      </motion.div>
    </section>
  );
}
```

- [ ] **Step 4: Add all three to `Landing.tsx`** after `<ProductShowcase />`, in order: `<HowItWorks />`, `<Numbers />`, `<Pricing />`.

- [ ] **Step 5: Verify in browser** — dividers draw left-to-right as rows reveal; stats count up once; pricing pill sweeps on hover; anchors `#outcomes` / `#pricing` from the nav land correctly.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/components/landing/HowItWorks.tsx frontend/src/components/landing/Numbers.tsx frontend/src/components/landing/Pricing.tsx frontend/src/pages/Landing.tsx
git commit -m "feat(landing): how-it-works rows, count-up numbers, pricing section"
```

---

### Task 6: Footer + smoke test

**Files:**
- Create: `frontend/src/components/landing/LandingFooter.tsx`
- Modify: `frontend/src/pages/Landing.tsx`
- Test: `frontend/src/pages/Landing.test.tsx`

- [ ] **Step 1: Create `LandingFooter.tsx`**

```tsx
import { motion } from "framer-motion";
import { fadeUp, VIEWPORT } from "./motion";
import { PillButton } from "./PillButton";

export function LandingFooter() {
  return (
    <footer className="bg-ink py-24 text-paper md:py-32">
      <div className="mx-auto max-w-7xl px-6 md:px-10">
        <motion.div variants={fadeUp} initial="hidden" whileInView="visible" viewport={VIEWPORT}>
          <div className="mb-4 font-hero text-xs font-semibold uppercase tracking-[0.25em] text-white/40">
            Ready when you are
          </div>
          <h2 className="font-hero text-5xl font-bold leading-[1.02] tracking-[-0.03em] md:text-8xl">
            Bring CareInsight to{" "}
            <em className="font-serifit font-normal italic">your hospital.</em>
          </h2>
          <div className="mt-10">
            <PillButton tone="paper" href="mailto:jadassaf6000@gmail.com?subject=CareInsight%20demo%20request">
              book a demo
            </PillButton>
          </div>
          <a
            href="mailto:jadassaf6000@gmail.com"
            className="mt-16 block font-serifit text-2xl italic text-white/60 transition-colors hover:text-white md:text-4xl"
          >
            jadassaf6000@gmail.com
          </a>
          <div className="mt-12 border-t border-white/10 pt-6 font-hero text-xs text-white/30">
            careinsight — beirut · 2026
          </div>
        </motion.div>
      </div>
    </footer>
  );
}
```

- [ ] **Step 2: Add `<LandingFooter />`** as the final section in `Landing.tsx`.

- [ ] **Step 3: Write the smoke test** — create `frontend/src/pages/Landing.test.tsx`:

```tsx
// @vitest-environment jsdom
import { beforeAll, describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

beforeAll(() => {
  // jsdom lacks these; reduced-motion=true also short-circuits Lenis.
  window.matchMedia = ((query: string) => ({
    matches: query.includes("reduce"),
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;

  class MockObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() { return []; }
  }
  (window as unknown as Record<string, unknown>).IntersectionObserver = MockObserver;
  (window as unknown as Record<string, unknown>).ResizeObserver = MockObserver;
});

describe("Landing", () => {
  it("renders every section heading", async () => {
    const { Landing } = await import("./Landing");
    render(
      <MemoryRouter>
        <Landing />
      </MemoryRouter>,
    );
    expect(screen.getByText(/Every patient,/)).toBeTruthy();
    expect(screen.getByText(/every morning\./)).toBeTruthy();
    expect(screen.getByText(/How it/)).toBeTruthy();
    expect(screen.getByText("$12")).toBeTruthy();
    expect(screen.getByText(/your hospital\./)).toBeTruthy();
    expect(screen.getAllByText(/book a demo/i).length).toBeGreaterThanOrEqual(2);
  });
});
```

- [ ] **Step 4: Run tests**

Run: `npm test`
Expected: Landing smoke test + existing board tests pass. (If `$12` matching fails because the counter starts at 0, match on `/\/bed\/month\./` instead — the static suffix always renders.)

- [ ] **Step 5: Verify + commit**

`npm run lint`, `npm run build` → clean.

```bash
git add frontend/src/components/landing/LandingFooter.tsx frontend/src/pages/Landing.tsx frontend/src/pages/Landing.test.tsx
git commit -m "feat(landing): footer with oversized closing headline, smoke test"
```

---

### Task 7: Full verification pass

- [ ] **Step 1: Gates**

```powershell
cd frontend
npm run lint
npm test
npm run build
```
All clean/green.

- [ ] **Step 2: Browser pass (preview tools, logged out)**

1. Desktop (1280): full-page scroll — hero mask reveal, marquee motion + hover pause + scroll acceleration, dark showcase parallax, divider draws, counters, footer.
2. Mobile (375): headline clamps without overflow; nav links hidden, pill CTA visible; sections stack cleanly.
3. Reduced motion (`preview_resize` colorScheme n/a — use DevTools emulation via `preview_eval` `matchMedia` check or OS setting): page readable, Lenis disabled.
4. Flows: nav anchors land on sections; "see it live" + "sign in" → `/login` → log in → app works; authed user visiting `/` lands on `/ward`.

- [ ] **Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix(landing): verification pass fixes"
```

---

## Self-review checklist (run after writing, fixed inline)

1. **Spec coverage:** routing ✅ (T1), hero/marquee/nav ✅ (T3), product section ✅ (T4, vignettes deviation documented in header), how-it-works/numbers/pricing ✅ (T5), footer ✅ (T6), motion catalog ✅ (T2–T5: reveals, mask, marquee velocity, magnetic, parallax, divider draw, counters, nav state), reduced-motion ✅ (Lenis guard + framer honors OS setting via `MotionConfig` defaults — reveals still run but instantly; acceptable), fonts/tokens ✅ (T1), lazy-load ✅ (T1), smoke test ✅ (T6), verification ✅ (T7).
2. **Placeholder scan:** clean — full code in every create step.
3. **Type consistency:** `PillButton` props (`tone`) used in T3/T5/T6 match T2; `fadeUp`/`maskUp`/`VIEWPORT`/`EASE` exports match usage; `useMagnetic` return shape consistent across Hero/PillButton.
