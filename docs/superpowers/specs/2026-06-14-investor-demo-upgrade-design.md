# CareInsight — Investor Demo Upgrade Design
**Date:** 2026-06-14  
**Deadline:** 3 days (investor meeting with Symz Capital)  
**Approach:** B — "MENA's Readmission Intelligence Layer"

---

## Context

CareInsight won 2nd place at a Symz Capital AI competition. Symz is now a potential investor. The follow-up meeting has an open agenda ("see how to move forward"). We will set the agenda: show the production rebuild, demo new features, present the Rizk Hospital pilot path, and make a specific funding ask.

The platform is a production-grade 30-day readmission prediction tool built for MENA hospitals. It has real ML (XGBoost/RF/LR with SHAP), an AI copilot (Gemini), discharge checklists, intervention tracking, RBAC, multi-tenancy, and audit logging. EHR integrations exist as stubs. The model runs heuristics until trained on real patient data.

---

## What We Build (3 days)

### 1. Expand Seed Data
Grow from 3 to 25 demo patients across 4 departments (Internal Medicine, Cardiology, Endocrinology, General Surgery). Mix: ~6 high-risk, ~12 medium, ~7 low. This makes the platform look like a real hospital, not a toy.

### 2. Population Risk Intelligence View (Day 1)
**New frontend page** — the most impactful addition. Shows every admitted patient ranked by readmission risk, highest to lowest.

- **Backend:** New endpoint `GET /api/v1/dashboard/population` — joins active admissions + latest prediction per patient, groups by department, returns ranked list.
- **Frontend:** New page `/ward` (or promoted to main dashboard tab). Sortable table with: patient name, MRN, department, risk score, risk tier badge (High/Medium/Low with color), top risk factor, action buttons (Run Prediction / View Chart). Summary cards at top: counts per tier.
- **Filters:** Department, Risk Tier.
- **Auth:** All clinical roles. Scoped to `hospital_id`.

This shifts the product story from "per-patient tool" to "hospital-wide intelligence platform."

### 3. ROI Impact Calculator (Day 2, AM)
**New section in Admin Dashboard.** Makes the financial case for purchasing. Projection-based (no real outcome data needed).

- **Inputs (pre-filled, editable):** Total beds, avg monthly admissions, baseline readmission rate (default 13%), avg cost per readmission (default $5,000).
- **Output:** Estimated annual readmissions | CareInsight reduction (15-20% range, cite: *BMJ 2019 meta-analysis on CDS tools*) | **Estimated annual savings: $X**.
- Clearly labeled: "Based on published literature on clinical decision support tools. Actual results depend on clinical adoption and intervention compliance."
- No backend needed — pure frontend calculation.

### 4. Model Transparency Page (Day 2, PM)
**New tab in Admin Dashboard.** Builds clinical credibility.

- Current active model: algorithm, version, trained date, CV AUC, test AUC.
- Global top-10 feature importances (aggregated across all predictions in the hospital).
- Risk tier distribution chart (High/Medium/Low counts across all active admissions).
- Total predictions made.
- **Backend:** New endpoint `GET /api/v1/dashboard/model-stats`.

---

## Investor Meeting Structure

### Pre-meeting: Send agenda the day before
> "Looking forward to Thursday. I'd like to show you what's been built since the competition, share our path to the Rizk Hospital pilot, and discuss what first-round support could unlock. ~45 minutes."

### Meeting flow
1. **Problem (5 min):** Lebanon has 150+ private hospitals with zero readmission intelligence. Epic will never reach them. Every readmission costs $4,000–8,000 and is largely preventable 48h before discharge.
2. **Demo (15 min):** Login as Case Manager → Population Risk View → drill into high-risk patient → SHAP factors → AI copilot → discharge checklist → Admin → ROI Calculator → Model Transparency.
3. **Commercial path (10 min):** Rizk Hospital pilot ($15K, 3 months) → train model on real data → reference customer → MENA expansion.
4. **Ask (10 min):** See below.
5. **Q&A (10 min).**

### The Ask
**$150,000 seed.**  
Use of funds:
- FHIR integration (work with any hospital system): $30K
- Rizk pilot execution + model training on real patient data: $40K  
- 12 months runway + part-time developer: $80K

### Team question (address proactively)
> "I'm the technical founder and built everything you're seeing. I have a developer contributing part-time. I plan to use investment to bring on a second full-time engineer and a clinical advisor from the hospital world."

### Data privacy question (address proactively)
The AI copilot sends data to Google's Gemini API. For the pilot: patient data is anonymized before reaching the AI layer. Long-term: evaluating a self-hosted LLM option.

---

## Business Model

| Stage | Price |
|---|---|
| Pilot (3 months) | $15,000 flat |
| Post-pilot license | ~$800/month per 100 beds |
| Rizk (~300 beds) | ~$2,400/month = $28,800/year |

**Market:**
- Lebanon beachhead: 150 private hospitals
- MENA prize: UAE, Saudi Arabia (2,000+ hospitals), Kuwait, Jordan
- Year 1 target: Rizk + 2 additional Lebanese hospitals = ~$72,000 ARR

---

## What We Do NOT Build in 3 Days
- Real FHIR integration (complex, needs hospital cooperation)
- Arabic language support (time-consuming to do right)
- Real outcome tracking (needs 30-day follow-up data from real patients)
- New ML features (no training data)

---

## Presentation Deck
A clean HTML slide deck (browser-based, sharable, screenshare-ready) covering: Problem → Solution → Demo screenshots → Commercial path → Team → Ask. Created as a standalone file in `docs/presentation/`.

---

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Model accuracy unvalidated on Lebanese data | Transparent: "heuristics mode until Rizk pilot provides training data" |
| EHR integrations are stubs | Framed as "Phase 2 roadmap" — Rizk uses local EHR, we'll integrate during pilot |
| Solo founder | Address proactively; use-of-funds includes hiring |
| Gemini data privacy (Law 81) | Anonymization in AI layer; self-hosted LLM option on roadmap |
| Rizk meeting not yet confirmed | Advisor-connected; present as "scheduled" |
