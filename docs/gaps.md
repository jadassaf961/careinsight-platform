# Remaining gaps before a hospital pilot

This scaffold delivers Phases 1–3 fully and Phases 4–10 as a working skeleton.
Below is the work outstanding before any clinical pilot.

## Security & access

- [ ] Refresh-token rotation + revocation list (currently single short-TTL access token only)
- [ ] SSO via SAML / OIDC (Okta, Azure AD, Epic Hyperdrive context launch)
- [ ] MFA for clinician accounts
- [ ] Tenant-scoped query filters enforced at the ORM layer (defense-in-depth beyond manual checks)
- [ ] Pen-test + threat-model review

## Compliance

- [ ] HIPAA: encryption-at-rest configuration for managed Postgres, S3 (or equivalent) for PDFs, BAA in place with all vendors
- [ ] GDPR: data-subject-access and erasure flows wired to the `consent_records` table
- [ ] Audit-log retention policy + immutable storage (e.g. S3 Object Lock)
- [ ] PHI access reviews (quarterly)
- [ ] Breach-notification runbook

## ML lifecycle

- [ ] Async retraining (Celery / RQ / Cloud Run jobs) — `/retrain` is synchronous in this scaffold
- [ ] Champion-challenger evaluation before promoting a new `model_versions` row to active
- [ ] Drift monitoring (feature distribution + calibration over time)
- [ ] Fairness audit pipeline against incoming production data
- [ ] Backfill of `predictions` when a new model is promoted

## EHR integration

- [ ] Real `FHIRAdapter` implementation (SMART-on-FHIR OAuth, Patient/Encounter/RiskAssessment)
- [ ] Epic AppOrchard submission + Hyperdrive launch context
- [ ] Cerner / Oracle Health certification
- [ ] HL7 v2 ADT feed support for Meditech sites without FHIR
- [ ] Bi-directional sync: pull encounters in, push assessments out

## Clinical validation

- [ ] Retrospective validation study on the host institution's own data
- [ ] IRB review
- [ ] Sensitivity / specificity / NPV / PPV at multiple thresholds on validation cohort
- [ ] Subgroup performance audit (age, sex, race, payor) per institutional policy
- [ ] Documented intended use, contraindications, and operating envelope

## Regulatory

- [ ] FDA SaMD classification analysis (Class I / II?). Determine 510(k) vs De Novo path if applicable.
- [ ] 21 CFR Part 11 review for electronic records / signatures (intervention logging)
- [ ] EU MDR analysis if marketing in EU

## Frontend

- [ ] Full Clinician / Case-Manager / Admin dashboards (currently stubs)
- [ ] Patient queue + cohort filter UI
- [ ] Intervention recording form wired to `interventions` table
- [ ] Notifications / paging integration for newly flagged high-risk patients
- [ ] Accessibility audit (WCAG 2.1 AA)

## Reliability

- [ ] Structured logging shipped to a log aggregator (Loki / Cloud Logging)
- [ ] Prometheus metrics + Grafana dashboards
- [ ] Tracing (OpenTelemetry) across frontend → backend → ml-service
- [ ] Postgres backup verification & restore drill
