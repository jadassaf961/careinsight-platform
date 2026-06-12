# HIPAA Control Mapping (Placeholder)

This document is a placeholder for control mappings. **No HIPAA controls are
actually implemented in this scaffold.** Use it as a checklist when planning
the production deployment.

## §164.308 — Administrative safeguards

| Requirement | Status | Notes |
|---|---|---|
| Security management process | TODO | Risk analysis + risk management |
| Workforce security | TODO | Role-based access; this scaffold has RBAC scaffolding only |
| Information access management | TODO | RBAC ↔ minimum-necessary policy linkage |
| Security awareness & training | TODO | Out of scope of platform |
| Security incident procedures | TODO | Runbook in `docs/deployment.md` is stub |
| Contingency plan | TODO | Backup / restore drill |
| Evaluation | TODO | Periodic security review |

## §164.310 — Physical safeguards

Out of scope for application layer. Hosting environment must be evaluated.

## §164.312 — Technical safeguards

| Requirement | Status | Notes |
|---|---|---|
| Access control | PARTIAL | JWT + RBAC implemented; tenant-scoped queries TODO |
| Audit controls | PARTIAL | `audit_logs` table + middleware exists; retention + immutability TODO |
| Integrity | TODO | Field-level integrity, signed audit chain |
| Person or entity authentication | PARTIAL | Password+JWT; MFA TODO; SSO TODO |
| Transmission security | TODO | TLS termination is deployment-config concern |

## Business Associate Agreements

Required with: cloud host, managed Postgres provider, log aggregator,
Google (Gemini), any third-party EHR adapter providers.
