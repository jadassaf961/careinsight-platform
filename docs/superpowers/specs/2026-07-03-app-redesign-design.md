# CareInsight App Redesign (Phase 2) — Design

**Date:** 2026-07-03
**Status:** Approved direction, pending spec review
**Author:** Jad Assaf (with Claude)

## 1. Why this exists

Phase 1 shipped a Cuberto-style monochrome marketing landing page. Phase 2 brings the same design language into the logged-in product so the screen an investor sees after clicking "see it live" matches the quality of the screen before it. Full redesign of all eight app screens, executed design-system-first in four stages so the app works after every stage.

**Color principle:** color on screen always means clinical or system state — never decoration. But the clinical palette itself is redesigned: the current bright Tailwind defaults (#dc2626 / #d97706 / #16a34a / emerald-500) are replaced with one curated, desaturated family designed to sit coherently on the ink/paper monochrome, so the whole screen reads as a single professional composition (see §2).

## 2. Design language translation

### Tokens (already in `tailwind.config.ts` from Phase 1)
- Surfaces: `paper` (#ffffff) backgrounds, `tint` (#f5f5f3) grouped areas, `hairline` (#e5e5e5) borders
- Chrome ink: `ink` (#0f0f0f) replaces navy/brand for text, buttons, links, focus rings
- The `brand-*` teal palette disappears from chrome (kept in the config during migration; a final sweep may remove unused tokens)

### Clinical palette (redesigned — one coherent, desaturated family)

The `risk.*` tokens are re-valued so clinical colors feel designed with the monochrome, not pasted on. Deep, slightly muted foregrounds (all AA-contrast on white) with barely-there warm washes for backgrounds:

| Token | Foreground | Background wash | Border |
|---|---|---|---|
| `risk.high` | `#B42318` | `#FEF3F2` | `#FECDCA` |
| `risk.medium` | `#B54708` | `#FFFAEB` | `#FEDF89` |
| `risk.low` / success | `#067647` | `#ECFDF3` | `#ABEFC6` |

Everything green-ish converges on the single `risk.low`/success family: the demo badge, the simulated phone styling, check-in "responded" states, and success chips all use `#067647` on `#ECFDF3` — no separate emerald. Escalation priorities map to the same three tokens. Result: exactly one accent family on top of ink/paper, and every instance of it means state.

### Typography
- **Archivo** becomes the app display face: page titles, section headings, stat numbers. The `display` fontFamily token is repointed from Josefin Sans to Archivo (Josefin removed from the font link once unused).
- **Instrument Serif italic**: exactly one accent word per page title ("Discharge *readiness.*", "Escalation *queue.*"). Never in body text, tables, or labels.
- **DM Sans** stays for body/UI. **IBM Plex Mono** stays for MRNs, percentages, timestamps.

### Surfaces & depth
Cards flatten: hairline borders, no shadows, more padding. Grouped content separates with hairline dividers instead of nested boxes.

## 3. Design system components (redesigned once, inherited everywhere)

| Component | Becomes |
|---|---|
| `core/Button` | Ink pill: filled primary / hairline-outlined secondary, lowercase Archivo label, fill-sweep hover (from landing `PillButton` pattern, no magnetic) |
| `core/Card` | Hairline border, no shadow, larger padding |
| `SectionLabel` (promoted to `core/`) | App-wide uppercase micro-label: 0.65rem, 0.2em tracking, ink/40 |
| `core/Input` | Hairline underline style, ink focus, micro-label above |
| `core/Badge` | Ink-outlined neutral; colored variants only for clinical states |
| `clinical/RiskBadge` | Colored dot + colored text ("● high"), no filled pill |
| `clinical/StatCard` | Oversized Archivo number + micro-label + optional serif-italic unit, hairline-separated (landing Numbers pattern); optional count-up |
| `clinical/RiskGauge`, `ShapBar` | Recolored: ink chrome + clinical colors only |

## 4. AppShell

Sidebar: paper background, hairline right border, lowercase `careinsight` wordmark in Archivo, nav items ink/50 → ink with a small ink dot marker when active, minimal user block, ink "sign out" link. Demo badge restyled to the success family (§2 palette). Main content area stays `tint` or goes `paper` — whichever reads calmer against flattened cards (decide in implementation; default `paper` with `tint` reserved for grouped sub-areas).

## 5. Screens

1. **Login** — split screen. Left (hidden `md:` down): paper mini-hero "Every patient, *followed home.*" + thin marquee band at the bottom. Right: centered form — micro-labels, underline inputs, ink pill "sign in", demo accounts hint in mono.
2. **Discharge Board** — title "Discharge *readiness.*"; stats as oversized-number row; group headers as Archivo + serif-italic counts ("Blocked — *3 patients*"); flat hairline tables, micro-label column heads, dot risk badges; blocked group keeps a thin red left rule as its only colored chrome.
3. **Patient Chart** — editorial header: name at ~3rem Archivo, mono meta-line (MRN · DOB · sex), inline risk dot; ink underline tabs; all cards → hairline sections; Transition tab/timeline/phone inherit (phone restyled to the success family).
4. **Clinician & Case Manager dashboards** — oversized stat numbers with count-ups; escalation queue rows: priority dot, Archivo patient name, hairline separators, ink resolve affordance.
5. **Admin dashboard** — outcomes panel numbers oversized + count-up; ROI calculator with underline inputs and Archivo results; `.card` divs get hairline treatment.
6. **Patient Search** — near-hero-sized underline search input; results as hairline rows.
7. **ModelLab** — component inheritance + micro-labels/Archivo numbers; no layout invention.
8. **Shared widgets** (`EscalationQueue`, `MyTasksWidget`, `OutcomesPanel`, `SimulatedPhone`, `DemoBadge`) — same vocabulary; phone/badge move to the §2 success family.

## 6. Motion (subtle & purposeful)

New `src/lib/appMotion.ts`:
- `pageFade` — page content fades up 8px over 200ms on mount
- `rowStagger` — table/list rows cascade 30ms apart, once
- `CountUp` — dashboard stat numbers count up ~1s on first view

No Lenis, no magnetic, no parallax in the app. All motion respects `prefers-reduced-motion`. Accepted trade-off: importing framer-motion in app code moves it from the Landing-only chunk into the shared bundle (~+50kB gzip on app load).

## 7. Staging & verification

Four stages; the app is fully functional after each:

1. **Foundation** — repoint `display` token to Archivo, redesign core + clinical components, AppShell, `appMotion.ts`
2. **Demo path** — Login, Discharge Board, Patient Chart
3. **Dashboards** — Clinician, Case Manager, Admin + shared widgets
4. **Long tail** — Patient Search, ModelLab, consistency sweep (leftover navy/brand/slate classes, unused Josefin link)

Gates per stage: `npm run lint`, `npm test`, browser screenshots. Final pass: complete demo loop (board → chart → transition tab → simulated phone reply → escalation queue → outcomes) to prove zero functional regression — the redesign touches classNames and JSX structure, never queries, mutations, or handlers.

**Out of scope:** dark mode, mobile-first rework of clinical tables (they remain desktop-first), backend changes of any kind.
