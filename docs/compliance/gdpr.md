# GDPR Data-Subject Rights (Placeholder)

This document is a placeholder. **No GDPR data-subject flows are implemented**
in this scaffold. The `consent_records` table exists as a data model anchor only.

## Article-by-article TODOs

| Article | Right | Status | Anchor |
|---|---|---|---|
| 13/14 | Information | TODO | Patient-facing notice on intake |
| 15 | Access | TODO | `GET /patients/me/data-export` endpoint (not implemented) |
| 16 | Rectification | TODO | Patient demographics edit flow |
| 17 | Erasure ("right to be forgotten") | TODO | Soft-delete exists on `patients`; cascade + retention policy TODO |
| 18 | Restriction of processing | TODO | Per-consent flagging |
| 20 | Data portability | TODO | Structured export (FHIR JSON) |
| 21 | Objection | TODO | Opt-out from predictive scoring |
| 22 | Automated decision-making | TODO | The platform is *decision-support*, not autonomous decisioning; documentation required |

## Lawful basis (Art. 6)

Healthcare typically relies on Art. 9(2)(h) — provision of health care.
This must be confirmed per deploying institution; the platform itself takes no
position. See `consent_records.consent_type` for the lawful-basis tag once
populated.

## Data Protection Impact Assessment (DPIA)

Required before any EU deployment. Out of scope for this scaffold.
