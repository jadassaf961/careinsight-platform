# App Redesign (Phase 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the Cuberto monochrome language into all eight app screens — Archivo display type, ink/paper/hairline chrome, one curated clinical color family, subtle motion — in four stages that each leave the app fully working.

**Architecture:** Design-system-first: re-value tokens and redesign shared components (every screen inherits ~70% of the look), then rework screens in demo-priority order. Component APIs stay identical so call sites only change where layout changes. No query/mutation/handler logic is touched anywhere.

**Tech Stack:** Tailwind 3.4 (token re-values), Archivo + Instrument Serif (already loaded), framer-motion (already a dependency; enters the shared app bundle, accepted ~+50kB gzip).

**Spec:** `docs/superpowers/specs/2026-07-03-app-redesign-design.md`

**All commands from `frontend/`. Gates per stage: `npm run lint`, `npm test`, browser screenshot.**

---

## THE MIGRATION MAP (canonical — referenced by every screen task)

Apply these substitutions wherever they appear in the files a task lists. `src/components/landing/` is **excluded** from all sweeps (the landing is finished and its dark-section colors are intentional).

### Chrome classes
| Old | New |
|---|---|
| `text-navy-700` | `text-ink` |
| `text-slate-800` / `-700` / `-600` | `text-ink` / `text-ink/80` / `text-ink/60` |
| `text-slate-500` / `-400` / `-300` | `text-ink/50` / `text-ink/40` / `text-ink/20` |
| `bg-slate-50` / `bg-slate-100` | `bg-tint` |
| `border-slate-300` / `-200` / `-100` / `-50` | `border-hairline` |
| `divide-slate-100` | `divide-hairline` |
| `shadow-sm` / `shadow-md` (on cards/tables) | *(delete)* |
| `text-brand-600 hover:text-brand-700` (links) | `text-ink underline underline-offset-2 hover:text-ink/60` |
| `bg-brand-600` / `hover:bg-brand-700` (buttons) | `bg-ink` / `hover:bg-ink/85` |
| `focus:border-brand-600` / `focus:shadow-focus` | `focus:border-ink` / `focus:ring-2 focus:ring-ink/15` |
| `accent-brand-600` (checkboxes) | `accent-ink` |
| `text-brand-600` (plain, non-link) | `text-ink` |

### Clinical colors (hex literals and status utilities)
| Old | New |
|---|---|
| `#dc2626`, `#f87171`, `text-red-700`, `text-red-300` | `#B42318` / `text-risk-high` |
| `#d97706`, `#fbbf24`, `text-amber-800`, `-700`, `-300`, `text-yellow-600` | `#B54708` / `text-risk-medium` |
| `#16a34a`, `text-green-600`, `-700`, `text-emerald-*` | `#067647` / `text-risk-low` |
| `#fee2e2`, `bg-red-50`, `bg-red-500/10` | `bg-risk-high-bg` (`#FEF3F2`) |
| `#fef3c7`, `bg-amber-50` | `bg-risk-medium-bg` (`#FFFAEB`) |
| `#dcfce7`, `bg-green-50`, `bg-emerald-50`, `-100` | `bg-risk-low-bg` (`#ECFDF3`) |
| `#fca5a5`, `border-red-200` | `border-risk-high-border` (`#FECDCA`) |
| `#fcd34d`, `border-amber-200` | `border-risk-medium-border` (`#FEDF89`) |
| `#86efac`, `border-green-200`, `border-emerald-200`, `-300` | `border-risk-low-border` (`#ABEFC6`) |
| `bg-emerald-500` / `-600` / `hover:bg-emerald-700` | `bg-risk-low` / `hover:opacity-90` |
| `bg-blue-50 text-blue-700 border-blue-200` (checkin "sent" chip) | `bg-tint text-ink/60 border border-hairline` |
| `bg-purple-50 text-purple-700 border-purple-200` (checkin "manual" chip) | `bg-tint text-ink/60 border border-hairline` |

---

## File structure

**Stage 1 (foundation):** `tailwind.config.ts`, `src/index.css`, `src/components/core/{Button,Card,Badge,Input,SectionLabel(new),DemoBadge}.tsx`, `src/components/clinical/{RiskBadge,StatCard,RiskGauge,ShapBar}.tsx`, `src/lib/appMotion.tsx` (new), `src/components/AppShell.tsx`
**Stage 2 (demo path):** `src/pages/{Login,WardView,PatientChart}.tsx`
**Stage 3 (dashboards):** `src/components/clinical/{EscalationQueue,MyTasksWidget,OutcomesPanel,SimulatedPhone,TransitionTab}.tsx`, `src/pages/{ClinicianDashboard,CaseManagerDashboard,AdminDashboard}.tsx`
**Stage 4 (long tail):** `src/pages/{PatientSearch,ModelLab}.tsx`, consistency sweep, `index.html` (drop Josefin Sans)

---

### Task 1: Tokens + CSS utilities

**Files:**
- Modify: `frontend/tailwind.config.ts`
- Modify: `frontend/src/index.css`

- [ ] **Step 1: Re-value tokens** — in `tailwind.config.ts`:

Replace the `risk` color block with:

```ts
        risk: {
          high:            "#B42318",
          medium:          "#B54708",
          low:             "#067647",
          "high-bg":       "#FEF3F2",
          "high-border":   "#FECDCA",
          "medium-bg":     "#FFFAEB",
          "medium-border": "#FEDF89",
          "low-bg":        "#ECFDF3",
          "low-border":    "#ABEFC6",
        },
```

Repoint the display face (Josefin Sans retires):

```ts
        display: ["Archivo", "system-ui", "sans-serif"],
```

- [ ] **Step 2: Restyle the CSS utility classes** — in `src/index.css`, replace the `.card`, `.btn`, `.btn-primary`, `.btn-secondary` bodies:

```css
  .card {
    @apply bg-paper rounded-xl border border-hairline p-6;
  }
  .btn {
    @apply inline-flex items-center justify-center px-5 py-2 rounded-full font-display font-semibold lowercase transition-colors;
  }
  .btn-primary {
    @apply btn bg-ink text-paper hover:bg-ink/85;
  }
  .btn-secondary {
    @apply btn bg-paper border border-hairline text-ink hover:bg-tint;
  }
```

- [ ] **Step 3: Verify** — `npm run lint` clean; app loads (colors shift globally; some screens look intermediate — expected until Stage 4).

- [ ] **Step 4: Commit**

```bash
git add frontend/tailwind.config.ts frontend/src/index.css
git commit -m "feat(redesign): curated clinical palette tokens, Archivo display face, flat utilities"
```

---

### Task 2: Core components

**Files:**
- Modify: `frontend/src/components/core/Button.tsx`
- Modify: `frontend/src/components/core/Card.tsx`
- Modify: `frontend/src/components/core/Badge.tsx`
- Modify: `frontend/src/components/core/Input.tsx`
- Create: `frontend/src/components/core/SectionLabel.tsx`

- [ ] **Step 1: `Button.tsx`** — keep the exact props interface; replace the class maps and button classes:

```tsx
const variantClasses: Record<string, string> = {
  primary:   'bg-ink text-paper border-transparent hover:bg-ink/85',
  secondary: 'bg-paper text-ink border-hairline hover:bg-tint',
  ghost:     'bg-transparent text-ink/70 border-transparent hover:text-ink hover:bg-tint',
  danger:    'bg-risk-high text-white border-transparent hover:opacity-90',
};

const sizeClasses: Record<string, string> = {
  sm: 'text-xs px-3.5 py-1.5',
  md: 'text-sm px-5 py-2',
  lg: 'text-sm px-6 py-2.5',
};
```

and in the `className` array replace

```
'rounded-md border', 'uppercase tracking-btn', 'focus:outline-none focus:shadow-focus',
```

with

```
'rounded-full border', 'lowercase font-display', 'focus:outline-none focus-visible:ring-2 focus-visible:ring-ink/15',
```

(also change `'font-sans font-medium ...'` to `'font-semibold leading-none whitespace-nowrap'` — font-display supplies the face).

- [ ] **Step 2: `Card.tsx`** — replace the outer div classes:

```tsx
      className={[
        'bg-paper rounded-xl border border-hairline overflow-hidden',
        className,
      ].join(' ')}
```

(the `elevated` prop remains accepted but no longer adds a shadow), and the heading `h3` classes become `font-display text-base font-semibold text-ink m-0 leading-snug tracking-tight`, subheading `font-sans text-sm text-ink/50 mt-0.5 m-0`.

- [ ] **Step 3: `Badge.tsx`** — replace `variantStyles`:

```tsx
const variantStyles: Record<string, React.CSSProperties> = {
  default: { background: '#f5f5f3', color: '#565656', borderColor: '#e5e5e5' },
  primary: { background: 'transparent', color: '#0f0f0f', borderColor: '#0f0f0f' },
  success: { background: '#ECFDF3', color: '#067647', borderColor: '#ABEFC6' },
  danger:  { background: '#FEF3F2', color: '#B42318', borderColor: '#FECDCA' },
  warning: { background: '#FFFAEB', color: '#B54708', borderColor: '#FEDF89' },
  navy:    { background: '#0f0f0f', color: '#ffffff', borderColor: 'transparent' },
  outline: { background: 'transparent', color: '#565656', borderColor: '#e5e5e5' },
};
```

- [ ] **Step 4: `Input.tsx`** — underline style. Replace the label classes with `font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 flex gap-0.5`, and the input `className` array with:

```tsx
          className={[
            'w-full font-sans bg-transparent text-ink placeholder:text-ink/30',
            'border-0 border-b rounded-none px-0',
            'transition-colors duration-150 outline-none',
            'focus:border-ink',
            'disabled:text-ink/40 disabled:cursor-not-allowed',
            error ? 'border-risk-high' : 'border-hairline',
            icon ? 'pl-7' : '',
            sizeClasses[size],
          ].join(' ')}
```

with `sizeClasses` becoming `sm: 'text-sm py-1.5'`, `md: 'text-sm py-2'`, `lg: 'text-lg py-2.5'`, and the icon span's `left-2.5` → `left-0`.

- [ ] **Step 5: Create `SectionLabel.tsx`** (the app-wide micro-label):

```tsx
export function SectionLabel({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={`font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 mb-3 ${className}`}
    >
      {children}
    </div>
  );
}
```

- [ ] **Step 6: Verify + commit**

`npm run lint` clean.

```bash
git add frontend/src/components/core
git commit -m "feat(redesign): ink pill buttons, hairline cards, underline inputs, core SectionLabel"
```

---

### Task 3: Clinical components + app motion

**Files:**
- Modify: `frontend/src/components/clinical/RiskBadge.tsx`
- Modify: `frontend/src/components/clinical/StatCard.tsx`
- Modify: `frontend/src/components/clinical/RiskGauge.tsx`
- Modify: `frontend/src/components/clinical/ShapBar.tsx`
- Create: `frontend/src/lib/appMotion.tsx`

- [ ] **Step 1: `RiskBadge.tsx`** — full replacement (dot + text, no pill; same props):

```tsx
interface RiskBadgeProps {
  tier: 'high' | 'medium' | 'low';
  size?: 'sm' | 'md' | 'lg';
}

const tierConfig = {
  high:   { label: 'high',   color: '#B42318' },
  medium: { label: 'medium', color: '#B54708' },
  low:    { label: 'low',    color: '#067647' },
};

const sizeConfig = {
  sm: { fontSize: '0.7rem',    dot: 5 },
  md: { fontSize: '0.8rem',    dot: 6 },
  lg: { fontSize: '0.9375rem', dot: 7 },
};

export function RiskBadge({ tier, size = 'md' }: RiskBadgeProps) {
  const t = tier.toLowerCase() as keyof typeof tierConfig;
  const v = tierConfig[t] ?? tierConfig.medium;
  const s = sizeConfig[size] ?? sizeConfig.md;

  return (
    <span
      className="inline-flex items-center gap-1.5 font-display font-semibold lowercase whitespace-nowrap"
      style={{ color: v.color, fontSize: s.fontSize }}
    >
      <span
        style={{
          width: s.dot, height: s.dot, borderRadius: '50%',
          background: v.color, flexShrink: 0, display: 'inline-block',
        }}
      />
      {v.label}
    </span>
  );
}
```

- [ ] **Step 2: `StatCard.tsx`** — full replacement (oversized-number pattern; same props + optional `countUp`):

```tsx
import { CountUp } from '@/lib/appMotion';

interface StatCardProps {
  label: string;
  value: string | number;
  delta?: number;
  deltaLabel?: string;
  tone?: 'default' | 'risk' | 'success' | 'brand';
  countUp?: boolean;
}

const toneColors: Record<string, string> = {
  default: '#0f0f0f',
  risk:    '#B42318',
  success: '#067647',
  brand:   '#0f0f0f',
};

export function StatCard({ label, value, delta, deltaLabel, tone = 'default', countUp = false }: StatCardProps) {
  const valueColor = toneColors[tone] ?? toneColors.default;
  const deltaColor = delta === undefined ? undefined : delta > 0 ? '#B42318' : '#067647';
  const numeric = typeof value === 'number';

  return (
    <div className="py-1">
      <div className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 mb-2">
        {label}
      </div>
      <div
        className="font-display text-5xl font-bold leading-none tracking-[-0.03em]"
        style={{ color: valueColor }}
      >
        {countUp && numeric ? <CountUp value={value as number} /> : value ?? '—'}
      </div>
      {delta !== undefined && (
        <div className="font-sans text-xs mt-2" style={{ color: deltaColor }}>
          {delta > 0 ? '↑' : '↓'} {Math.abs(delta)}{deltaLabel ? ` ${deltaLabel}` : ''}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create `src/lib/appMotion.tsx`**:

```tsx
import { useEffect, useRef } from "react";
import { animate, motion, useInView, useReducedMotion } from "framer-motion";

/** Quick page-content entrance: fade + 8px rise, 200ms. */
export function PageFade({ children, k }: { children: React.ReactNode; k?: string }) {
  const reduce = useReducedMotion();
  if (reduce) return <div>{children}</div>;
  return (
    <motion.div
      key={k}
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
    >
      {children}
    </motion.div>
  );
}

/** Variants for cascading rows: use with motion elements + custom={index}. */
export const listItem = {
  hidden: { opacity: 0, y: 6 },
  visible: (i: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.03, duration: 0.25, ease: "easeOut" },
  }),
};

/** Number that counts up on first viewport entry. */
export function CountUp({ value, decimals = 0 }: { value: number; decimals?: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, amount: 0.6 });
  const reduce = useReducedMotion();

  useEffect(() => {
    if (!ref.current) return;
    if (reduce || !inView) {
      if (reduce) ref.current.textContent = value.toFixed(decimals);
      return;
    }
    const controls = animate(0, value, {
      duration: 1,
      ease: "easeOut",
      onUpdate: (v) => {
        if (ref.current) ref.current.textContent = v.toFixed(decimals);
      },
    });
    return () => controls.stop();
  }, [inView, value, decimals, reduce]);

  return <span ref={ref}>{(0).toFixed(decimals)}</span>;
}
```

- [ ] **Step 4: `RiskGauge.tsx` + `ShapBar.tsx`** — apply the MIGRATION MAP hex substitutions only (`#dc2626`→`#B42318`, `#d97706`→`#B54708`, `#16a34a`→`#067647`, plus any chrome classes per the map). No structural changes.

- [ ] **Step 5: Verify + commit**

`npm run lint`, `npm test` green (StatCard renders differently but its props are unchanged, so `WardView`/dashboards compile untouched).

```bash
git add frontend/src/components/clinical frontend/src/lib/appMotion.tsx
git commit -m "feat(redesign): dot risk badges, oversized stat numbers, recolored gauge/shap, app motion kit"
```

---

### Task 4: AppShell + DemoBadge (completes Stage 1)

**Files:**
- Modify: `frontend/src/components/AppShell.tsx`
- Modify: `frontend/src/components/core/DemoBadge.tsx`

- [ ] **Step 1: `AppShell.tsx`** — replace the returned JSX (keep `links`, `useAuth`, `initials`, role filtering exactly as-is; add imports `import { useLocation } from "react-router-dom"` merged into the existing react-router import and `import { PageFade } from "@/lib/appMotion"`; add `const location = useLocation();` next to `useAuth`):

```tsx
  return (
    <div className="min-h-screen flex bg-paper">
      <aside className="w-60 flex flex-col bg-paper border-r border-hairline shrink-0">
        <div className="px-6 py-5">
          <span className="font-display text-lg font-bold tracking-tight text-ink">careinsight</span>
        </div>

        <nav className="flex-1 px-3 space-y-0.5">
          {visibleLinks.map(l => (
            <NavLink
              key={l.to}
              to={l.to}
              className={({ isActive }) =>
                [
                  'flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-sans transition-colors duration-150',
                  isActive
                    ? 'text-ink font-medium'
                    : 'text-ink/50 hover:text-ink hover:bg-tint',
                ].join(' ')
              }
            >
              {({ isActive }) => (
                <>
                  <span
                    className={`h-1.5 w-1.5 rounded-full shrink-0 transition-colors ${
                      isActive ? 'bg-ink' : 'bg-transparent'
                    }`}
                  />
                  {l.label}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="p-4 border-t border-hairline">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-tint border border-hairline flex items-center justify-center text-[0.65rem] font-display font-bold text-ink shrink-0">
              {initials(user.full_name)}
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium text-ink truncate">{user.full_name}</div>
              <div className="text-[0.65rem] text-ink/40 capitalize">{user.role}</div>
            </div>
          </div>
          <button
            onClick={logout}
            className="mt-2.5 text-xs text-ink/40 hover:text-ink transition-colors duration-150 underline underline-offset-2"
          >
            Sign out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto bg-paper p-8">
        <DemoBadge />
        <PageFade k={location.pathname}>
          <Outlet />
        </PageFade>
      </main>
    </div>
  );
```

Note: `NavLink` `className`+children-as-function is valid react-router v6. The `logo-white.svg` img is gone (wordmark text instead).

- [ ] **Step 2: `DemoBadge.tsx`** — swap the emerald classes per the MIGRATION MAP:

```tsx
    <div className="mb-4 flex justify-end">
      <span className="inline-flex items-center gap-1.5 rounded-full border border-risk-low-border bg-risk-low-bg text-risk-low px-2.5 py-0.5 text-[0.65rem] font-display font-semibold uppercase tracking-wide">
        <span className="h-1.5 w-1.5 rounded-full bg-risk-low animate-pulse" />
        Demo mode — simulated messaging
      </span>
    </div>
```

- [ ] **Step 3: Stage 1 gate**

`npm run lint`, `npm test` green. Browser: log in — paper sidebar with dot-marked active item, page content fades in on route change, risk badges everywhere are dots+text in the new palette, buttons are ink pills. Screens are ~70% restyled; body layouts still old (fixed in Stages 2–4).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/AppShell.tsx frontend/src/components/core/DemoBadge.tsx
git commit -m "feat(redesign): paper sidebar shell with page fade, demo badge on success family"
```

---

### Task 5: Login (Stage 2 begins)

**Files:**
- Modify: `frontend/src/pages/Login.tsx` (full replacement of the returned JSX; keep all state/logic lines 1–31 exactly)

- [ ] **Step 1: Replace the `return (...)` block with the split screen** (add imports: `import { Input } from "@/components/core/Input";` and `import { Button } from "@/components/core/Button";`):

```tsx
  return (
    <div className="min-h-screen flex bg-paper text-ink">
      {/* Left: mini-hero (hidden on small screens) */}
      <div className="hidden md:flex md:w-1/2 flex-col justify-between border-r border-hairline p-12">
        <span className="font-display text-lg font-bold tracking-tight">careinsight</span>
        <h1 className="font-display text-[clamp(2.5rem,4.5vw,4.5rem)] font-bold leading-[1.02] tracking-[-0.04em]">
          Every patient,<br />
          <em className="font-serifit font-normal italic">followed home.</em>
        </h1>
        <div className="border-t border-hairline pt-4 font-display text-sm font-semibold tracking-tight text-ink/40">
          predict <span className="px-2 text-ink/20">·</span> plan
          <span className="px-2 text-ink/20">·</span> discharge
          <span className="px-2 text-ink/20">·</span> follow up
        </div>
      </div>

      {/* Right: form */}
      <div className="flex flex-1 items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="mb-10 md:hidden">
            <span className="font-display text-lg font-bold tracking-tight">careinsight</span>
          </div>
          <div className="font-display text-[0.65rem] font-semibold tracking-[0.2em] uppercase text-ink/40 mb-2">
            Sign in
          </div>
          <h2 className="font-display text-3xl font-bold tracking-tight mb-10">
            Welcome <em className="font-serifit font-normal italic">back.</em>
          </h2>
          <form onSubmit={onSubmit} className="space-y-7">
            <Input
              label="Email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="username"
            />
            <Input
              label="Password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
            {error && (
              <div className="text-sm text-risk-high bg-risk-high-bg border border-risk-high-border rounded-md px-3 py-2">
                {error}
              </div>
            )}
            <Button type="submit" disabled={submitting} fullWidth size="lg">
              {submitting ? "signing in…" : "sign in"}
            </Button>
          </form>
          <p className="font-mono text-[0.65rem] text-ink/40 mt-10 leading-relaxed">
            demo accounts: physician@ · nurse@ · casemanager@ · admin@careinsight.dev
            <br />
            password: Demo123!
          </p>
        </div>
      </div>
    </div>
  );
```

- [ ] **Step 2: Verify + commit** — `npm run lint`; browser: `/login` shows the split hero, underline inputs, ink pill; signing in still lands on `/patients`.

```bash
git add frontend/src/pages/Login.tsx
git commit -m "feat(redesign): split-screen editorial login"
```

---

### Task 6: Discharge Board

**Files:**
- Modify: `frontend/src/pages/WardView.tsx`

- [ ] **Step 1: Apply these structural changes** (plus the MIGRATION MAP everywhere in the file):

1. Page header becomes:

```tsx
      <div className="mb-10">
        <h1 className="font-display text-4xl font-bold tracking-[-0.03em] text-ink">
          Discharge <em className="font-serifit font-normal italic">readiness.</em>
        </h1>
        <p className="text-sm text-ink/50 mt-2">
          Every admitted patient, their readmission risk, and what's blocking discharge.
        </p>
      </div>
```

2. The stat trio becomes a hairline-divided row (StatCard already renders the new oversized style):

```tsx
      <div className="grid grid-cols-1 md:grid-cols-3 md:divide-x md:divide-hairline border-y border-hairline py-6 mb-10 [&>*]:md:px-8 [&>*:first-child]:md:pl-0">
        <StatCard label="Blocked discharges" value={isLoading ? "—" : grouped.blocked.length} tone="risk" />
        <StatCard label="On track" value={isLoading ? "—" : grouped.on_track.length} tone="success" />
        <StatCard label="Awaiting planning" value={isLoading ? "—" : grouped.unplanned.length} />
      </div>
```

3. `GROUP_META` accents change to: blocked `"border-l-2 border-risk-high"`, on_track `""`, unplanned `""` — and group headers become:

```tsx
            <div className="mb-3 flex items-baseline gap-3">
              <h2 className="font-display text-xl font-bold tracking-tight text-ink">{meta.title}</h2>
              <span className="font-serifit italic text-lg text-ink/40">
                {groupRows.length} patient{groupRows.length !== 1 ? "s" : ""}
              </span>
            </div>
```

(drop the per-group blurb paragraph; the titles carry it).

4. Table container: `bg-paper rounded-none border-0 border-t border-hairline overflow-hidden ${meta.accent}` (tables lose the box; they're hairline-ruled lists now). `thead` becomes borderless with micro-labels: `<thead>` rows use `text-left px-4 py-3 font-display font-semibold text-ink/40 text-[0.6rem] uppercase tracking-[0.2em]` and drop `bg-slate-50 border-b`.

5. Row cells: apply the map (`hover:bg-slate-50`→`hover:bg-tint`, name cell `font-sans font-medium text-slate-800`→`font-sans font-medium text-ink`, etc.). The open-tasks chips: amber chip → `bg-risk-medium-bg border-risk-medium-border text-risk-medium`, green chip → `bg-risk-low-bg border-risk-low-border text-risk-low`. "Start discharge planning" button → `text-xs font-medium text-ink underline underline-offset-2 hover:text-ink/60`. "View chart →" → `text-ink/40 group-hover:text-ink text-xs font-medium` (add `group` to the `tr`).

- [ ] **Step 2: Verify + commit** — `npm run lint`, `npm test` (board grouping tests untouched); browser: board shows editorial title, oversized stat row, hairline tables, red rule only on the blocked group.

```bash
git add frontend/src/pages/WardView.tsx
git commit -m "feat(redesign): editorial discharge readiness board"
```

---

### Task 7: Patient Chart (completes Stage 2)

**Files:**
- Modify: `frontend/src/pages/PatientChart.tsx`

- [ ] **Step 1: Structural changes** (plus MIGRATION MAP for every remaining old class in the file):

1. Delete the local `SectionLabel` function; add `import { SectionLabel } from "@/components/core/SectionLabel";`.
2. Patient header block (inside the existing header `Card`, which now renders hairline style automatically) — replace the name/meta JSX:

```tsx
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-4 flex-wrap">
              <h1 className="font-display text-4xl font-bold tracking-[-0.03em] text-ink m-0 leading-none">
                {p.last_name}, {p.first_name}
              </h1>
              {risk.data && <RiskBadge tier={riskTier} size="lg" />}
            </div>
            <div className="font-mono text-xs text-ink/50 flex items-center gap-3">
              <span>MRN {p.mrn}</span>
              <span className="text-ink/20">·</span>
              <span>DOB {p.dob}</span>
              <span className="text-ink/20">·</span>
              <span>{p.sex}</span>
            </div>
          </div>
```

3. Tab bar: `border-brand-600 text-brand-700` → `border-ink text-ink`; inactive stays mapped (`text-slate-500`→`text-ink/50`).
4. AI copilot chat bubbles: `bg-brand-50 text-brand-700 ml-8` → `bg-tint text-ink ml-8`; assistant bubble `bg-slate-50 text-slate-800` → `bg-tint/60 text-ink`.

- [ ] **Step 2: Verify + commit** — browser: chart header is editorial, tabs ink, transition tab inherits (its own restyle lands in Task 8).

```bash
git add frontend/src/pages/PatientChart.tsx
git commit -m "feat(redesign): editorial patient chart header, ink tabs"
```

---

### Task 8: Shared clinical widgets (Stage 3 begins)

**Files:**
- Modify: `frontend/src/components/clinical/TransitionTab.tsx`
- Modify: `frontend/src/components/clinical/SimulatedPhone.tsx`
- Modify: `frontend/src/components/clinical/EscalationQueue.tsx`
- Modify: `frontend/src/components/clinical/MyTasksWidget.tsx`
- Modify: `frontend/src/components/clinical/OutcomesPanel.tsx`

- [ ] **Step 1: All five files** — delete local `SectionLabel`/inline micro-label divs where present and import `SectionLabel` from `@/components/core/SectionLabel`; then apply the MIGRATION MAP throughout (this converts every emerald/red/amber/blue/purple utility and status style to the curated family; `CHECKIN_STATUS_STYLE` and `PRIORITY_STYLE`/`PRIORITY_BADGE` maps get their values swapped per the map).

- [ ] **Step 2: `OutcomesPanel.tsx` only** — the `Metric` value div becomes the oversized pattern with count-up: replace its inner `div` with

```tsx
      <div className="font-display text-5xl font-bold leading-none tracking-[-0.03em] text-ink">
        {value}
      </div>
```

and where the panel renders percentage/count values, keep the existing `pct`/string formatting (no CountUp here — values are pre-formatted strings; dashboards use `StatCard countUp` instead).

- [ ] **Step 3: `EscalationQueue.tsx` rows** — patient name button gains `font-display font-semibold tracking-tight`; row container `border border-slate-100 hover:border-slate-200` → `border-b border-hairline last:border-0 rounded-none px-0` (rows become hairline list items, not boxes); "Resolve"/"Mark resolved" affordances per map (ink underline / ink pill).

- [ ] **Step 4: Verify + commit** — browser: patient chart Transition tab + case manager queue fully in the new language; simulated phone now green-family.

```bash
git add frontend/src/components/clinical
git commit -m "feat(redesign): transition tab, phone, queue, widgets on the curated palette"
```

---

### Task 9: Dashboards (completes Stage 3)

**Files:**
- Modify: `frontend/src/pages/ClinicianDashboard.tsx`
- Modify: `frontend/src/pages/CaseManagerDashboard.tsx`
- Modify: `frontend/src/pages/AdminDashboard.tsx`

- [ ] **Step 1: All three** — apply the MIGRATION MAP; delete local `SectionLabel` defs in favor of the core import; page `h1`s become the editorial pattern with one serif accent each:

```tsx
<h1 className="font-display text-4xl font-bold tracking-[-0.03em] text-ink">Clinician <em className="font-serifit font-normal italic">overview.</em></h1>
<h1 className="font-display text-4xl font-bold tracking-[-0.03em] text-ink">Escalation <em className="font-serifit font-normal italic">queue.</em></h1>
<h1 className="font-display text-4xl font-bold tracking-[-0.03em] text-ink">Hospital <em className="font-serifit font-normal italic">outcomes.</em></h1>
```

(Case Manager page's subtitle stays; Admin's old `text-2xl font-bold` h1 is replaced by the above.)

- [ ] **Step 2: Stat rows** — Clinician + Case Manager stat grids adopt the board's hairline-divided pattern from Task 6 (same wrapper classes) and pass `countUp` to `StatCard` where values are numbers. Admin's three `.card` stat divs become `StatCard` usages inside the same hairline-divided wrapper:

```tsx
      <div className="grid grid-cols-1 md:grid-cols-3 md:divide-x md:divide-hairline border-y border-hairline py-6 mb-10 [&>*]:md:px-8 [&>*:first-child]:md:pl-0">
        <StatCard label="Total predictions" value={stats.data?.total_predictions ?? "—"} countUp />
        <StatCard label="High-risk rate" value={stats.data ? `${(stats.data.high_risk_rate * 100).toFixed(1)}%` : "—"} tone="risk" />
        <StatCard label="Period" value={stats.data?.period ?? "—"} />
      </div>
```

(add `import { StatCard } from "@/components/clinical/StatCard";` to AdminDashboard).

- [ ] **Step 3: CaseManagerDashboard risk-distribution bars** — inline hex colors per the map (`#dc2626`→`#B42318`, `#d97706`→`#B54708`, `#16a34a`→`#067647`, backgrounds to the wash values).

- [ ] **Step 4: Verify + commit** — browser: all three dashboards coherent; count-ups fire once.

```bash
git add frontend/src/pages/ClinicianDashboard.tsx frontend/src/pages/CaseManagerDashboard.tsx frontend/src/pages/AdminDashboard.tsx
git commit -m "feat(redesign): dashboards on editorial pattern with count-up stats"
```

---

### Task 10: Search + ModelLab (Stage 4 begins)

**Files:**
- Modify: `frontend/src/pages/PatientSearch.tsx`
- Modify: `frontend/src/pages/ModelLab.tsx`

- [ ] **Step 1: `PatientSearch.tsx`** — MIGRATION MAP throughout; page h1 → `Find a <em className="font-serifit font-normal italic">patient.</em>` editorial pattern; the search input becomes hero-sized underline style (keep its state/handlers):

```tsx
          <input
            /* existing value/onChange/placeholder props unchanged */
            className="w-full bg-transparent font-display text-2xl md:text-3xl font-semibold tracking-tight text-ink placeholder:text-ink/25 border-0 border-b border-hairline focus:border-ink outline-none py-3 transition-colors"
          />
```

Result rows: hairline list treatment (`border-b border-hairline`, `hover:bg-tint`).

- [ ] **Step 2: `ModelLab.tsx`** — MIGRATION MAP throughout (7 hex/class hits); h1 → `Model <em className="font-serifit font-normal italic">lab.</em>`; metric numbers get `font-display font-bold tracking-[-0.03em]`; no layout changes.

- [ ] **Step 3: Verify + commit**

```bash
git add frontend/src/pages/PatientSearch.tsx frontend/src/pages/ModelLab.tsx
git commit -m "feat(redesign): hero search input, model lab restyle"
```

---

### Task 11: Consistency sweep + full verification (completes Stage 4)

**Files:**
- Modify: `frontend/index.html` (retire Josefin Sans from the font link)
- Modify: any files the sweep catches

- [ ] **Step 1: Sweep for stragglers** (excluding `src/components/landing/`):

```powershell
# from frontend/ — each should return ONLY landing/ files or nothing
findstr /s /n "dc2626 d97706 16a34a emerald slate-  navy- brand-" src\pages\*.tsx src\components\core\*.tsx src\components\clinical\*.tsx src\components\AppShell.tsx
```

Fix every hit per the MIGRATION MAP. Then remove `Josefin+Sans:wght@300;400;600;700&` from the Google Fonts link in `index.html` (nothing references it once `display` points to Archivo).

- [ ] **Step 2: Gates**

```powershell
npm run lint
npm test
npm run build
```

- [ ] **Step 3: Full demo-loop browser pass** (all three services, fresh session): login (split screen) → board (editorial groups, dot badges) → patient chart → Transition tab → simulated phone reply "chest pain" → RED FLAG + escalation → case manager queue → resolve with notes → admin outcomes with count-ups. Every screen coherent; color appears only as clinical state; `prefers-reduced-motion` check via the smoke-test stub path (PageFade/CountUp render statically).

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "feat(redesign): consistency sweep, retire Josefin, verification fixes"
```

---

## Self-review checklist (run after writing, fixed inline)

1. **Spec coverage:** palette re-values ✅ (T1), Archivo display ✅ (T1), core components ✅ (T2), clinical components + motion kit ✅ (T3), AppShell + demo badge ✅ (T4), Login/Board/Chart ✅ (T5–7), widgets + phone success-family ✅ (T8), dashboards + count-ups ✅ (T9), Search/ModelLab ✅ (T10), sweep + Josefin retirement + demo-loop regression pass ✅ (T11). Main-area `paper` default ✅ (T4 shell).
2. **Placeholder scan:** clean — every restyle is either full code or an explicit MIGRATION MAP substitution (the map is the single source of truth, defined once).
3. **Type consistency:** all component prop interfaces unchanged (Button/Card/Badge/Input/RiskBadge/StatCard keep their APIs; StatCard adds optional `countUp`); `SectionLabel` import path consistent (`@/components/core/SectionLabel`); `PageFade`/`CountUp`/`listItem` names consistent between T3 and consumers.
