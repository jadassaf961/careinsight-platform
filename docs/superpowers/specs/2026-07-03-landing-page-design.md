# CareInsight Marketing Landing Page — Design

**Date:** 2026-07-03
**Status:** Approved direction, pending spec review
**Author:** Jad Assaf (with Claude)

## 1. Why this exists

CareInsight needs a public face that matches the ambition of the product — what a hospital CEO or investor sees *before* logging in. This is Phase 1 of the frontend overhaul ("both, marketing first"); Phase 2 (in-app visual polish) gets its own spec later.

**Design direction (validated via mockups):** Cuberto-style adapted for healthcare — strict monochrome, oversized typography with italic-serif accent words, extreme whitespace, motion-first. Professional; no emojis; no decoration. The only color on the page comes from product screenshots, which makes the product glow.

## 2. Scope & routing

The landing page lives inside the existing React app:

- `/` → new public `Landing` page (no auth)
- `/login` → the existing Login page (moved from `/`)
- All authenticated routes unchanged; an authenticated user visiting `/` still reaches their dashboard (existing redirect behavior preserved)
- "See it live" / "Sign in" link to `/login` — one click from marketing site into the live demo
- "Book a demo" opens `mailto:jadassaf6000@gmail.com?subject=CareInsight demo request` — no contact-form backend (YAGNI)

**Out of scope:** in-app UI polish (Phase 2), CMS/blog, multi-language site copy, analytics, SEO beyond basic meta tags, contact-form backend.

## 3. Page structure & copy (top to bottom)

1. **Nav** — `careinsight` wordmark left; `product / outcomes / pricing` anchor links; pill button "book a demo". Transparent over the hero; solid white + hairline border after ~80px scroll.
2. **Hero** — headline "Every patient, *followed home.*" (display sans + italic serif accent; clamps ~4rem mobile → 8.5rem desktop). Sub-line: "CareInsight runs your hospital's discharge process and follows every patient for 30 days — predicting who comes back before they do." Round black "see it live" button → `/login`.
3. **Marquee band** — hairline top/bottom borders; endlessly scrolling `predict · plan · discharge · follow up`.
4. **Product section** (`#product`, ink-black) — heading "The discharge board your ward opens *every morning.*" Real product screenshot (Discharge Readiness Board) in a rounded frame with parallax; below it, three smaller screenshot cards — transition checklist, simulated WhatsApp phone, escalation queue — each with one line of copy.
5. **How it works** — four full-width hairline-divided rows: 01 Predict (readmission risk at admission, explained factor by factor) / 02 Plan (risk factors become role-assigned discharge tasks) / 03 Discharge (checklist cleared, patient leaves with a follow-up plan) / 04 Follow up (WhatsApp check-ins for 30 days; concerning answers escalate to a human).
6. **Numbers** (`#outcomes`) — oversized stats: `30 days` of automated follow-up · `4 roles` on one checklist · `94% response` rate (pilot metric; update as real data lands).
7. **Pricing** (`#pricing`) — one card: "$12 */bed/month.* Every module. Every role. No surprises." One-line note: works alongside any HIS — no EHR migration required.
8. **Footer** (ink-black) — "Bring CareInsight to *your hospital.*", pill CTA (mailto), email in large type, "careinsight — beirut · 2026".

## 4. Type & palette

- **Display sans:** Archivo (Google Fonts, variable), tight tracking (−0.04em), for headlines/stats/marquee
- **Serif accent:** Instrument Serif *italic* (Google Fonts) — accent words inside headlines only
- **Body:** Inter (already in the app)
- **Palette:** ink `#0f0f0f`, paper `#ffffff`, warm tint `#f5f5f3` (alternating sections), hairline `#e5e5e5`. No other color anywhere on the page.
- Tailwind: add `ink`/`paper` colors and `display`/`serif-accent` font families to `tailwind.config.ts`; fonts loaded via `<link>` in `index.html`.

## 5. Motion design

Stack: **framer-motion + lenis** (chosen over GSAP for React ergonomics, over CSS-only for the motion ceiling). All motion respects `prefers-reduced-motion` — animations collapse to simple fades or none.

- **Smooth scroll:** Lenis wraps the landing route only; the app keeps native scrolling. Instance created on Landing mount, destroyed on unmount.
- **Hero text reveal:** headline lines rise from behind an overflow mask, staggered ~80ms, on load; sub-line and button fade up after.
- **Scroll reveals:** section headings/content animate once at ~25% viewport entry — y-offset + opacity, ease `[0.16, 1, 0.3, 1]`.
- **Marquee:** infinite CSS-transform loop with duplicated content; pauses on hover; duration modulated by Lenis scroll velocity.
- **Magnetic buttons:** pill CTAs and the round hero button translate toward the cursor within a proximity radius, spring back on leave (`useMagnetic` hook). Pills get an ink↔white fill sweep on hover.
- **Screenshot parallax:** `useScroll` + `useTransform`, ~8% translate differential inside rounded frames.
- **How-it-works rows:** hairline divider draws 0→100% width on reveal; numbered rows stagger.
- **Stat counters:** count up from 0 on first viewport entry.
- **Nav:** transparent → solid white + hairline after 80px scroll.

## 6. Components & files

New isolated directory; the landing never imports app components and app code never imports landing components (shared surface: router, Tailwind tokens, fonts).

```
frontend/src/pages/Landing.tsx              # composition only
frontend/src/components/landing/
  LandingNav.tsx      Hero.tsx        Marquee.tsx
  ProductShowcase.tsx HowItWorks.tsx  Numbers.tsx
  Pricing.tsx         LandingFooter.tsx
  motion.ts           # shared variants, eases, viewport config
  useMagnetic.ts      # magnetic-button hook
frontend/src/assets/landing/                # product screenshots captured from the running app
```

**Modified files:** router (`/` → Landing, `/login` → Login, preserve authed redirect), `index.html` (font links + meta description/title), `tailwind.config.ts` (tokens). **New deps:** `framer-motion`, `lenis`.

**Screenshots:** captured from the seeded running app (board, transition tab with phone, escalation queue) at 2x scale, stored as optimized PNG/WebP in `assets/landing/`.

## 7. Verification

- Gates: `npm run lint` (tsc), `npm run build`, vitest smoke test that `Landing` renders all section headings
- Browser pass (preview tools): desktop (1280) and mobile (375) screenshots; reveals fire; marquee loops seamlessly; magnetic hover works; anchor links scroll; `/login` still reaches the app; reduced-motion yields a readable static page
- Performance sanity: landing route lazy-loaded so `framer-motion`/`lenis` don't weigh down the app bundle
