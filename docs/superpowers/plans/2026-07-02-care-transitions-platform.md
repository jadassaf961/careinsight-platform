# Care Transitions Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn CareInsight from a readmission predictor into a care-transitions workflow platform: discharge readiness board, role-assigned checklists, WhatsApp post-discharge check-ins (simulated + Twilio), escalation queue, and an outcomes loop.

**Architecture:** All new work extends the existing backend (FastAPI) and frontend (React/Vite). The ML service is untouched. New ORM models follow the existing `UUIDPKMixin + TimestampMixin + hospital_id` pattern; new routes follow the one-file-per-resource pattern in `api/v1/`; scheduling is in-process APScheduler; messaging is a provider interface with simulated and Twilio implementations.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, APScheduler, httpx (Twilio REST, no SDK), React 18, TanStack Query v5, Tailwind.

**Spec:** `docs/superpowers/specs/2026-07-02-care-transitions-platform-design.md`

**Deliberate deviations from spec (documented here so nobody hunts for missing pieces):**
1. `MessageTemplate` is a code constants module (`app/services/messaging/templates.py`), not a DB table — no v1 UI edits templates; a DB table is phase 2.
2. CSV import is a script (`backend/scripts/import_patients_csv.py`), not an endpoint — it's pilot ops tooling.
3. Risk-driven tasks attach via an explicit `refresh-tasks` endpoint + UI button rather than hooking the prediction flow — keeps `predictions.py` untouched.

**Environment notes:**
- The `Patient` table gains columns. Dev DB must be reset once: `Remove-Item backend\dev.db` then restart backend (SQLite auto-creates). Alembic revision for Postgres is deferred to deployment (per CLAUDE.md, migrations are Postgres-only).
- All backend commands run from `backend/`: `py -m pytest tests/test_x.py -v`. Frontend from `frontend/`: `npm run lint`, `npm test`.
- Tests never call the ML service and never run APScheduler (the conftest `TestClient(app)` is not used as a context manager, so lifespan never runs in tests).

---

## File structure

**Backend — create:**
| File | Responsibility |
|---|---|
| `app/models/transition.py` | `PlanStatus`, `TaskStatus`, `TransitionPlan`, `TransitionTask` |
| `app/models/followup.py` | `CheckinStatus`, `EscalationPriority`, `EscalationStatus`, `FollowUpCheckin`, `CheckinResponse`, `Escalation`, `ReadmissionEvent` |
| `app/schemas/transition.py` | Plan/task/board Pydantic schemas |
| `app/schemas/followup.py` | Checkin/escalation/outcomes schemas |
| `app/services/messaging/base.py` | `OutboundMessage`, `SendError`, `MessagingProvider` protocol |
| `app/services/messaging/simulated.py` | `SimulatedProvider` |
| `app/services/messaging/twilio_whatsapp.py` | `TwilioWhatsAppProvider` + `validate_twilio_signature` |
| `app/services/messaging/templates.py` | Bilingual check-in templates + reply scoring keywords + `render_checkin` + `score_reply` |
| `app/services/messaging/__init__.py` | `get_provider()` factory |
| `app/services/transition_service.py` | `role_for_item`, `create_plan`, `refresh_risk_tasks`, `discharge_plan` |
| `app/services/followup_service.py` | `schedule_checkins`, `find_due_checkins`, `dispatch_due_checkins`, `record_response`, `mark_no_responses`, `run_cycle` |
| `app/api/v1/transitions.py` | plans, tasks, board, discharge |
| `app/api/v1/checkins.py` | timeline + simulate-reply (demo mode) |
| `app/api/v1/escalations.py` | queue list + resolve |
| `app/api/v1/outcomes.py` | readmission events + metrics |
| `app/api/v1/webhooks.py` | Twilio inbound webhook |
| `scripts/import_patients_csv.py` | pilot CSV loader |
| `tests/test_transition_service.py`, `tests/test_transitions_api.py`, `tests/test_reply_scoring.py`, `tests/test_followup_service.py`, `tests/test_checkins_api.py`, `tests/test_escalations_api.py`, `tests/test_outcomes_api.py`, `tests/test_webhooks.py` | per-unit tests |

**Backend — modify:** `app/models/patient.py` (phone/language/opt-out), `app/models/user.py` (PHARMACIST), `app/api/deps.py` (PHARMACIST in clinical roles), `app/models/__init__.py`, `app/api/v1/__init__.py`, `app/core/config.py`, `app/main.py` (scheduler + `/api/v1/meta`), `app/db/seed.py` (pharmacist user + demo transitions), `pyproject.toml` (apscheduler).

**Frontend — create:** `src/lib/board.ts` (+ `src/lib/board.test.ts`), `src/components/clinical/TransitionTab.tsx`, `src/components/clinical/SimulatedPhone.tsx`, `src/components/clinical/EscalationQueue.tsx`, `src/components/clinical/MyTasksWidget.tsx`, `src/components/clinical/OutcomesPanel.tsx`, `src/components/core/DemoBadge.tsx`.

**Frontend — modify:** `src/lib/api.ts` (patch method + types), `src/pages/WardView.tsx` (board), `src/pages/PatientChart.tsx` (tabs), `src/pages/CaseManagerDashboard.tsx` (queue), `src/pages/ClinicianDashboard.tsx` (widget), `src/pages/AdminDashboard.tsx` (outcomes + per-bed ROI), `src/components/AppShell.tsx` (demo badge).

---

### Task 1: Config, roles, patient contact fields

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/models/user.py`
- Modify: `backend/app/api/deps.py`
- Modify: `backend/app/models/patient.py`
- Modify: `backend/app/schemas/patient.py`
- Modify: `backend/pyproject.toml`
- Test: `backend/tests/test_transitions_api.py` (started here, grows in Task 4)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_transitions_api.py`:

```python
"""Transitions API + config/role prerequisites."""
from __future__ import annotations

from app.core.config import Settings
from app.models.user import RoleName


def test_pharmacist_role_exists():
    assert RoleName.PHARMACIST.value == "pharmacist"


def test_settings_have_messaging_defaults():
    s = Settings(_env_file=None)
    assert s.messaging_provider == "simulated"
    assert s.checkin_day_offsets_list == [2, 7, 14, 30]
    assert s.checkin_no_response_hours == 48
    assert s.checkin_max_attempts == 3
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -m pytest tests/test_transitions_api.py -v`
Expected: FAIL — `AttributeError: PHARMACIST` and missing settings attributes.

- [ ] **Step 3: Implement**

In `backend/app/models/user.py`, add to `RoleName` after `CASE_MANAGER`:

```python
    PHARMACIST = "pharmacist"
```

In `backend/app/api/deps.py`, replace `require_any_clinical_role` body:

```python
def require_any_clinical_role():
    return require_role(
        RoleName.ADMIN, RoleName.PHYSICIAN, RoleName.RESIDENT,
        RoleName.NURSE, RoleName.CASE_MANAGER, RoleName.PHARMACIST,
    )
```

In `backend/app/core/config.py`, add inside `Settings` after the `gemini_api_key` field:

```python
    # Messaging / follow-up engine
    messaging_provider: str = "simulated"  # simulated | twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = ""  # e.g. +14155238886
    checkin_day_offsets: str = "2,7,14,30"
    checkin_no_response_hours: int = 48
    checkin_max_attempts: int = 3
    checkin_retry_minutes: int = 30
```

and a property next to `cors_origins_list`:

```python
    @property
    def checkin_day_offsets_list(self) -> list[int]:
        return [int(x) for x in self.checkin_day_offsets.split(",") if x.strip()]
```

In `backend/app/models/patient.py`, add to `Patient` after `sex`:

```python
    phone_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    preferred_language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    messaging_opted_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
```

and add `Boolean` to the `sqlalchemy` import line.

In `backend/app/schemas/patient.py`:
- `PatientCreate`: add `phone_number: str | None = Field(None, max_length=40)` and `preferred_language: str = Field("en", max_length=8)`.
- `PatientRead`: add `phone_number: str | None`, `preferred_language: str`, `messaging_opted_out: bool`.

In `backend/pyproject.toml`, add `"apscheduler>=3.10"` to the `dependencies` list, then run `py -m pip install ".[dev]"`.

- [ ] **Step 4: Run tests**

Run: `py -m pytest tests/test_transitions_api.py -v` → PASS. Then `py -m pytest` → full suite still green (patient schema additions are optional-with-defaults, so existing tests pass).

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/config.py backend/app/models/user.py backend/app/api/deps.py backend/app/models/patient.py backend/app/schemas/patient.py backend/pyproject.toml backend/tests/test_transitions_api.py
git commit -m "feat(transitions): add pharmacist role, patient contact fields, messaging settings"
```

---

### Task 2: Transition + follow-up ORM models

**Files:**
- Create: `backend/app/models/transition.py`
- Create: `backend/app/models/followup.py`
- Modify: `backend/app/models/__init__.py`
- Test: `backend/tests/test_transition_service.py` (started here)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_transition_service.py`:

```python
"""Transition models + transition_service unit tests."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.followup import (
    CheckinStatus, Escalation, EscalationPriority, EscalationStatus,
    FollowUpCheckin, ReadmissionEvent,
)
from app.models.hospital import Department, Hospital
from app.models.patient import Admission, Patient
from app.models.transition import PlanStatus, TaskStatus, TransitionPlan, TransitionTask


def make_admission(db: Session, hospital: Hospital, phone: str | None = "+96170000001") -> Admission:
    dept = db.query(Department).filter(Department.hospital_id == hospital.id).first()
    p = Patient(
        hospital_id=hospital.id, mrn=f"MRN-{datetime.now().timestamp()}",
        first_name="Test", last_name="Patient", dob=datetime(1960, 1, 1).date(),
        sex="F", phone_number=phone,
    )
    db.add(p)
    db.flush()
    adm = Admission(
        patient_id=p.id, department_id=dept.id, admission_type="emergency",
        admitted_at=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
        clinical_features={},
    )
    db.add(adm)
    db.commit()
    db.refresh(adm)
    return adm


def test_models_round_trip(db: Session, hospital: Hospital):
    adm = make_admission(db, hospital)
    plan = TransitionPlan(hospital_id=hospital.id, admission_id=adm.id)
    db.add(plan)
    db.flush()
    db.add(TransitionTask(
        hospital_id=hospital.id, plan_id=plan.id, role="nurse",
        title="Educate patient", source="default",
    ))
    db.add(FollowUpCheckin(
        hospital_id=hospital.id, plan_id=plan.id, patient_id=adm.patient_id,
        day_offset=2, scheduled_at=datetime(2026, 7, 3, 10, 0, tzinfo=timezone.utc),
    ))
    db.add(Escalation(
        hospital_id=hospital.id, patient_id=adm.patient_id,
        trigger="red_flag", detail="chest pain", priority=EscalationPriority.HIGH,
    ))
    db.commit()

    saved = db.query(TransitionPlan).one()
    assert saved.status == PlanStatus.PLANNING
    assert saved.tasks[0].status == TaskStatus.OPEN
    assert db.query(FollowUpCheckin).one().status == CheckinStatus.SCHEDULED
    assert db.query(Escalation).one().status == EscalationStatus.OPEN
    assert db.query(ReadmissionEvent).count() == 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `py -m pytest tests/test_transition_service.py -v`
Expected: FAIL — `ModuleNotFoundError: app.models.transition`.

- [ ] **Step 3: Create the model files**

Create `backend/app/models/transition.py`:

```python
"""TransitionPlan + TransitionTask ORM models — the discharge workflow."""
from __future__ import annotations

import enum
import uuid
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin, UUIDType


class PlanStatus(str, enum.Enum):
    PLANNING = "planning"
    READY = "ready"
    DISCHARGED = "discharged"
    CLOSED = "closed"


class TaskStatus(str, enum.Enum):
    OPEN = "open"
    DONE = "done"
    SKIPPED = "skipped"


class TransitionPlan(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "transition_plans"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    admission_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("admissions.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True,
    )
    status: Mapped[PlanStatus] = mapped_column(
        Enum(PlanStatus, name="plan_status"),
        default=PlanStatus.PLANNING, nullable=False,
    )
    target_discharge_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    admission = relationship("Admission")
    tasks: Mapped[list["TransitionTask"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan",
        order_by="TransitionTask.created_at",
    )


class TransitionTask(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "transition_tasks"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("transition_plans.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    role: Mapped[str] = mapped_column(String(40), nullable=False)  # RoleName value
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status"), default=TaskStatus.OPEN, nullable=False,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # what generated this task: "default" | "risk_tier" | a risk-factor label
    source: Mapped[str] = mapped_column(String(255), nullable=False)

    plan: Mapped[TransitionPlan] = relationship(back_populates="tasks")
```

Create `backend/app/models/followup.py`:

```python
"""Follow-up engine ORM models: check-ins, responses, escalations, outcomes."""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPKMixin, UUIDType


class CheckinStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    SENT = "sent"
    RESPONDED = "responded"
    NO_RESPONSE = "no_response"
    SEND_FAILED = "send_failed"
    MANUAL = "manual"
    SKIPPED = "skipped"


class EscalationPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EscalationStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"


class FollowUpCheckin(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "followup_checkins"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("transition_plans.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    day_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[CheckinStatus] = mapped_column(
        Enum(CheckinStatus, name="checkin_status"),
        default=CheckinStatus.SCHEDULED, nullable=False,
    )
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sent_body: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    language: Mapped[str] = mapped_column(String(8), default="en", nullable=False)

    responses: Mapped[list["CheckinResponse"]] = relationship(
        back_populates="checkin", cascade="all, delete-orphan",
    )


class CheckinResponse(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "checkin_responses"

    checkin_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("followup_checkins.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # provider message id for webhook idempotency (unique when present)
    provider_message_id: Mapped[str | None] = mapped_column(
        String(80), nullable=True, unique=True,
    )
    raw_text: Mapped[str] = mapped_column(String(2000), nullable=False)
    red_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    meds_missed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    opted_out: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    concern_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    checkin: Mapped[FollowUpCheckin] = relationship(back_populates="responses")


class Escalation(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "escalations"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    # nullable: unmatched inbound messages have no patient
    patient_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("patients.id", ondelete="CASCADE"), nullable=True, index=True,
    )
    checkin_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("followup_checkins.id", ondelete="SET NULL"), nullable=True,
    )
    # red_flag | meds_missed | no_response | send_failed | opted_out | unmatched_message
    trigger: Mapped[str] = mapped_column(String(60), nullable=False)
    detail: Mapped[str] = mapped_column(String(1000), nullable=False)
    priority: Mapped[EscalationPriority] = mapped_column(
        Enum(EscalationPriority, name="escalation_priority"), nullable=False,
    )
    status: Mapped[EscalationStatus] = mapped_column(
        Enum(EscalationStatus, name="escalation_status"),
        default=EscalationStatus.OPEN, nullable=False,
    )
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("users.id"), nullable=True,
    )
    resolution_notes: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ReadmissionEvent(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "readmission_events"

    hospital_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("hospitals.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True,
    )
    prior_admission_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("admissions.id", ondelete="CASCADE"), nullable=False,
    )
    readmission_admission_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("admissions.id", ondelete="CASCADE"),
        nullable=False, unique=True,
    )
    days_since_discharge: Mapped[int] = mapped_column(Integer, nullable=False)
```

In `backend/app/models/__init__.py`, append:

```python
from app.models.transition import (  # noqa: F401
    PlanStatus,
    TaskStatus,
    TransitionPlan,
    TransitionTask,
)
from app.models.followup import (  # noqa: F401
    CheckinResponse,
    CheckinStatus,
    Escalation,
    EscalationPriority,
    EscalationStatus,
    FollowUpCheckin,
    ReadmissionEvent,
)
```

- [ ] **Step 4: Run tests**

Run: `py -m pytest tests/test_transition_service.py -v` → PASS. Then `py -m pytest` → green.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/transition.py backend/app/models/followup.py backend/app/models/__init__.py backend/tests/test_transition_service.py
git commit -m "feat(transitions): transition plan, task, checkin, escalation, outcome models"
```

---

### Task 3: Transition service — task generation, plan lifecycle

**Files:**
- Create: `backend/app/services/transition_service.py`
- Test: `backend/tests/test_transition_service.py` (extend)

- [ ] **Step 1: Write the failing tests** — append to `backend/tests/test_transition_service.py`:

```python
from app.services import transition_service


def test_role_for_item_mapping():
    assert transition_service.role_for_item("Perform full medication reconciliation before discharge") == "pharmacist"
    assert transition_service.role_for_item("Schedule follow-up appointment within 7 days of discharge") == "case_manager"
    assert transition_service.role_for_item("Nephrology referral; monitor renal function post-discharge") == "case_manager"
    assert transition_service.role_for_item("Provide written discharge summary in patient's preferred language") == "physician"
    assert transition_service.role_for_item("Screen for social determinants: housing, food access, transport") == "nurse"


def test_create_plan_generates_default_tasks(db: Session, hospital: Hospital):
    adm = make_admission(db, hospital)
    plan = transition_service.create_plan(db, adm, hospital.id)
    db.commit()
    assert plan.status == PlanStatus.PLANNING
    titles = [t.title for t in plan.tasks]
    assert "Confirm patient has correct medications and understands dosing" in titles
    assert all(t.source == "default" for t in plan.tasks)
    assert {t.role for t in plan.tasks} <= {"physician", "nurse", "case_manager", "pharmacist"}


def test_create_plan_twice_rejected(db: Session, hospital: Hospital):
    adm = make_admission(db, hospital)
    transition_service.create_plan(db, adm, hospital.id)
    db.commit()
    import pytest
    with pytest.raises(ValueError):
        transition_service.create_plan(db, adm, hospital.id)


def test_discharge_plan_sets_status_and_discharged_at(db: Session, hospital: Hospital):
    adm = make_admission(db, hospital)
    plan = transition_service.create_plan(db, adm, hospital.id)
    db.commit()
    now = datetime(2026, 7, 2, 9, 0, tzinfo=timezone.utc)
    transition_service.discharge_plan(db, plan, now=now)
    db.commit()
    assert plan.status == PlanStatus.DISCHARGED
    assert db.get(Admission, adm.id).discharged_at is not None
    # check-ins were scheduled (detail asserted in followup tests)
    assert db.query(FollowUpCheckin).filter(FollowUpCheckin.plan_id == plan.id).count() == 4
```

- [ ] **Step 2: Run to verify failure**

Run: `py -m pytest tests/test_transition_service.py -v`
Expected: FAIL — `ImportError: transition_service`.

- [ ] **Step 3: Implement** — create `backend/app/services/transition_service.py`:

```python
"""Transition plan + task lifecycle. Tasks are generated from the discharge
checklist (base items + risk-factor items when a prediction exists) and
assigned to a role by keyword."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.patient import Admission
from app.models.transition import PlanStatus, TaskStatus, TransitionPlan, TransitionTask
from app.services import followup_service
from app.services.checklist_service import generate_checklist

# Keyword → role routing, checked in order; first match wins.
_ROLE_RULES: list[tuple[tuple[str, ...], str]] = [
    (("medication", "medications", "dosing", "nrt prescription"), "pharmacist"),
    (("follow-up", "referral", "case management", "care coordination",
      "community health", "social work", "benefits"), "case_manager"),
    (("discharge summary", "root cause", "care instructions"), "physician"),
]


def role_for_item(text: str) -> str:
    lowered = text.lower()
    for keywords, role in _ROLE_RULES:
        if any(k in lowered for k in keywords):
            return role
    return "nurse"


def _latest_prediction(admission: Admission):
    return admission.predictions[0] if admission.predictions else None


def _checklist_items(admission: Admission) -> list[dict[str, str]]:
    pred = _latest_prediction(admission)
    if pred is None:
        return generate_checklist([], "low")
    factors = [(f.feature_name, f.shap_value) for f in pred.risk_factors]
    return generate_checklist(factors, pred.risk_tier)


def create_plan(db: Session, admission: Admission, hospital_id: uuid.UUID) -> TransitionPlan:
    existing = db.query(TransitionPlan).filter(
        TransitionPlan.admission_id == admission.id
    ).first()
    if existing is not None:
        raise ValueError("A transition plan already exists for this admission")
    plan = TransitionPlan(hospital_id=hospital_id, admission_id=admission.id)
    db.add(plan)
    db.flush()
    for item in _checklist_items(admission):
        source = "default" if item["source"] == "base" else item["source"]
        db.add(TransitionTask(
            hospital_id=hospital_id, plan_id=plan.id,
            role=role_for_item(item["text"]), title=item["text"], source=source,
        ))
    db.flush()
    db.refresh(plan)
    return plan


def refresh_risk_tasks(db: Session, plan: TransitionPlan) -> int:
    """Append checklist items missing from the plan (e.g. after a new
    prediction). Returns the number of tasks added."""
    admission = plan.admission
    existing_titles = {t.title for t in plan.tasks}
    added = 0
    for item in _checklist_items(admission):
        if item["text"] in existing_titles:
            continue
        source = "default" if item["source"] == "base" else item["source"]
        db.add(TransitionTask(
            hospital_id=plan.hospital_id, plan_id=plan.id,
            role=role_for_item(item["text"]), title=item["text"], source=source,
        ))
        added += 1
    db.flush()
    return added


def discharge_plan(db: Session, plan: TransitionPlan, now: datetime) -> TransitionPlan:
    if plan.status in (PlanStatus.DISCHARGED, PlanStatus.CLOSED):
        raise ValueError("Plan already discharged")
    plan.status = PlanStatus.DISCHARGED
    plan.admission.discharged_at = now
    followup_service.schedule_checkins(db, plan, now=now)
    db.flush()
    return plan


def open_task_summary(plan: TransitionPlan) -> tuple[int, list[str]]:
    open_tasks = [t for t in plan.tasks if t.status == TaskStatus.OPEN]
    roles = sorted({t.role for t in open_tasks})
    return len(open_tasks), roles
```

Note: this imports `followup_service.schedule_checkins`, written in Task 4. To keep this task green on its own, Task 4's service file is created in the same commit *only if needed* — instead, implement `schedule_checkins` now as part of Task 4 below and run Task 3's tests after Task 4 Step 3. Practical order: write both test files, then implement `followup_service.py` (Task 4) and `transition_service.py` together, then run both test files.

- [ ] **Step 4: Run tests** (after Task 4 Step 3 exists): `py -m pytest tests/test_transition_service.py -v` → PASS.

- [ ] **Step 5: Commit** (combined with Task 4's commit — see Task 4 Step 5).

---

### Task 4: Messaging package + follow-up service

**Files:**
- Create: `backend/app/services/messaging/__init__.py`, `base.py`, `simulated.py`, `twilio_whatsapp.py`, `templates.py`
- Create: `backend/app/services/followup_service.py`
- Test: `backend/tests/test_reply_scoring.py`, `backend/tests/test_followup_service.py`

- [ ] **Step 1: Write the failing scoring tests** — create `backend/tests/test_reply_scoring.py`:

```python
"""Table-driven tests for check-in reply scoring — this is clinical logic."""
from __future__ import annotations

import pytest

from app.services.messaging.templates import render_checkin, score_reply


@pytest.mark.parametrize("text,red_flag,meds_missed,opted_out,score", [
    ("I feel fine, took all my meds", False, False, False, 0),
    ("having chest pain since morning", True, False, False, 2),
    ("Severe shortness of breath at night", True, False, False, 2),
    ("i missed my pills two days", False, True, False, 1),
    ("ran out of medication", False, True, False, 1),
    ("chest pain and I missed my meds", True, True, False, 2),
    ("STOP", False, False, True, 0),
    ("stop", False, False, True, 0),
    ("عندي ألم في الصدر", True, False, False, 2),      # Arabic: chest pain
    ("نسيت الدواء اليوم", False, True, False, 1),        # Arabic: forgot meds
    ("توقف", False, False, True, 0),                     # Arabic: stop
    ("", False, False, False, 0),
])
def test_score_reply(text, red_flag, meds_missed, opted_out, score):
    result = score_reply(text)
    assert result["red_flag"] is red_flag
    assert result["meds_missed"] is meds_missed
    assert result["opted_out"] is opted_out
    assert result["concern_score"] == score


def test_render_checkin_en_and_ar():
    en = render_checkin("en", name="Rania", hospital="Rizk Hospital", day=7)
    assert "Rania" in en and "Rizk Hospital" in en and "day 7" in en
    ar = render_checkin("ar", name="رانيا", hospital="مستشفى رزق", day=7)
    assert "رانيا" in ar
    # unknown language falls back to English
    assert render_checkin("fr", name="X", hospital="H", day=2) == render_checkin("en", name="X", hospital="H", day=2)
```

- [ ] **Step 2: Write the failing follow-up service tests** — create `backend/tests/test_followup_service.py`:

```python
"""Scheduling, dispatch, retry, no-response — all with explicit `now` params."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.followup import CheckinStatus, Escalation, FollowUpCheckin
from app.models.hospital import Hospital
from app.services import followup_service, transition_service
from app.services.messaging.base import OutboundMessage, SendError
from tests.test_transition_service import make_admission

NOW = datetime(2026, 7, 2, 9, 0, tzinfo=timezone.utc)


class FakeProvider:
    name = "fake"

    def __init__(self, fail: bool = False):
        self.fail = fail
        self.sent: list[OutboundMessage] = []

    def send(self, message: OutboundMessage) -> str:
        if self.fail:
            raise SendError("boom")
        self.sent.append(message)
        return f"fake-{len(self.sent)}"


def make_discharged_plan(db: Session, hospital: Hospital, phone="+96170000001"):
    adm = make_admission(db, hospital, phone=phone)
    plan = transition_service.create_plan(db, adm, hospital.id)
    transition_service.discharge_plan(db, plan, now=NOW)
    db.commit()
    return plan


def test_schedule_checkins_offsets(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    checkins = db.query(FollowUpCheckin).filter_by(plan_id=plan.id).order_by(
        FollowUpCheckin.day_offset).all()
    assert [c.day_offset for c in checkins] == [2, 7, 14, 30]
    assert checkins[0].scheduled_at.replace(tzinfo=timezone.utc) == NOW + timedelta(days=2)
    assert all(c.status == CheckinStatus.SCHEDULED for c in checkins)


def test_schedule_checkins_no_phone_is_manual(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital, phone=None)
    checkins = db.query(FollowUpCheckin).filter_by(plan_id=plan.id).all()
    assert all(c.status == CheckinStatus.MANUAL for c in checkins)


def test_dispatch_sends_due_checkins(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    provider = FakeProvider()
    later = NOW + timedelta(days=2, minutes=5)
    sent = followup_service.dispatch_due_checkins(db, provider, now=later)
    db.commit()
    assert sent == 1
    assert len(provider.sent) == 1
    c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).one()
    assert c.status == CheckinStatus.SENT
    assert c.sent_body and "day 2" in c.sent_body


def test_dispatch_failure_retries_then_escalates(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    provider = FakeProvider(fail=True)
    t = NOW + timedelta(days=2, minutes=5)
    for i in range(3):
        followup_service.dispatch_due_checkins(db, provider, now=t + timedelta(minutes=31 * i))
    db.commit()
    c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).one()
    assert c.status == CheckinStatus.SEND_FAILED
    assert c.attempts == 3
    esc = db.query(Escalation).filter_by(trigger="send_failed").one()
    assert esc.patient_id == plan.admission.patient_id


def test_dispatch_respects_retry_window(db: Session, hospital: Hospital):
    make_discharged_plan(db, hospital)
    provider = FakeProvider(fail=True)
    t = NOW + timedelta(days=2, minutes=5)
    followup_service.dispatch_due_checkins(db, provider, now=t)
    # 1 minute later: inside the 30-min retry window, must not attempt again
    followup_service.dispatch_due_checkins(db, provider, now=t + timedelta(minutes=1))
    db.commit()
    c = db.query(FollowUpCheckin).filter_by(day_offset=2).one()
    assert c.attempts == 1


def test_record_response_scores_and_escalates(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    provider = FakeProvider()
    followup_service.dispatch_due_checkins(db, provider, now=NOW + timedelta(days=2, minutes=5))
    c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).one()
    resp = followup_service.record_response(db, c, "severe chest pain", provider_message_id="m1")
    db.commit()
    assert resp.red_flag is True
    assert c.status == CheckinStatus.RESPONDED
    esc = db.query(Escalation).filter_by(trigger="red_flag").one()
    assert esc.priority.value == "high"


def test_record_response_idempotent(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    provider = FakeProvider()
    followup_service.dispatch_due_checkins(db, provider, now=NOW + timedelta(days=2, minutes=5))
    c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).one()
    r1 = followup_service.record_response(db, c, "fine", provider_message_id="dup")
    r2 = followup_service.record_response(db, c, "fine", provider_message_id="dup")
    db.commit()
    assert r1.id == r2.id


def test_stop_opts_out_and_converts_remaining(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    provider = FakeProvider()
    followup_service.dispatch_due_checkins(db, provider, now=NOW + timedelta(days=2, minutes=5))
    c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).one()
    followup_service.record_response(db, c, "STOP", provider_message_id="m-stop")
    db.commit()
    remaining = db.query(FollowUpCheckin).filter(
        FollowUpCheckin.plan_id == plan.id, FollowUpCheckin.day_offset > 2).all()
    assert all(r.status == CheckinStatus.MANUAL for r in remaining)
    assert plan.admission.patient.messaging_opted_out is True
    assert db.query(Escalation).filter_by(trigger="opted_out").count() == 1


def test_two_consecutive_no_responses_escalate(db: Session, hospital: Hospital):
    plan = make_discharged_plan(db, hospital)
    provider = FakeProvider()
    # send day-2 and day-7, answer neither
    followup_service.dispatch_due_checkins(db, provider, now=NOW + timedelta(days=7, minutes=5))
    # both sent; 48h later they are stale
    followup_service.mark_no_responses(db, now=NOW + timedelta(days=9, hours=1))
    db.commit()
    stale = db.query(FollowUpCheckin).filter_by(status=CheckinStatus.NO_RESPONSE).count()
    assert stale == 2
    assert db.query(Escalation).filter_by(trigger="no_response").count() == 1
```

- [ ] **Step 3: Run to verify failure**

Run: `py -m pytest tests/test_reply_scoring.py tests/test_followup_service.py -v`
Expected: FAIL — missing modules.

- [ ] **Step 4: Implement the messaging package**

Create `backend/app/services/messaging/base.py`:

```python
"""Messaging provider interface."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SendError(Exception):
    """Raised when a provider fails to deliver a message."""


@dataclass
class OutboundMessage:
    to: str
    body: str


class MessagingProvider(Protocol):
    name: str

    def send(self, message: OutboundMessage) -> str:
        """Send and return the provider's message id. Raises SendError."""
        ...
```

Create `backend/app/services/messaging/templates.py`:

```python
"""Bilingual check-in templates + deterministic reply scoring.

Templates live in code (not the DB) in v1 — nothing edits them at runtime.
Scoring scans ALL keyword languages regardless of the patient's preferred
language: patients reply in whatever language they like.
"""
from __future__ import annotations

CHECKIN_TEMPLATES: dict[str, str] = {
    "en": (
        "Hello {name}, this is {hospital} checking in — day {day} after your discharge.\n"
        "Please reply to these questions:\n"
        "1. Any chest pain, severe shortness of breath, or bleeding?\n"
        "2. Have you taken all your medications as prescribed?\n"
        "3. Any other symptoms or concerns?\n"
        "Reply STOP to end these messages."
    ),
    "ar": (
        "مرحباً {name}، معك {hospital} للاطمئنان عليك — اليوم {day} بعد الخروج.\n"
        "الرجاء الإجابة على الأسئلة التالية:\n"
        "١. هل تعاني من ألم في الصدر أو ضيق تنفس شديد أو نزيف؟\n"
        "٢. هل تناولت جميع أدويتك كما وُصفت؟\n"
        "٣. هل لديك أي أعراض أو مخاوف أخرى؟\n"
        "أرسل STOP أو توقف لإيقاف الرسائل."
    ),
}

RED_FLAG_KEYWORDS: list[str] = [
    "chest pain", "shortness of breath", "short of breath", "bleeding",
    "fainted", "fainting", "passed out", "severe pain",
    "ألم في الصدر", "ضيق تنفس", "نزيف", "إغماء", "ألم شديد",
]

MEDS_MISSED_KEYWORDS: list[str] = [
    "missed my", "missed the", "didn't take", "did not take", "no meds",
    "ran out", "stopped taking", "missed my pills",
    "نسيت الدواء", "لم آخذ", "خلص الدواء", "توقفت عن",
]

OPT_OUT_KEYWORDS: list[str] = ["stop", "توقف"]


def render_checkin(language: str, *, name: str, hospital: str, day: int) -> str:
    template = CHECKIN_TEMPLATES.get(language, CHECKIN_TEMPLATES["en"])
    return template.format(name=name, hospital=hospital, day=day)


def score_reply(text: str) -> dict:
    lowered = text.lower().strip()
    opted_out = any(lowered == k or lowered.startswith(k + " ") for k in OPT_OUT_KEYWORDS)
    red_flag = any(k in lowered for k in RED_FLAG_KEYWORDS)
    meds_missed = any(k in lowered for k in MEDS_MISSED_KEYWORDS)
    concern_score = 2 if red_flag else (1 if meds_missed else 0)
    return {
        "red_flag": red_flag,
        "meds_missed": meds_missed,
        "opted_out": opted_out,
        "concern_score": concern_score,
    }
```

Note the "missed" keyword list uses phrases (`"missed my"`) rather than the bare word so "I missed my grandkids" doesn't false-positive less than necessary; the table test defines the contract — if a test case demands looser matching, loosen the keyword, not the test.

Create `backend/app/services/messaging/simulated.py`:

```python
"""In-memory provider — used for demos and local dev. Outbound bodies are
persisted on the checkin row (sent_body), so the UI reads them from the DB."""
from __future__ import annotations

import uuid

from app.services.messaging.base import OutboundMessage


class SimulatedProvider:
    name = "simulated"

    def send(self, message: OutboundMessage) -> str:  # noqa: ARG002 - body persisted by caller
        return f"sim-{uuid.uuid4()}"
```

Create `backend/app/services/messaging/twilio_whatsapp.py`:

```python
"""Twilio WhatsApp provider via plain REST (no SDK dependency)."""
from __future__ import annotations

import base64
import hashlib
import hmac

import httpx

from app.core.config import settings
from app.services.messaging.base import OutboundMessage, SendError

TWILIO_API = "https://api.twilio.com/2010-04-01"


class TwilioWhatsAppProvider:
    name = "twilio"

    def send(self, message: OutboundMessage) -> str:
        url = f"{TWILIO_API}/Accounts/{settings.twilio_account_sid}/Messages.json"
        try:
            resp = httpx.post(
                url,
                auth=(settings.twilio_account_sid, settings.twilio_auth_token),
                data={
                    "From": f"whatsapp:{settings.twilio_whatsapp_from}",
                    "To": f"whatsapp:{message.to}",
                    "Body": message.body,
                },
                timeout=15,
            )
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise SendError(str(exc)) from exc
        return resp.json()["sid"]


def validate_twilio_signature(url: str, params: dict[str, str], signature: str, auth_token: str) -> bool:
    """Twilio request validation: HMAC-SHA1 over url + concatenated sorted
    form params, base64-encoded, compared to X-Twilio-Signature."""
    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    digest = hmac.new(auth_token.encode(), payload.encode(), hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)
```

Create `backend/app/services/messaging/__init__.py`:

```python
"""Provider factory — selected by MESSAGING_PROVIDER env var."""
from __future__ import annotations

from functools import lru_cache

from app.core.config import settings
from app.services.messaging.base import MessagingProvider, OutboundMessage, SendError  # noqa: F401
from app.services.messaging.simulated import SimulatedProvider
from app.services.messaging.twilio_whatsapp import TwilioWhatsAppProvider


@lru_cache
def get_provider() -> MessagingProvider:
    if settings.messaging_provider == "twilio":
        return TwilioWhatsAppProvider()
    return SimulatedProvider()
```

- [ ] **Step 5: Implement the follow-up service**

Create `backend/app/services/followup_service.py`:

```python
"""Post-discharge follow-up engine: scheduling, dispatch, response scoring,
no-response detection. Governing rule: never silently drop a patient.

All time-dependent functions take an explicit `now` so tests never freeze
clocks, and all datetime comparisons happen in SQL (SQLite returns naive
datetimes; comparing them to aware datetimes in Python raises)."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.followup import (
    CheckinResponse, CheckinStatus, Escalation, EscalationPriority, FollowUpCheckin,
)
from app.models.transition import TransitionPlan
from app.services.messaging.base import MessagingProvider, OutboundMessage, SendError
from app.services.messaging.templates import render_checkin, score_reply


def schedule_checkins(db: Session, plan: TransitionPlan, now: datetime) -> list[FollowUpCheckin]:
    patient = plan.admission.patient
    reachable = bool(patient.phone_number) and not patient.messaging_opted_out
    status = CheckinStatus.SCHEDULED if reachable else CheckinStatus.MANUAL
    checkins = [
        FollowUpCheckin(
            hospital_id=plan.hospital_id, plan_id=plan.id, patient_id=patient.id,
            day_offset=offset, scheduled_at=now + timedelta(days=offset),
            status=status, language=patient.preferred_language,
        )
        for offset in settings.checkin_day_offsets_list
    ]
    db.add_all(checkins)
    db.flush()
    return checkins


def find_due_checkins(db: Session, now: datetime) -> list[FollowUpCheckin]:
    retry_cutoff = now - timedelta(minutes=settings.checkin_retry_minutes)
    q = db.query(FollowUpCheckin).filter(
        FollowUpCheckin.status == CheckinStatus.SCHEDULED,
        FollowUpCheckin.scheduled_at <= now,
        (FollowUpCheckin.last_attempt_at.is_(None))
        | (FollowUpCheckin.last_attempt_at <= retry_cutoff),
    )
    return q.all()


def dispatch_due_checkins(db: Session, provider: MessagingProvider, now: datetime) -> int:
    sent = 0
    for checkin in find_due_checkins(db, now):
        patient = checkin.plan.admission.patient
        hospital = db.get(Hospital, checkin.hospital_id)
        body = render_checkin(
            checkin.language,
            name=patient.first_name,
            hospital=hospital.name if hospital else "your hospital",
            day=checkin.day_offset,
        )
        checkin.attempts += 1
        checkin.last_attempt_at = now
        try:
            provider.send(OutboundMessage(to=patient.phone_number or "", body=body))
        except SendError:
            if checkin.attempts >= settings.checkin_max_attempts:
                checkin.status = CheckinStatus.SEND_FAILED
                db.add(Escalation(
                    hospital_id=checkin.hospital_id, patient_id=patient.id,
                    checkin_id=checkin.id, trigger="send_failed",
                    detail=f"Day-{checkin.day_offset} check-in could not be delivered "
                           f"after {checkin.attempts} attempts — call the patient manually.",
                    priority=EscalationPriority.MEDIUM,
                ))
            continue
        checkin.status = CheckinStatus.SENT
        checkin.sent_at = now
        checkin.sent_body = body
        sent += 1
    db.flush()
    return sent


def record_response(
    db: Session, checkin: FollowUpCheckin, raw_text: str, provider_message_id: str | None,
) -> CheckinResponse:
    if provider_message_id:
        existing = db.query(CheckinResponse).filter(
            CheckinResponse.provider_message_id == provider_message_id
        ).first()
        if existing is not None:
            return existing

    scores = score_reply(raw_text)
    response = CheckinResponse(
        checkin_id=checkin.id, provider_message_id=provider_message_id,
        raw_text=raw_text[:2000], **scores,
    )
    db.add(response)
    checkin.status = CheckinStatus.RESPONDED
    patient = checkin.plan.admission.patient

    if scores["opted_out"]:
        patient.messaging_opted_out = True
        remaining = db.query(FollowUpCheckin).filter(
            FollowUpCheckin.plan_id == checkin.plan_id,
            FollowUpCheckin.status == CheckinStatus.SCHEDULED,
        ).all()
        for r in remaining:
            r.status = CheckinStatus.MANUAL
        db.add(Escalation(
            hospital_id=checkin.hospital_id, patient_id=patient.id, checkin_id=checkin.id,
            trigger="opted_out",
            detail="Patient opted out of messages — switch to phone-call follow-up.",
            priority=EscalationPriority.LOW,
        ))
    elif scores["red_flag"]:
        db.add(Escalation(
            hospital_id=checkin.hospital_id, patient_id=patient.id, checkin_id=checkin.id,
            trigger="red_flag",
            detail=f"Red-flag symptoms reported on day-{checkin.day_offset} check-in: "
                   f"\"{raw_text[:200]}\"",
            priority=EscalationPriority.HIGH,
        ))
    elif scores["meds_missed"]:
        db.add(Escalation(
            hospital_id=checkin.hospital_id, patient_id=patient.id, checkin_id=checkin.id,
            trigger="meds_missed",
            detail=f"Medication non-adherence reported on day-{checkin.day_offset} "
                   f"check-in: \"{raw_text[:200]}\"",
            priority=EscalationPriority.MEDIUM,
        ))
    db.flush()
    return response


def mark_no_responses(db: Session, now: datetime) -> int:
    cutoff = now - timedelta(hours=settings.checkin_no_response_hours)
    stale = db.query(FollowUpCheckin).filter(
        FollowUpCheckin.status == CheckinStatus.SENT,
        FollowUpCheckin.sent_at <= cutoff,
    ).all()
    escalated_plans: set = set()
    for checkin in stale:
        checkin.status = CheckinStatus.NO_RESPONSE
    for checkin in stale:
        if checkin.plan_id in escalated_plans:
            continue
        prior = db.query(FollowUpCheckin).filter(
            FollowUpCheckin.plan_id == checkin.plan_id,
            FollowUpCheckin.day_offset < checkin.day_offset,
            FollowUpCheckin.status == CheckinStatus.NO_RESPONSE,
        ).count()
        if prior >= 1:
            db.add(Escalation(
                hospital_id=checkin.hospital_id, patient_id=checkin.patient_id,
                checkin_id=checkin.id, trigger="no_response",
                detail="Two consecutive check-ins with no reply — patient may be "
                       "unreachable; call to verify.",
                priority=EscalationPriority.MEDIUM,
            ))
            escalated_plans.add(checkin.plan_id)
    db.flush()
    return len(stale)


def run_cycle(db: Session, provider: MessagingProvider, now: datetime) -> None:
    """One scheduler tick: dispatch due check-ins, then flag stale ones."""
    dispatch_due_checkins(db, provider, now)
    mark_no_responses(db, now)
    db.commit()
```

Add `from app.models.hospital import Hospital` to the imports of `followup_service.py` (used by the hospital-name lookup in `dispatch_due_checkins`).

- [ ] **Step 6: Run all three test files**

Run: `py -m pytest tests/test_reply_scoring.py tests/test_followup_service.py tests/test_transition_service.py -v`
Expected: PASS (Task 3's tests pass now that `followup_service` exists).

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/messaging backend/app/services/followup_service.py backend/app/services/transition_service.py backend/tests/test_reply_scoring.py backend/tests/test_followup_service.py backend/tests/test_transition_service.py
git commit -m "feat(followup): messaging providers, bilingual templates, scoring, scheduling engine"
```

---

### Task 5: Schemas + `/transitions` API (plans, tasks, board, discharge)

**Files:**
- Create: `backend/app/schemas/transition.py`
- Create: `backend/app/api/v1/transitions.py`
- Modify: `backend/app/api/v1/__init__.py`
- Test: `backend/tests/test_transitions_api.py` (extend)

- [ ] **Step 1: Write the failing tests** — append to `backend/tests/test_transitions_api.py`:

```python
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.hospital import Hospital
from app.models.user import User
from tests.test_transition_service import make_admission


def _mk_plan(auth_client: TestClient, admission_id: str):
    return auth_client.post("/api/v1/transitions/plans", json={"admission_id": admission_id})


def test_create_plan_and_list_tasks(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    auth_client.set_user(physician)
    adm = make_admission(db, hospital)
    resp = _mk_plan(auth_client, str(adm.id))
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "planning"
    assert len(body["tasks"]) >= 5
    assert {"role", "title", "status", "source"} <= set(body["tasks"][0])


def test_create_plan_duplicate_409(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    auth_client.set_user(physician)
    adm = make_admission(db, hospital)
    assert _mk_plan(auth_client, str(adm.id)).status_code == 201
    assert _mk_plan(auth_client, str(adm.id)).status_code == 409


def test_tenancy_cross_hospital_404(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    from app.models.hospital import Department
    other = Hospital(name="Other", slug="other")
    db.add(other)
    db.flush()
    db.add(Department(hospital_id=other.id, name="Med", code="MED"))
    db.commit()
    adm = make_admission(db, other)  # belongs to the other hospital
    auth_client.set_user(physician)  # physician is in `hospital`
    assert _mk_plan(auth_client, str(adm.id)).status_code == 404


def test_complete_task(auth_client: TestClient, db: Session, hospital: Hospital, nurse: User):
    auth_client.set_user(nurse)
    adm = make_admission(db, hospital)
    plan = _mk_plan(auth_client, str(adm.id)).json()
    task_id = plan["tasks"][0]["id"]
    resp = auth_client.patch(f"/api/v1/transitions/tasks/{task_id}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_board_lists_active_admissions(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    auth_client.set_user(physician)
    adm = make_admission(db, hospital)
    _mk_plan(auth_client, str(adm.id))
    resp = auth_client.get("/api/v1/transitions/board")
    assert resp.status_code == 200
    rows = resp.json()["rows"]
    row = next(r for r in rows if r["admission_id"] == str(adm.id))
    assert row["plan_status"] == "planning"
    assert row["open_tasks"] >= 5
    assert "case_manager" in row["open_task_roles"]


def test_discharge_endpoint_schedules_checkins(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    from app.models.followup import FollowUpCheckin
    auth_client.set_user(physician)
    adm = make_admission(db, hospital)
    plan = _mk_plan(auth_client, str(adm.id)).json()
    resp = auth_client.post(f"/api/v1/transitions/plans/{plan['id']}/discharge")
    assert resp.status_code == 200
    assert resp.json()["status"] == "discharged"
    assert db.query(FollowUpCheckin).count() == 4


def test_my_tasks(auth_client: TestClient, db: Session, hospital: Hospital, nurse: User):
    auth_client.set_user(nurse)
    adm = make_admission(db, hospital)
    _mk_plan(auth_client, str(adm.id))
    resp = auth_client.get("/api/v1/transitions/tasks/mine")
    assert resp.status_code == 200
    tasks = resp.json()
    assert all(t["role"] == "nurse" and t["status"] == "open" for t in tasks)
    assert len(tasks) >= 1
```

Also add `patch` support check: the existing `api` helper in tests uses `auth_client.patch` — FastAPI TestClient supports it natively; nothing to add.

- [ ] **Step 2: Run to verify failure**

Run: `py -m pytest tests/test_transitions_api.py -v`
Expected: FAIL — 404s (routes don't exist).

- [ ] **Step 3: Create schemas** — `backend/app/schemas/transition.py`:

```python
"""Transition plan/task/board Pydantic schemas."""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class PlanCreate(BaseModel):
    admission_id: UUID
    target_discharge_date: date | None = None


class TaskRead(BaseModel):
    id: UUID
    role: str
    title: str
    status: str
    due_date: date | None
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskStatusUpdate(BaseModel):
    status: str  # open | done | skipped


class PlanRead(BaseModel):
    id: UUID
    admission_id: UUID
    status: str
    target_discharge_date: date | None
    created_at: datetime
    tasks: list[TaskRead]

    model_config = {"from_attributes": True}


class BoardRow(BaseModel):
    patient_id: UUID
    admission_id: UUID
    first_name: str
    last_name: str
    mrn: str
    department: str
    probability: float | None
    risk_tier: str | None
    plan_id: UUID | None
    plan_status: str | None
    target_discharge_date: date | None
    open_tasks: int
    open_task_roles: list[str]


class BoardResponse(BaseModel):
    rows: list[BoardRow]
```

- [ ] **Step 4: Create the route file** — `backend/app/api/v1/transitions.py`:

```python
"""Transition plans, tasks, discharge board."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_any_clinical_role, require_role
from app.db.session import get_db
from app.models.hospital import Department
from app.models.patient import Admission, Patient
from app.models.transition import TaskStatus, TransitionPlan, TransitionTask
from app.models.user import RoleName, User
from app.schemas.transition import (
    BoardResponse, BoardRow, PlanCreate, PlanRead, TaskRead, TaskStatusUpdate,
)
from app.services import transition_service

router = APIRouter(prefix="/transitions", tags=["transitions"])


def _get_plan_scoped(db: Session, plan_id: UUID, current: User) -> TransitionPlan:
    plan = db.get(TransitionPlan, plan_id)
    if plan is None or plan.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


@router.post("/plans", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(
    body: PlanCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(
        RoleName.PHYSICIAN, RoleName.ADMIN, RoleName.CASE_MANAGER)),
) -> PlanRead:
    adm = db.get(Admission, body.admission_id)
    if adm is None or adm.patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Admission not found")
    try:
        plan = transition_service.create_plan(db, adm, current.hospital_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if body.target_discharge_date:
        plan.target_discharge_date = body.target_discharge_date
    db.commit()
    db.refresh(plan)
    return PlanRead.model_validate(plan)


@router.get("/plans/by-patient/{patient_id}", response_model=PlanRead)
def latest_plan_for_patient(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> PlanRead:
    patient = db.get(Patient, patient_id)
    if patient is None or patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    plan = (
        db.query(TransitionPlan)
        .join(Admission, TransitionPlan.admission_id == Admission.id)
        .filter(Admission.patient_id == patient_id)
        .order_by(TransitionPlan.created_at.desc())
        .first()
    )
    if plan is None:
        raise HTTPException(status_code=404, detail="No transition plan for patient")
    return PlanRead.model_validate(plan)


@router.post("/plans/{plan_id}/discharge", response_model=PlanRead)
def discharge(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(RoleName.PHYSICIAN, RoleName.ADMIN)),
) -> PlanRead:
    plan = _get_plan_scoped(db, plan_id, current)
    try:
        transition_service.discharge_plan(db, plan, now=datetime.now(timezone.utc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.commit()
    db.refresh(plan)
    return PlanRead.model_validate(plan)


@router.post("/plans/{plan_id}/refresh-tasks", response_model=PlanRead)
def refresh_tasks(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> PlanRead:
    plan = _get_plan_scoped(db, plan_id, current)
    transition_service.refresh_risk_tasks(db, plan)
    db.commit()
    db.refresh(plan)
    return PlanRead.model_validate(plan)


@router.patch("/tasks/{task_id}", response_model=TaskRead)
def update_task(
    task_id: UUID,
    body: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> TaskRead:
    task = db.get(TransitionTask, task_id)
    if task is None or task.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        task.status = TaskStatus(body.status)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid status") from exc
    db.commit()
    db.refresh(task)
    return TaskRead.model_validate(task)


@router.get("/tasks/mine", response_model=list[TaskRead])
def my_tasks(
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> list[TaskRead]:
    tasks = (
        db.query(TransitionTask)
        .filter(
            TransitionTask.hospital_id == current.hospital_id,
            TransitionTask.role == current.role.name.value,
            TransitionTask.status == TaskStatus.OPEN,
        )
        .order_by(TransitionTask.created_at)
        .all()
    )
    return [TaskRead.model_validate(t) for t in tasks]


@router.get("/board", response_model=BoardResponse)
def board(
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> BoardResponse:
    admissions = (
        db.query(Admission)
        .join(Patient, Admission.patient_id == Patient.id)
        .filter(
            Patient.hospital_id == current.hospital_id,
            Admission.discharged_at.is_(None),
        )
        .all()
    )
    rows: list[BoardRow] = []
    for adm in admissions:
        pred = adm.predictions[0] if adm.predictions else None
        plan = db.query(TransitionPlan).filter(
            TransitionPlan.admission_id == adm.id).first()
        open_count, roles = (0, [])
        if plan is not None:
            open_count, roles = transition_service.open_task_summary(plan)
        dept = db.get(Department, adm.department_id)
        rows.append(BoardRow(
            patient_id=adm.patient_id, admission_id=adm.id,
            first_name=adm.patient.first_name, last_name=adm.patient.last_name,
            mrn=adm.patient.mrn, department=dept.name if dept else "—",
            probability=pred.probability if pred else None,
            risk_tier=pred.risk_tier if pred else None,
            plan_id=plan.id if plan else None,
            plan_status=plan.status.value if plan else None,
            target_discharge_date=plan.target_discharge_date if plan else None,
            open_tasks=open_count, open_task_roles=roles,
        ))
    rows.sort(key=lambda r: (r.probability or 0), reverse=True)
    return BoardResponse(rows=rows)
```

In `backend/app/api/v1/__init__.py`, add `transitions` to the import list and `api_router.include_router(transitions.router)` after `admin`.

- [ ] **Step 5: Run tests**

Run: `py -m pytest tests/test_transitions_api.py -v` → PASS. Then full suite.

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/transition.py backend/app/api/v1/transitions.py backend/app/api/v1/__init__.py backend/tests/test_transitions_api.py
git commit -m "feat(transitions): plans/tasks/board/discharge API"
```

---

### Task 6: Follow-up schemas + `/checkins` and `/escalations` APIs

**Files:**
- Create: `backend/app/schemas/followup.py`
- Create: `backend/app/api/v1/checkins.py`
- Create: `backend/app/api/v1/escalations.py`
- Modify: `backend/app/api/v1/__init__.py`
- Test: `backend/tests/test_checkins_api.py`, `backend/tests/test_escalations_api.py`

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_checkins_api.py`:

```python
from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.hospital import Hospital
from app.models.user import User
from app.services import followup_service
from tests.test_followup_service import NOW, FakeProvider, make_discharged_plan


def test_checkin_timeline_for_patient(auth_client: TestClient, db: Session, hospital: Hospital, nurse: User):
    plan = make_discharged_plan(db, hospital)
    auth_client.set_user(nurse)
    resp = auth_client.get(f"/api/v1/checkins?patient_id={plan.admission.patient_id}")
    assert resp.status_code == 200
    items = resp.json()
    assert [i["day_offset"] for i in items] == [2, 7, 14, 30]
    assert items[0]["responses"] == []


def test_simulate_reply_records_response(auth_client: TestClient, db: Session, hospital: Hospital, nurse: User):
    plan = make_discharged_plan(db, hospital)
    followup_service.dispatch_due_checkins(db, FakeProvider(), now=NOW + timedelta(days=2, minutes=5))
    db.commit()
    auth_client.set_user(nurse)
    timeline = auth_client.get(f"/api/v1/checkins?patient_id={plan.admission.patient_id}").json()
    sent = next(i for i in timeline if i["status"] == "sent")
    resp = auth_client.post(f"/api/v1/checkins/{sent['id']}/simulate-reply", json={"text": "chest pain"})
    assert resp.status_code == 200
    assert resp.json()["red_flag"] is True
```

Create `backend/tests/test_escalations_api.py`:

```python
from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.hospital import Hospital
from app.models.user import User
from app.services import followup_service
from tests.test_followup_service import NOW, FakeProvider, make_discharged_plan


def _escalate(db, hospital) -> None:
    plan = make_discharged_plan(db, hospital)
    followup_service.dispatch_due_checkins(db, FakeProvider(), now=NOW + timedelta(days=2, minutes=5))
    from app.models.followup import FollowUpCheckin
    c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).one()
    followup_service.record_response(db, c, "severe chest pain", provider_message_id="e1")
    db.commit()


def test_queue_lists_open_escalations(auth_client: TestClient, db: Session, hospital: Hospital, nurse: User):
    _escalate(db, hospital)
    auth_client.set_user(nurse)
    resp = auth_client.get("/api/v1/escalations?status=open")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["trigger"] == "red_flag"
    assert items[0]["priority"] == "high"
    assert items[0]["patient_name"]


def test_resolve_escalation_requires_case_manager(auth_client: TestClient, db: Session, hospital: Hospital, nurse: User):
    _escalate(db, hospital)
    auth_client.set_user(nurse)
    esc_id = auth_client.get("/api/v1/escalations?status=open").json()[0]["id"]
    resp = auth_client.patch(f"/api/v1/escalations/{esc_id}", json={
        "status": "resolved", "resolution_notes": "called patient"})
    assert resp.status_code == 403  # nurses can view, not resolve


def test_resolve_escalation_as_case_manager(auth_client: TestClient, db: Session, hospital: Hospital):
    from app.models.user import RoleName
    from tests.conftest import _make_user
    cm = _make_user(db, hospital, RoleName.CASE_MANAGER)
    _escalate(db, hospital)
    auth_client.set_user(cm)
    esc_id = auth_client.get("/api/v1/escalations?status=open").json()[0]["id"]
    resp = auth_client.patch(f"/api/v1/escalations/{esc_id}", json={
        "status": "resolved", "resolution_notes": "called patient, meds adjusted"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "resolved"
    assert auth_client.get("/api/v1/escalations?status=open").json() == []
```

- [ ] **Step 2: Run to verify failure** — `py -m pytest tests/test_checkins_api.py tests/test_escalations_api.py -v` → FAIL (404s).

- [ ] **Step 3: Create schemas** — `backend/app/schemas/followup.py`:

```python
"""Check-in, escalation, outcomes Pydantic schemas."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class ResponseRead(BaseModel):
    id: UUID
    raw_text: str
    red_flag: bool
    meds_missed: bool
    opted_out: bool
    concern_score: int
    created_at: datetime

    model_config = {"from_attributes": True}


class CheckinRead(BaseModel):
    id: UUID
    patient_id: UUID
    day_offset: int
    scheduled_at: datetime
    status: str
    sent_at: datetime | None
    sent_body: str | None
    language: str
    responses: list[ResponseRead]

    model_config = {"from_attributes": True}


class SimulateReply(BaseModel):
    text: str


class EscalationRead(BaseModel):
    id: UUID
    patient_id: UUID | None
    patient_name: str | None
    trigger: str
    detail: str
    priority: str
    status: str
    resolution_notes: str | None
    created_at: datetime


class EscalationUpdate(BaseModel):
    status: str  # open | in_progress | resolved
    resolution_notes: str | None = None


class ReadmissionCreate(BaseModel):
    admission_id: UUID


class ReadmissionRead(BaseModel):
    id: UUID
    patient_id: UUID
    prior_admission_id: UUID
    readmission_admission_id: UUID
    days_since_discharge: int

    model_config = {"from_attributes": True}


class OutcomeMetrics(BaseModel):
    discharges_tracked: int
    readmissions_30d: int
    readmission_rate: float | None
    checkin_response_rate: float | None
    escalations_open: int
    escalations_resolved: int
    monthly: list[dict]  # [{"month": "2026-07", "discharges": n, "readmissions": n}]
```

- [ ] **Step 4: Create routes**

`backend/app/api/v1/checkins.py`:

```python
"""Check-in timeline + demo-mode simulated replies."""
from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_any_clinical_role
from app.core.config import settings
from app.db.session import get_db
from app.models.followup import CheckinStatus, FollowUpCheckin
from app.models.patient import Patient
from app.models.user import User
from app.schemas.followup import CheckinRead, ResponseRead, SimulateReply
from app.services import followup_service

router = APIRouter(prefix="/checkins", tags=["checkins"])


@router.get("", response_model=list[CheckinRead])
def timeline(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> list[CheckinRead]:
    patient = db.get(Patient, patient_id)
    if patient is None or patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Patient not found")
    checkins = (
        db.query(FollowUpCheckin)
        .filter(FollowUpCheckin.patient_id == patient_id)
        .order_by(FollowUpCheckin.day_offset)
        .all()
    )
    return [CheckinRead.model_validate(c) for c in checkins]


@router.post("/{checkin_id}/simulate-reply", response_model=ResponseRead)
def simulate_reply(
    checkin_id: UUID,
    body: SimulateReply,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> ResponseRead:
    if settings.messaging_provider != "simulated":
        raise HTTPException(status_code=403, detail="Only available in demo mode")
    checkin = db.get(FollowUpCheckin, checkin_id)
    if checkin is None or checkin.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Check-in not found")
    if checkin.status != CheckinStatus.SENT:
        raise HTTPException(status_code=409, detail="Check-in has not been sent")
    response = followup_service.record_response(
        db, checkin, body.text, provider_message_id=f"sim-reply-{uuid4()}")
    db.commit()
    db.refresh(response)
    return ResponseRead.model_validate(response)
```

`backend/app/api/v1/escalations.py`:

```python
"""Escalation queue for case managers."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import require_any_clinical_role, require_role
from app.db.session import get_db
from app.models.followup import Escalation, EscalationPriority, EscalationStatus
from app.models.patient import Patient
from app.models.user import RoleName, User
from app.schemas.followup import EscalationRead, EscalationUpdate

router = APIRouter(prefix="/escalations", tags=["escalations"])

_PRIORITY_ORDER = {EscalationPriority.HIGH: 0, EscalationPriority.MEDIUM: 1, EscalationPriority.LOW: 2}


def _to_read(db: Session, e: Escalation) -> EscalationRead:
    name = None
    if e.patient_id:
        p = db.get(Patient, e.patient_id)
        if p:
            name = f"{p.last_name}, {p.first_name}"
    return EscalationRead(
        id=e.id, patient_id=e.patient_id, patient_name=name, trigger=e.trigger,
        detail=e.detail, priority=e.priority.value, status=e.status.value,
        resolution_notes=e.resolution_notes, created_at=e.created_at,
    )


@router.get("", response_model=list[EscalationRead])
def list_escalations(
    status: str | None = None,
    patient_id: UUID | None = None,
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> list[EscalationRead]:
    q = db.query(Escalation).filter(Escalation.hospital_id == current.hospital_id)
    if status:
        q = q.filter(Escalation.status == EscalationStatus(status))
    if patient_id:
        q = q.filter(Escalation.patient_id == patient_id)
    items = q.all()
    items.sort(key=lambda e: (_PRIORITY_ORDER[e.priority], e.created_at))
    return [_to_read(db, e) for e in items]


@router.patch("/{escalation_id}", response_model=EscalationRead)
def update_escalation(
    escalation_id: UUID,
    body: EscalationUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(RoleName.CASE_MANAGER, RoleName.ADMIN)),
) -> EscalationRead:
    e = db.get(Escalation, escalation_id)
    if e is None or e.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Escalation not found")
    try:
        e.status = EscalationStatus(body.status)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid status") from exc
    if body.resolution_notes is not None:
        e.resolution_notes = body.resolution_notes
    if e.status == EscalationStatus.RESOLVED:
        e.resolved_at = datetime.now(timezone.utc)
        e.assigned_user_id = current.id
    db.commit()
    db.refresh(e)
    return _to_read(db, e)
```

Register both in `backend/app/api/v1/__init__.py` (import + `include_router`).

- [ ] **Step 5: Run tests** — `py -m pytest tests/test_checkins_api.py tests/test_escalations_api.py -v` → PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/followup.py backend/app/api/v1/checkins.py backend/app/api/v1/escalations.py backend/app/api/v1/__init__.py backend/tests/test_checkins_api.py backend/tests/test_escalations_api.py
git commit -m "feat(followup): checkin timeline, simulate-reply, escalation queue API"
```

---

### Task 7: Outcomes API + Twilio webhook

**Files:**
- Create: `backend/app/api/v1/outcomes.py`
- Create: `backend/app/api/v1/webhooks.py`
- Modify: `backend/app/api/v1/__init__.py`
- Test: `backend/tests/test_outcomes_api.py`, `backend/tests/test_webhooks.py`

- [ ] **Step 1: Write failing outcome tests** — create `backend/tests/test_outcomes_api.py`:

```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.hospital import Hospital
from app.models.patient import Admission
from app.models.user import User
from tests.test_followup_service import NOW, make_discharged_plan


def _readmit(db: Session, plan, days: int) -> Admission:
    adm = plan.admission
    new = Admission(
        patient_id=adm.patient_id, department_id=adm.department_id,
        admission_type="emergency",
        admitted_at=NOW + timedelta(days=days), clinical_features={},
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


def test_record_readmission_links_prior_discharge(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    plan = make_discharged_plan(db, hospital)
    new = _readmit(db, plan, days=10)
    auth_client.set_user(physician)
    resp = auth_client.post("/api/v1/outcomes/readmissions", json={"admission_id": str(new.id)})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["prior_admission_id"] == str(plan.admission_id)
    assert body["days_since_discharge"] == 10


def test_readmission_outside_30_days_rejected(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    plan = make_discharged_plan(db, hospital)
    new = _readmit(db, plan, days=45)
    auth_client.set_user(physician)
    resp = auth_client.post("/api/v1/outcomes/readmissions", json={"admission_id": str(new.id)})
    assert resp.status_code == 400


def test_metrics_shape(auth_client: TestClient, db: Session, hospital: Hospital, physician: User):
    plan = make_discharged_plan(db, hospital)
    new = _readmit(db, plan, days=5)
    auth_client.set_user(physician)
    auth_client.post("/api/v1/outcomes/readmissions", json={"admission_id": str(new.id)})
    m = auth_client.get("/api/v1/outcomes/metrics").json()
    assert m["discharges_tracked"] == 1
    assert m["readmissions_30d"] == 1
    assert m["readmission_rate"] == 1.0
    assert m["escalations_open"] == 0
    assert isinstance(m["monthly"], list)
```

- [ ] **Step 2: Write failing webhook tests** — create `backend/tests/test_webhooks.py`:

```python
from __future__ import annotations

import base64
import hashlib
import hmac
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.followup import CheckinResponse, Escalation
from app.models.hospital import Hospital
from app.services import followup_service
from tests.test_followup_service import NOW, FakeProvider, make_discharged_plan

WEBHOOK_PATH = "/api/v1/webhooks/messaging"


def _sign(params: dict[str, str]) -> str:
    url = f"http://testserver{WEBHOOK_PATH}"
    payload = url + "".join(f"{k}{params[k]}" for k in sorted(params))
    digest = hmac.new(settings.twilio_auth_token.encode(), payload.encode(), hashlib.sha1).digest()
    return base64.b64encode(digest).decode()


def _post(client: TestClient, params: dict[str, str], sig: str | None = None):
    return client.post(
        WEBHOOK_PATH, data=params,
        headers={"X-Twilio-Signature": sig if sig is not None else _sign(params)},
    )


def _setup(db, hospital):
    settings.twilio_auth_token = "test-token"  # noqa: S105 - test only
    plan = make_discharged_plan(db, hospital, phone="+96170000001")
    followup_service.dispatch_due_checkins(db, FakeProvider(), now=NOW + timedelta(days=2, minutes=5))
    db.commit()
    return plan


def test_inbound_reply_matched_to_latest_sent_checkin(client: TestClient, db: Session, hospital: Hospital):
    _setup(db, hospital)
    resp = _post(client, {"From": "whatsapp:+96170000001", "Body": "chest pain", "MessageSid": "SM1"})
    assert resp.status_code == 200
    saved = db.query(CheckinResponse).one()
    assert saved.red_flag is True


def test_duplicate_message_sid_idempotent(client: TestClient, db: Session, hospital: Hospital):
    _setup(db, hospital)
    p = {"From": "whatsapp:+96170000001", "Body": "fine", "MessageSid": "SMdup"}
    _post(client, p)
    _post(client, p)
    assert db.query(CheckinResponse).count() == 1


def test_unknown_sender_flagged_not_dropped(client: TestClient, db: Session, hospital: Hospital):
    _setup(db, hospital)
    resp = _post(client, {"From": "whatsapp:+96170009999", "Body": "hello", "MessageSid": "SM2"})
    assert resp.status_code == 200
    esc = db.query(Escalation).filter_by(trigger="unmatched_message").one()
    assert "+96170009999" in esc.detail


def test_bad_signature_rejected(client: TestClient, db: Session, hospital: Hospital):
    _setup(db, hospital)
    resp = _post(client, {"From": "whatsapp:+96170000001", "Body": "hi", "MessageSid": "SM3"},
                 sig="bogus")
    assert resp.status_code == 403
```

- [ ] **Step 3: Run to verify failure** — both files FAIL with 404s.

- [ ] **Step 4: Implement**

`backend/app/api/v1/outcomes.py`:

```python
"""Readmission outcome recording + metrics for the admin/investor dashboard."""
from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import require_any_clinical_role, require_role
from app.db.session import get_db
from app.models.followup import (
    CheckinStatus, Escalation, EscalationStatus, FollowUpCheckin, ReadmissionEvent,
)
from app.models.patient import Admission, Patient
from app.models.transition import PlanStatus, TransitionPlan
from app.models.user import RoleName, User
from app.schemas.followup import OutcomeMetrics, ReadmissionCreate, ReadmissionRead

router = APIRouter(prefix="/outcomes", tags=["outcomes"])


@router.post("/readmissions", response_model=ReadmissionRead, status_code=status.HTTP_201_CREATED)
def record_readmission(
    body: ReadmissionCreate,
    db: Session = Depends(get_db),
    current: User = Depends(require_role(
        RoleName.PHYSICIAN, RoleName.ADMIN, RoleName.CASE_MANAGER)),
) -> ReadmissionRead:
    adm = db.get(Admission, body.admission_id)
    if adm is None or adm.patient.hospital_id != current.hospital_id:
        raise HTTPException(status_code=404, detail="Admission not found")
    prior = (
        db.query(Admission)
        .filter(
            Admission.patient_id == adm.patient_id,
            Admission.id != adm.id,
            Admission.discharged_at.isnot(None),
            Admission.discharged_at <= adm.admitted_at,
            Admission.discharged_at >= adm.admitted_at - timedelta(days=30),
        )
        .order_by(Admission.discharged_at.desc())
        .first()
    )
    if prior is None:
        raise HTTPException(
            status_code=400,
            detail="No discharge within 30 days before this admission",
        )
    days = (adm.admitted_at - prior.discharged_at).days
    event = ReadmissionEvent(
        hospital_id=current.hospital_id, patient_id=adm.patient_id,
        prior_admission_id=prior.id, readmission_admission_id=adm.id,
        days_since_discharge=days,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return ReadmissionRead.model_validate(event)


@router.get("/metrics", response_model=OutcomeMetrics)
def metrics(
    db: Session = Depends(get_db),
    current: User = Depends(require_any_clinical_role()),
) -> OutcomeMetrics:
    hid = current.hospital_id
    discharged_plans = db.query(TransitionPlan).filter(
        TransitionPlan.hospital_id == hid,
        TransitionPlan.status.in_([PlanStatus.DISCHARGED, PlanStatus.CLOSED]),
    ).all()
    readmissions = db.query(ReadmissionEvent).filter(
        ReadmissionEvent.hospital_id == hid).all()

    checkins = db.query(FollowUpCheckin).filter(
        FollowUpCheckin.hospital_id == hid,
        FollowUpCheckin.status.in_([
            CheckinStatus.SENT, CheckinStatus.RESPONDED, CheckinStatus.NO_RESPONSE]),
    ).all()
    responded = sum(1 for c in checkins if c.status == CheckinStatus.RESPONDED)

    monthly: dict[str, dict[str, int]] = defaultdict(lambda: {"discharges": 0, "readmissions": 0})
    for plan in discharged_plans:
        if plan.admission.discharged_at:
            key = plan.admission.discharged_at.strftime("%Y-%m")
            monthly[key]["discharges"] += 1
    for ev in readmissions:
        key = ev.created_at.strftime("%Y-%m")
        monthly[key]["readmissions"] += 1

    n_discharges = len(discharged_plans)
    return OutcomeMetrics(
        discharges_tracked=n_discharges,
        readmissions_30d=len(readmissions),
        readmission_rate=(len(readmissions) / n_discharges) if n_discharges else None,
        checkin_response_rate=(responded / len(checkins)) if checkins else None,
        escalations_open=db.query(Escalation).filter(
            Escalation.hospital_id == hid,
            Escalation.status != EscalationStatus.RESOLVED).count(),
        escalations_resolved=db.query(Escalation).filter(
            Escalation.hospital_id == hid,
            Escalation.status == EscalationStatus.RESOLVED).count(),
        monthly=[{"month": k, **v} for k, v in sorted(monthly.items())],
    )
```

`backend/app/api/v1/webhooks.py`:

```python
"""Inbound messaging webhook (Twilio WhatsApp). Unauthenticated but
signature-verified; unknown senders are flagged, never dropped."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.followup import (
    CheckinStatus, Escalation, EscalationPriority, FollowUpCheckin,
)
from app.models.patient import Patient
from app.services import followup_service
from app.services.messaging.twilio_whatsapp import validate_twilio_signature

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/messaging")
async def inbound_message(
    request: Request,
    db: Session = Depends(get_db),
    x_twilio_signature: str = Header(default=""),
) -> dict[str, str]:
    form = dict((await request.form()).items())
    if not settings.twilio_auth_token or not validate_twilio_signature(
        str(request.url), form, x_twilio_signature, settings.twilio_auth_token,
    ):
        raise HTTPException(status_code=403, detail="Invalid signature")

    sender = form.get("From", "").removeprefix("whatsapp:")
    body = form.get("Body", "")
    message_sid = form.get("MessageSid") or None

    patient = db.query(Patient).filter(Patient.phone_number == sender).first()
    if patient is None:
        db.add(Escalation(
            hospital_id=_default_hospital_id(db), patient_id=None,
            trigger="unmatched_message",
            detail=f"Inbound message from unrecognized number {sender}: \"{body[:200]}\"",
            priority=EscalationPriority.LOW,
        ))
        db.commit()
        return {"status": "unmatched"}

    checkin = (
        db.query(FollowUpCheckin)
        .filter(
            FollowUpCheckin.patient_id == patient.id,
            FollowUpCheckin.status == CheckinStatus.SENT,
        )
        .order_by(FollowUpCheckin.sent_at.desc())
        .first()
    )
    if checkin is None:
        db.add(Escalation(
            hospital_id=patient.hospital_id, patient_id=patient.id,
            trigger="unmatched_message",
            detail=f"Reply received but no check-in awaiting response: \"{body[:200]}\"",
            priority=EscalationPriority.LOW,
        ))
        db.commit()
        return {"status": "no-open-checkin"}

    followup_service.record_response(db, checkin, body, provider_message_id=message_sid)
    db.commit()
    return {"status": "recorded"}


def _default_hospital_id(db: Session):
    from app.models.hospital import Hospital
    h = db.query(Hospital).first()
    if h is None:
        raise HTTPException(status_code=500, detail="No hospital configured")
    return h.id
```

Register both routers in `backend/app/api/v1/__init__.py`.

- [ ] **Step 5: Run tests** — `py -m pytest tests/test_outcomes_api.py tests/test_webhooks.py -v` → PASS, then full suite.

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/outcomes.py backend/app/api/v1/webhooks.py backend/app/api/v1/__init__.py backend/tests/test_outcomes_api.py backend/tests/test_webhooks.py
git commit -m "feat(outcomes): readmission recording, metrics, signed inbound webhook"
```

---

### Task 8: Scheduler, meta endpoint, seed data, CSV import

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/db/seed.py`
- Create: `backend/scripts/import_patients_csv.py`

No new automated tests (scheduler wiring and seed are exercised manually; the functions they call are already covered).

- [ ] **Step 1: Scheduler + meta endpoint in `backend/app/main.py`**

Add imports:

```python
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

from app.services import followup_service
from app.services.messaging import get_provider
```

Add above `lifespan`:

```python
def _followup_tick() -> None:
    db = SessionLocal()
    try:
        followup_service.run_cycle(db, get_provider(), now=datetime.now(timezone.utc))
    except Exception as exc:  # noqa: BLE001 - a failed tick must not kill the scheduler
        logger.warning("Follow-up cycle failed: %s", exc)
    finally:
        db.close()
```

Inside `lifespan`, before `yield` (after seeding):

```python
    scheduler = BackgroundScheduler()
    scheduler.add_job(_followup_tick, "interval", minutes=2, id="followup-cycle")
    scheduler.start()
    logger.info("Follow-up scheduler started (provider=%s)", settings.messaging_provider)
```

and change `yield` to:

```python
    yield
    scheduler.shutdown(wait=False)
```

After the `/health` route, add:

```python
@app.get("/api/v1/meta")
def meta() -> dict[str, str]:
    return {"app": settings.app_name, "messaging_mode": settings.messaging_provider}
```

(Tests are unaffected: conftest's `TestClient(app)` is not used as a context manager, so lifespan — and the scheduler — never run in tests.)

- [ ] **Step 2: Seed demo transitions in `backend/app/db/seed.py`**

Add `(RoleName.PHARMACIST, "pharmacist@careinsight.dev", "Demo Pharmacist")` to the demo-users list (line ~27).

Add a new function (place before `seed_all`) and call it at the end of `seed_all(db)` as `seed_transitions(db)`:

```python
def seed_transitions(db: Session) -> None:
    """Demo transition plans, check-ins, and escalations. Idempotent."""
    from datetime import datetime, timedelta, timezone

    from app.models.followup import CheckinStatus, FollowUpCheckin
    from app.models.patient import Admission, Patient
    from app.models.transition import TransitionPlan
    from app.services import followup_service, transition_service

    if db.query(TransitionPlan).count() > 0:
        return
    now = datetime.now(timezone.utc)

    active = (
        db.query(Admission).filter(Admission.discharged_at.is_(None)).limit(6).all()
    )
    for i, adm in enumerate(active):
        patient = db.get(Patient, adm.patient_id)
        if not patient.phone_number:
            patient.phone_number = f"+9617000{1000 + i}"
        hospital_id = patient.hospital_id
        plan = transition_service.create_plan(db, adm, hospital_id)
        plan.target_discharge_date = (now + timedelta(days=i % 3)).date()
        # discharge two of them so the follow-up timeline has content
        if i < 2:
            transition_service.discharge_plan(db, plan, now=now - timedelta(days=3))
            # mark the day-2 check-in as sent so the demo phone has a message
            c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).first()
            if c is not None:
                c.status = CheckinStatus.SENT
                c.sent_at = now - timedelta(days=1)
                c.sent_body = "(seeded) Day-2 check-in message"
        # answer one check-in with a red flag so the escalation queue is not empty
        if i == 0:
            c = db.query(FollowUpCheckin).filter_by(plan_id=plan.id, day_offset=2).first()
            if c is not None:
                followup_service.record_response(
                    db, c, "I have chest pain and missed my meds",
                    provider_message_id=f"seed-{plan.id}")
    db.commit()
```

- [ ] **Step 3: CSV import script** — create `backend/scripts/import_patients_csv.py`:

```python
"""Pilot data loader: import patients + admissions from a CSV.

Usage (from backend/):
    py scripts/import_patients_csv.py data.csv --hospital-slug rizk

CSV columns (header row required):
    mrn,first_name,last_name,dob,sex,phone_number,preferred_language,
    department_code,admission_type,admitted_at,discharged_at
Dates: YYYY-MM-DD; datetimes: YYYY-MM-DDTHH:MM (discharged_at may be empty).
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.db.session import SessionLocal  # noqa: E402
from app.models.hospital import Department, Hospital  # noqa: E402
from app.models.patient import Admission, Patient  # noqa: E402


def _dt(value: str) -> datetime | None:
    if not value.strip():
        return None
    return datetime.fromisoformat(value).replace(tzinfo=timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path")
    parser.add_argument("--hospital-slug", required=True)
    args = parser.parse_args()

    db = SessionLocal()
    hospital = db.query(Hospital).filter(Hospital.slug == args.hospital_slug).first()
    if hospital is None:
        print(f"No hospital with slug {args.hospital_slug!r}")
        return 1

    created_p = created_a = skipped = 0
    with open(args.csv_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            dept = db.query(Department).filter(
                Department.hospital_id == hospital.id,
                Department.code == row["department_code"].strip(),
            ).first()
            if dept is None:
                print(f"SKIP {row['mrn']}: unknown department {row['department_code']!r}")
                skipped += 1
                continue
            patient = db.query(Patient).filter(
                Patient.hospital_id == hospital.id, Patient.mrn == row["mrn"].strip(),
            ).first()
            if patient is None:
                patient = Patient(
                    hospital_id=hospital.id, mrn=row["mrn"].strip(),
                    first_name=row["first_name"].strip(), last_name=row["last_name"].strip(),
                    dob=date.fromisoformat(row["dob"].strip()), sex=row["sex"].strip(),
                    phone_number=row.get("phone_number", "").strip() or None,
                    preferred_language=row.get("preferred_language", "en").strip() or "en",
                )
                db.add(patient)
                db.flush()
                created_p += 1
            db.add(Admission(
                patient_id=patient.id, department_id=dept.id,
                admission_type=row["admission_type"].strip(),
                admitted_at=_dt(row["admitted_at"]),
                discharged_at=_dt(row.get("discharged_at", "")),
                clinical_features={},
            ))
            created_a += 1
    db.commit()
    print(f"Imported {created_p} patients, {created_a} admissions ({skipped} skipped).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Verify manually**

```powershell
cd backend
Remove-Item dev.db -ErrorAction SilentlyContinue
py -m pytest                        # full suite green
py -m ruff check app/
py -m uvicorn app.main:app --port 8000   # boots, log shows "Follow-up scheduler started"
# GET http://localhost:8000/api/v1/meta → {"app": "...", "messaging_mode": "simulated"}
# Ctrl+C
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/app/db/seed.py backend/scripts/import_patients_csv.py
git commit -m "feat(followup): APScheduler wiring, meta endpoint, demo seed, CSV import"
```

---

### Task 9: Frontend API layer + board grouping logic

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Create: `frontend/src/lib/board.ts`
- Test: `frontend/src/lib/board.test.ts`

- [ ] **Step 1: Add `patch` + types to `frontend/src/lib/api.ts`**

In the `api` object, after `post`:

```typescript
  patch: <T>(p: string, body?: unknown) =>
    request<T>(p, { method: "PATCH", body: body ? JSON.stringify(body) : undefined }),
```

Append type definitions at the end of the file:

```typescript
export interface TransitionTask {
  id: string;
  role: string;
  title: string;
  status: "open" | "done" | "skipped";
  due_date: string | null;
  source: string;
  created_at: string;
}

export interface TransitionPlan {
  id: string;
  admission_id: string;
  status: "planning" | "ready" | "discharged" | "closed";
  target_discharge_date: string | null;
  created_at: string;
  tasks: TransitionTask[];
}

export interface BoardRow {
  patient_id: string;
  admission_id: string;
  first_name: string;
  last_name: string;
  mrn: string;
  department: string;
  probability: number | null;
  risk_tier: string | null;
  plan_id: string | null;
  plan_status: string | null;
  target_discharge_date: string | null;
  open_tasks: number;
  open_task_roles: string[];
}

export interface BoardResponse {
  rows: BoardRow[];
}

export interface CheckinResponseItem {
  id: string;
  raw_text: string;
  red_flag: boolean;
  meds_missed: boolean;
  opted_out: boolean;
  concern_score: number;
  created_at: string;
}

export interface Checkin {
  id: string;
  patient_id: string;
  day_offset: number;
  scheduled_at: string;
  status: string;
  sent_at: string | null;
  sent_body: string | null;
  language: string;
  responses: CheckinResponseItem[];
}

export interface Escalation {
  id: string;
  patient_id: string | null;
  patient_name: string | null;
  trigger: string;
  detail: string;
  priority: "high" | "medium" | "low";
  status: "open" | "in_progress" | "resolved";
  resolution_notes: string | null;
  created_at: string;
}

export interface OutcomeMetrics {
  discharges_tracked: number;
  readmissions_30d: number;
  readmission_rate: number | null;
  checkin_response_rate: number | null;
  escalations_open: number;
  escalations_resolved: number;
  monthly: Array<{ month: string; discharges: number; readmissions: number }>;
}

export interface MetaResponse {
  app: string;
  messaging_mode: string;
}
```

Note: `/api/v1/meta` is under the same BASE_URL prefix, so `api.get<MetaResponse>("/meta")` works.

- [ ] **Step 2: Write the failing grouping test** — create `frontend/src/lib/board.test.ts`:

```typescript
import { describe, expect, it } from "vitest";
import { groupForRow } from "./board";
import type { BoardRow } from "./api";

const base: BoardRow = {
  patient_id: "p", admission_id: "a", first_name: "F", last_name: "L",
  mrn: "M", department: "Med", probability: 0.4, risk_tier: "Medium",
  plan_id: "plan", plan_status: "planning", target_discharge_date: "2026-07-02",
  open_tasks: 3, open_task_roles: ["nurse"],
};

describe("groupForRow", () => {
  it("is unplanned without a plan", () => {
    expect(groupForRow({ ...base, plan_id: null, plan_status: null }, "2026-07-02")).toBe("unplanned");
  });
  it("is blocked when target date reached and tasks open", () => {
    expect(groupForRow(base, "2026-07-02")).toBe("blocked");
    expect(groupForRow({ ...base, target_discharge_date: "2026-07-01" }, "2026-07-02")).toBe("blocked");
  });
  it("is on_track when target in future or no open tasks", () => {
    expect(groupForRow({ ...base, target_discharge_date: "2026-07-09" }, "2026-07-02")).toBe("on_track");
    expect(groupForRow({ ...base, open_tasks: 0 }, "2026-07-02")).toBe("on_track");
    expect(groupForRow({ ...base, target_discharge_date: null }, "2026-07-02")).toBe("on_track");
  });
});
```

- [ ] **Step 3: Run to verify failure** — `npm test` → FAIL (module missing).

- [ ] **Step 4: Implement** — create `frontend/src/lib/board.ts`:

```typescript
import type { BoardRow } from "./api";

export type BoardGroup = "blocked" | "on_track" | "unplanned";

/** `today` is an ISO date string (YYYY-MM-DD) so string comparison works. */
export function groupForRow(row: BoardRow, today: string): BoardGroup {
  if (!row.plan_id) return "unplanned";
  if (
    row.open_tasks > 0 &&
    row.target_discharge_date !== null &&
    row.target_discharge_date <= today
  ) {
    return "blocked";
  }
  return "on_track";
}

export function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}
```

- [ ] **Step 5: Run tests** — `npm test` → PASS; `npm run lint` → clean.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/api.ts frontend/src/lib/board.ts frontend/src/lib/board.test.ts
git commit -m "feat(frontend): transitions API types, patch verb, board grouping"
```

---

### Task 10: Discharge Readiness Board (WardView)

**Files:**
- Modify: `frontend/src/pages/WardView.tsx` (full replacement)

- [ ] **Step 1: Replace `frontend/src/pages/WardView.tsx` with:**

```tsx
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, BoardResponse, BoardRow } from "@/lib/api";
import { BoardGroup, groupForRow, todayIso } from "@/lib/board";
import { StatCard } from "@/components/clinical/StatCard";
import { RiskBadge } from "@/components/clinical/RiskBadge";

const GROUP_META: Record<BoardGroup, { title: string; blurb: string; accent: string }> = {
  blocked: {
    title: "Dischargeable today — blocked",
    blurb: "Target discharge date reached but tasks remain open.",
    accent: "border-l-4 border-risk-high",
  },
  on_track: {
    title: "On track",
    blurb: "Transition plan in progress.",
    accent: "border-l-4 border-brand-600",
  },
  unplanned: {
    title: "No transition plan yet",
    blurb: "Start discharge planning to generate the task checklist.",
    accent: "border-l-4 border-slate-300",
  },
};

export function WardView() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const today = todayIso();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["transition-board"],
    queryFn: () => api.get<BoardResponse>("/transitions/board"),
  });

  const createPlan = useMutation({
    mutationFn: (admissionId: string) =>
      api.post("/transitions/plans", { admission_id: admissionId }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["transition-board"] }),
  });

  const rows = data?.rows ?? [];
  const grouped: Record<BoardGroup, BoardRow[]> = { blocked: [], on_track: [], unplanned: [] };
  for (const row of rows) grouped[groupForRow(row, today)].push(row);

  return (
    <div>
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold text-navy-700">
          Discharge Readiness Board
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Every admitted patient, their readmission risk, and what's blocking discharge.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <StatCard label="Blocked discharges" value={isLoading ? "—" : grouped.blocked.length} tone="risk" />
        <StatCard label="On track" value={isLoading ? "—" : grouped.on_track.length} tone="success" />
        <StatCard label="Awaiting planning" value={isLoading ? "—" : grouped.unplanned.length} tone="default" />
      </div>

      {isError && (
        <div className="text-risk-high text-sm py-6">Failed to load the discharge board.</div>
      )}

      {(Object.keys(GROUP_META) as BoardGroup[]).map((group) => {
        const meta = GROUP_META[group];
        const groupRows = grouped[group];
        if (!isLoading && groupRows.length === 0) return null;
        return (
          <div key={group} className="mb-6">
            <div className="mb-2">
              <h2 className="font-display text-sm font-semibold text-navy-700">{meta.title}</h2>
              <p className="text-xs text-slate-400">{meta.blurb}</p>
            </div>
            <div className={`bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden ${meta.accent}`}>
              <table className="w-full text-sm">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    {["Patient", "MRN", "Department", "Risk", "Target discharge", "Open tasks", ""].map((h) => (
                      <th key={h} className="text-left px-4 py-2.5 font-sans font-medium text-slate-500 text-xs uppercase tracking-wide">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {groupRows.map((r) => (
                    <tr
                      key={r.admission_id}
                      className="hover:bg-slate-50 cursor-pointer transition-colors duration-100"
                      onClick={() => navigate(`/patients/${r.patient_id}`)}
                    >
                      <td className="px-4 py-3 font-sans font-medium text-slate-800">
                        {r.last_name}, {r.first_name}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-500">{r.mrn}</td>
                      <td className="px-4 py-3 text-slate-600">{r.department}</td>
                      <td className="px-4 py-3">
                        {r.risk_tier ? (
                          <span className="inline-flex items-center gap-2">
                            <span className="font-mono font-semibold text-slate-800">
                              {((r.probability ?? 0) * 100).toFixed(1)}%
                            </span>
                            <RiskBadge tier={r.risk_tier.toLowerCase() as "high" | "medium" | "low"} size="sm" />
                          </span>
                        ) : (
                          <span className="text-xs text-slate-400">No prediction</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-slate-600 text-xs">
                        {r.target_discharge_date ?? "—"}
                      </td>
                      <td className="px-4 py-3">
                        {r.plan_id ? (
                          r.open_tasks > 0 ? (
                            <span className="inline-flex items-center rounded-full bg-amber-50 border border-amber-200 text-amber-800 px-2 py-0.5 text-xs">
                              {r.open_tasks} open · {r.open_task_roles.join(", ")}
                            </span>
                          ) : (
                            <span className="inline-flex items-center rounded-full bg-green-50 border border-green-200 text-green-700 px-2 py-0.5 text-xs">
                              All tasks done
                            </span>
                          )
                        ) : (
                          <button
                            className="text-xs font-medium text-brand-600 hover:text-brand-700 underline"
                            onClick={(e) => {
                              e.stopPropagation();
                              createPlan.mutate(r.admission_id);
                            }}
                            disabled={createPlan.isPending}
                          >
                            Start discharge planning
                          </button>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <span className="text-brand-600 hover:text-brand-700 text-xs font-medium">
                          View chart →
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        );
      })}

      {isLoading && <div className="text-slate-400 text-sm py-6">Loading board…</div>}
      {!isLoading && rows.length === 0 && !isError && (
        <div className="text-slate-400 text-sm py-6">No active admissions.</div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify** — `npm run lint` → clean. Start all three services, log in, open `/ward`: three grouped sections render; "Start discharge planning" creates a plan and the row moves out of *unplanned*.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/WardView.tsx
git commit -m "feat(frontend): ward view becomes grouped discharge readiness board"
```

---

### Task 11: Transition tab + simulated phone on PatientChart

**Files:**
- Create: `frontend/src/components/clinical/TransitionTab.tsx`
- Create: `frontend/src/components/clinical/SimulatedPhone.tsx`
- Modify: `frontend/src/pages/PatientChart.tsx`

- [ ] **Step 1: Create `frontend/src/components/clinical/SimulatedPhone.tsx`:**

```tsx
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api, Checkin } from "@/lib/api";

/** WhatsApp-styled demo panel: shows outbound check-ins, lets the demo
 * operator type the patient's reply. Rendered only in simulated mode. */
export function SimulatedPhone({ patientId, checkins }: { patientId: string; checkins: Checkin[] }) {
  const qc = useQueryClient();
  const [drafts, setDrafts] = useState<Record<string, string>>({});

  const reply = useMutation({
    mutationFn: ({ checkinId, text }: { checkinId: string; text: string }) =>
      api.post(`/checkins/${checkinId}/simulate-reply`, { text }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["checkins", patientId] });
      qc.invalidateQueries({ queryKey: ["escalations", patientId] });
    },
  });

  const sent = checkins.filter((c) => c.status === "sent" || c.status === "responded");

  return (
    <div className="rounded-xl border border-emerald-200 bg-emerald-50/40 p-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="h-2 w-2 rounded-full bg-emerald-500" />
        <span className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-emerald-700">
          Simulated patient phone — demo mode
        </span>
      </div>
      {sent.length === 0 && (
        <p className="text-xs text-slate-500">No check-ins sent yet. Messages appear here once dispatched.</p>
      )}
      <div className="space-y-3">
        {sent.map((c) => (
          <div key={c.id} className="space-y-2">
            <div className="max-w-[85%] rounded-lg rounded-tl-none bg-white border border-slate-200 p-2.5 text-xs text-slate-700 whitespace-pre-wrap">
              {c.sent_body}
            </div>
            {c.responses.map((r) => (
              <div key={r.id} className="max-w-[85%] ml-auto rounded-lg rounded-tr-none bg-emerald-100 border border-emerald-200 p-2.5 text-xs text-slate-800">
                {r.raw_text}
              </div>
            ))}
            {c.status === "sent" && (
              <form
                className="flex gap-2"
                onSubmit={(e) => {
                  e.preventDefault();
                  const text = drafts[c.id]?.trim();
                  if (text) reply.mutate({ checkinId: c.id, text });
                }}
              >
                <input
                  className="flex-1 border border-slate-300 rounded-md px-2.5 py-1.5 text-xs bg-white focus:outline-none focus:border-brand-600"
                  placeholder="Type the patient's reply…"
                  value={drafts[c.id] ?? ""}
                  onChange={(e) => setDrafts((d) => ({ ...d, [c.id]: e.target.value }))}
                />
                <button
                  type="submit"
                  disabled={reply.isPending}
                  className="text-xs font-medium bg-emerald-600 text-white rounded-md px-3 py-1.5 hover:bg-emerald-700 disabled:opacity-50"
                >
                  Reply
                </button>
              </form>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Create `frontend/src/components/clinical/TransitionTab.tsx`:**

```tsx
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ApiError, api, Checkin, Escalation, MetaResponse, TransitionPlan,
} from "@/lib/api";
import { Card } from "@/components/core/Card";
import { Button } from "@/components/core/Button";
import { SimulatedPhone } from "@/components/clinical/SimulatedPhone";

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-3">
      {children}
    </div>
  );
}

const CHECKIN_STATUS_STYLE: Record<string, string> = {
  scheduled: "bg-slate-100 text-slate-600",
  sent: "bg-blue-50 text-blue-700 border border-blue-200",
  responded: "bg-green-50 text-green-700 border border-green-200",
  no_response: "bg-amber-50 text-amber-800 border border-amber-200",
  send_failed: "bg-red-50 text-red-700 border border-red-200",
  manual: "bg-purple-50 text-purple-700 border border-purple-200",
  skipped: "bg-slate-100 text-slate-400",
};

const PRIORITY_STYLE: Record<string, string> = {
  high: "text-risk-high",
  medium: "text-amber-700",
  low: "text-slate-500",
};

export function TransitionTab({ patientId, admissionId }: { patientId: string; admissionId: string | null }) {
  const qc = useQueryClient();
  const invalidate = () => {
    qc.invalidateQueries({ queryKey: ["transition-plan", patientId] });
    qc.invalidateQueries({ queryKey: ["checkins", patientId] });
    qc.invalidateQueries({ queryKey: ["escalations", patientId] });
    qc.invalidateQueries({ queryKey: ["transition-board"] });
  };

  const plan = useQuery<TransitionPlan, ApiError>({
    queryKey: ["transition-plan", patientId],
    queryFn: () => api.get<TransitionPlan>(`/transitions/plans/by-patient/${patientId}`),
    retry: false,
  });

  const checkins = useQuery<Checkin[], ApiError>({
    queryKey: ["checkins", patientId],
    queryFn: () => api.get<Checkin[]>(`/checkins?patient_id=${patientId}`),
  });

  const escalations = useQuery<Escalation[], ApiError>({
    queryKey: ["escalations", patientId],
    queryFn: () => api.get<Escalation[]>(`/escalations?patient_id=${patientId}`),
  });

  const meta = useQuery({
    queryKey: ["meta"],
    queryFn: () => api.get<MetaResponse>("/meta"),
    staleTime: Infinity,
  });

  const createPlan = useMutation({
    mutationFn: () => api.post("/transitions/plans", { admission_id: admissionId }),
    onSuccess: invalidate,
  });
  const updateTask = useMutation({
    mutationFn: ({ taskId, status }: { taskId: string; status: string }) =>
      api.patch(`/transitions/tasks/${taskId}`, { status }),
    onSuccess: invalidate,
  });
  const discharge = useMutation({
    mutationFn: () => api.post(`/transitions/plans/${plan.data!.id}/discharge`),
    onSuccess: invalidate,
  });
  const refreshTasks = useMutation({
    mutationFn: () => api.post(`/transitions/plans/${plan.data!.id}/refresh-tasks`),
    onSuccess: invalidate,
  });

  if (plan.isError && plan.error.status === 404) {
    return (
      <Card>
        <SectionLabel>Transition Plan</SectionLabel>
        <p className="text-sm text-slate-500 mb-3">
          No discharge planning has started for this patient.
        </p>
        <Button onClick={() => createPlan.mutate()} disabled={!admissionId || createPlan.isPending}>
          Start discharge planning
        </Button>
        {!admissionId && (
          <p className="text-xs text-slate-400 mt-2">Requires an admission on record.</p>
        )}
      </Card>
    );
  }

  const tasks = plan.data?.tasks ?? [];
  const byRole = tasks.reduce<Record<string, typeof tasks>>((acc, t) => {
    (acc[t.role] ??= []).push(t);
    return acc;
  }, {});
  const openCount = tasks.filter((t) => t.status === "open").length;

  return (
    <div className="space-y-5">
      <Card>
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <SectionLabel>Transition Checklist</SectionLabel>
            <p className="text-xs text-slate-400 -mt-2 mb-3">
              Plan status: <span className="font-medium text-slate-600">{plan.data?.status ?? "…"}</span>
              {" · "}{openCount} task{openCount !== 1 ? "s" : ""} open
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => refreshTasks.mutate()}
              disabled={!plan.data || refreshTasks.isPending}>
              Refresh from latest risk
            </Button>
            {plan.data?.status === "planning" && (
              <Button onClick={() => discharge.mutate()} disabled={discharge.isPending}>
                Confirm discharge
              </Button>
            )}
          </div>
        </div>
        {plan.isLoading && <p className="text-sm text-slate-400">Loading…</p>}
        {Object.entries(byRole).map(([role, roleTasks]) => (
          <div key={role} className="mb-4 last:mb-0">
            <div className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-1.5">
              {role.replace("_", " ")}
            </div>
            <div className="space-y-1">
              {roleTasks.map((t) => (
                <label
                  key={t.id}
                  className="flex items-start gap-2.5 p-2 rounded hover:bg-slate-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    className="mt-0.5 accent-brand-600"
                    checked={t.status === "done"}
                    onChange={() =>
                      updateTask.mutate({
                        taskId: t.id,
                        status: t.status === "done" ? "open" : "done",
                      })
                    }
                  />
                  <span className={`text-sm ${t.status === "done" ? "line-through text-slate-400" : "text-slate-700"}`}>
                    {t.title}
                    {t.source !== "default" && (
                      <span className="ml-2 text-[0.65rem] text-brand-600 bg-brand-600/5 rounded px-1.5 py-0.5">
                        from risk: {t.source}
                      </span>
                    )}
                  </span>
                </label>
              ))}
            </div>
          </div>
        ))}
      </Card>

      <Card>
        <SectionLabel>Post-Discharge Follow-Up</SectionLabel>
        {(checkins.data?.length ?? 0) === 0 ? (
          <p className="text-sm text-slate-500">
            Check-ins are scheduled automatically when discharge is confirmed.
          </p>
        ) : (
          <div className="space-y-2">
            {checkins.data!.map((c) => (
              <div key={c.id} className="flex items-start justify-between gap-3 py-2 border-b border-slate-50 last:border-0">
                <div>
                  <div className="text-sm font-medium text-slate-700">Day {c.day_offset} check-in</div>
                  <div className="text-xs text-slate-400">
                    {new Date(c.scheduled_at).toLocaleDateString()} · {c.language.toUpperCase()}
                  </div>
                  {c.responses.map((r) => (
                    <div key={r.id} className="text-xs mt-1 text-slate-600">
                      Reply: “{r.raw_text}”
                      {r.red_flag && <span className="ml-1.5 text-risk-high font-semibold">RED FLAG</span>}
                      {r.meds_missed && !r.red_flag && <span className="ml-1.5 text-amber-700 font-semibold">MEDS MISSED</span>}
                    </div>
                  ))}
                </div>
                <span className={`text-[0.65rem] font-medium rounded-full px-2 py-0.5 ${CHECKIN_STATUS_STYLE[c.status] ?? ""}`}>
                  {c.status.replace("_", " ")}
                </span>
              </div>
            ))}
          </div>
        )}
      </Card>

      {(escalations.data?.length ?? 0) > 0 && (
        <Card>
          <SectionLabel>Escalations</SectionLabel>
          <div className="space-y-2">
            {escalations.data!.map((e) => (
              <div key={e.id} className="text-sm py-1.5 border-b border-slate-50 last:border-0">
                <span className={`font-semibold uppercase text-xs mr-2 ${PRIORITY_STYLE[e.priority]}`}>
                  {e.priority}
                </span>
                <span className="text-slate-700">{e.detail}</span>
                <span className="ml-2 text-xs text-slate-400">({e.status.replace("_", " ")})</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      {meta.data?.messaging_mode === "simulated" && (
        <SimulatedPhone patientId={patientId} checkins={checkins.data ?? []} />
      )}
    </div>
  );
}
```

- [ ] **Step 3: Add tabs to `frontend/src/pages/PatientChart.tsx`**

1. Add imports: `import { TransitionTab } from "@/components/clinical/TransitionTab";`
2. Inside `PatientChart()`, after the `qc` line, add: `const [tab, setTab] = useState<"overview" | "transition">("overview");` (`useState` is already imported).
3. In the returned JSX, directly under the page header block (patient name/MRN), insert the tab bar:

```tsx
      <div className="flex gap-1 border-b border-slate-200 mb-5">
        {(["overview", "transition"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t === "overview" ? "Overview" : "Transition & Follow-Up"}
          </button>
        ))}
      </div>
```

4. Wrap the entire existing chart body (risk gauge, SHAP, recommendations, chat — everything currently rendered below the header) in `{tab === "overview" && ( ... )}`.
5. After that block add:

```tsx
      {tab === "transition" && (
        <TransitionTab patientId={patientId} admissionId={admissions.data?.[0]?.id ?? null} />
      )}
```

- [ ] **Step 4: Verify** — `npm run lint` → clean. In the app: open a patient, switch to "Transition & Follow-Up", start planning, tick tasks, confirm discharge, see check-ins appear; in the simulated phone, dispatch happens on the next scheduler tick (≤2 min) or check-in rows show `scheduled` until then. Reply "chest pain" on a sent check-in → RED FLAG appears and an escalation shows.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/clinical/TransitionTab.tsx frontend/src/components/clinical/SimulatedPhone.tsx frontend/src/pages/PatientChart.tsx
git commit -m "feat(frontend): transition tab with checklist, follow-up timeline, simulated phone"
```

---

### Task 12: Escalation queue, my-tasks widget, outcomes panel, demo badge

**Files:**
- Create: `frontend/src/components/clinical/EscalationQueue.tsx`
- Create: `frontend/src/components/clinical/MyTasksWidget.tsx`
- Create: `frontend/src/components/clinical/OutcomesPanel.tsx`
- Create: `frontend/src/components/core/DemoBadge.tsx`
- Modify: `frontend/src/pages/CaseManagerDashboard.tsx`, `frontend/src/pages/ClinicianDashboard.tsx`, `frontend/src/pages/AdminDashboard.tsx`, `frontend/src/components/AppShell.tsx`

- [ ] **Step 1: Create `frontend/src/components/clinical/EscalationQueue.tsx`:**

```tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, Escalation } from "@/lib/api";
import { Card } from "@/components/core/Card";

const PRIORITY_BADGE: Record<string, string> = {
  high: "bg-red-50 text-red-700 border-red-200",
  medium: "bg-amber-50 text-amber-800 border-amber-200",
  low: "bg-slate-50 text-slate-600 border-slate-200",
};

function daysWaiting(createdAt: string): number {
  return Math.floor((Date.now() - new Date(createdAt).getTime()) / 86_400_000);
}

export function EscalationQueue() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [resolving, setResolving] = useState<string | null>(null);
  const [notes, setNotes] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["escalations", "open"],
    queryFn: () => api.get<Escalation[]>("/escalations?status=open"),
    refetchInterval: 30_000,
  });

  const resolve = useMutation({
    mutationFn: ({ id, resolution_notes }: { id: string; resolution_notes: string }) =>
      api.patch(`/escalations/${id}`, { status: "resolved", resolution_notes }),
    onSuccess: () => {
      setResolving(null);
      setNotes("");
      qc.invalidateQueries({ queryKey: ["escalations"] });
    },
  });

  return (
    <Card>
      <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-3">
        Escalation Queue — needs action today
      </div>
      {isLoading && <p className="text-sm text-slate-400">Loading…</p>}
      {!isLoading && (data?.length ?? 0) === 0 && (
        <p className="text-sm text-slate-500">No open escalations. All patients accounted for.</p>
      )}
      <div className="space-y-2">
        {data?.map((e) => {
          const waiting = daysWaiting(e.created_at);
          return (
            <div key={e.id} className="p-3 rounded-lg border border-slate-100 hover:border-slate-200 transition-colors">
              <div className="flex items-start justify-between gap-3 flex-wrap">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-[0.65rem] font-semibold uppercase rounded-full border px-2 py-0.5 ${PRIORITY_BADGE[e.priority]}`}>
                      {e.priority}
                    </span>
                    {e.patient_name ? (
                      <button
                        className="text-sm font-medium text-slate-800 hover:text-brand-700 hover:underline"
                        onClick={() => e.patient_id && navigate(`/patients/${e.patient_id}`)}
                      >
                        {e.patient_name}
                      </button>
                    ) : (
                      <span className="text-sm font-medium text-slate-500 italic">Unmatched sender</span>
                    )}
                    <span className="text-xs text-slate-400">
                      {waiting === 0 ? "today" : `${waiting}d waiting`}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 mt-1">{e.detail}</p>
                </div>
                <button
                  className="text-xs font-medium text-brand-600 hover:text-brand-700 underline shrink-0"
                  onClick={() => setResolving(resolving === e.id ? null : e.id)}
                >
                  {resolving === e.id ? "Cancel" : "Resolve"}
                </button>
              </div>
              {resolving === e.id && (
                <form
                  className="mt-2 flex gap-2"
                  onSubmit={(ev) => {
                    ev.preventDefault();
                    if (notes.trim()) resolve.mutate({ id: e.id, resolution_notes: notes.trim() });
                  }}
                >
                  <input
                    autoFocus
                    className="flex-1 border border-slate-300 rounded-md px-2.5 py-1.5 text-xs focus:outline-none focus:border-brand-600"
                    placeholder="Outcome notes — e.g. called patient, adjusted meds, PCP booked"
                    value={notes}
                    onChange={(ev) => setNotes(ev.target.value)}
                  />
                  <button
                    type="submit"
                    disabled={resolve.isPending || !notes.trim()}
                    className="text-xs font-medium bg-brand-600 text-white rounded-md px-3 py-1.5 hover:bg-brand-700 disabled:opacity-50"
                  >
                    Mark resolved
                  </button>
                </form>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
```

- [ ] **Step 2: Create `frontend/src/components/clinical/MyTasksWidget.tsx`:**

```tsx
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, TransitionTask } from "@/lib/api";
import { Card } from "@/components/core/Card";

export function MyTasksWidget() {
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["my-tasks"],
    queryFn: () => api.get<TransitionTask[]>("/transitions/tasks/mine"),
  });
  const complete = useMutation({
    mutationFn: (taskId: string) => api.patch(`/transitions/tasks/${taskId}`, { status: "done" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["my-tasks"] }),
  });

  return (
    <Card>
      <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-3">
        My Open Transition Tasks
      </div>
      {isLoading && <p className="text-sm text-slate-400">Loading…</p>}
      {!isLoading && (data?.length ?? 0) === 0 && (
        <p className="text-sm text-slate-500">Nothing pending for your role. 🎉</p>
      )}
      <div className="space-y-1">
        {data?.slice(0, 8).map((t) => (
          <label key={t.id} className="flex items-start gap-2.5 p-1.5 rounded hover:bg-slate-50 cursor-pointer">
            <input
              type="checkbox"
              className="mt-0.5 accent-brand-600"
              checked={false}
              onChange={() => complete.mutate(t.id)}
            />
            <span className="text-sm text-slate-700">{t.title}</span>
          </label>
        ))}
        {(data?.length ?? 0) > 8 && (
          <p className="text-xs text-slate-400 mt-1">+{data!.length - 8} more on the board</p>
        )}
      </div>
    </Card>
  );
}
```

- [ ] **Step 3: Create `frontend/src/components/clinical/OutcomesPanel.tsx`:**

```tsx
import { useQuery } from "@tanstack/react-query";
import { api, OutcomeMetrics } from "@/lib/api";
import { Card } from "@/components/core/Card";

function Metric({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div>
      <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-1">
        {label}
      </div>
      <div className="font-sans text-3xl font-bold text-navy-700">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
    </div>
  );
}

export function OutcomesPanel() {
  const { data } = useQuery({
    queryKey: ["outcome-metrics"],
    queryFn: () => api.get<OutcomeMetrics>("/outcomes/metrics"),
  });

  const pct = (v: number | null) => (v === null ? "—" : `${(v * 100).toFixed(1)}%`);

  return (
    <Card>
      <div className="font-display text-[0.65rem] font-semibold tracking-allcaps uppercase text-slate-400 mb-4">
        Care Transition Outcomes
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
        <Metric label="Discharges tracked" value={data ? String(data.discharges_tracked) : "—"} />
        <Metric label="30-day readmission rate" value={data ? pct(data.readmission_rate) : "—"}
          sub={data ? `${data.readmissions_30d} readmissions` : undefined} />
        <Metric label="Check-in response rate" value={data ? pct(data.checkin_response_rate) : "—"} />
        <Metric label="Escalations resolved" value={data ? String(data.escalations_resolved) : "—"}
          sub={data ? `${data.escalations_open} still open` : undefined} />
      </div>
      {data && data.monthly.length > 0 && (
        <div className="mt-5 border-t border-slate-100 pt-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400 mb-2">
            Monthly trend
          </div>
          <div className="flex gap-3 flex-wrap">
            {data.monthly.map((m) => (
              <div key={m.month} className="text-xs text-slate-600 bg-slate-50 rounded-md px-2.5 py-1.5">
                <span className="font-mono font-medium">{m.month}</span>
                {" · "}{m.discharges} discharged · {m.readmissions} readmitted
              </div>
            ))}
          </div>
        </div>
      )}
      <p className="text-xs text-slate-400 italic mt-4">
        These numbers also retrain the local model — every tracked discharge improves prediction accuracy on this hospital's population.
      </p>
    </Card>
  );
}
```

- [ ] **Step 4: Create `frontend/src/components/core/DemoBadge.tsx`:**

```tsx
import { useQuery } from "@tanstack/react-query";
import { api, MetaResponse } from "@/lib/api";

/** Visible badge whenever messaging runs in simulated mode, so demo
 * messages can never be mistaken for real patient contact. */
export function DemoBadge() {
  const { data } = useQuery({
    queryKey: ["meta"],
    queryFn: () => api.get<MetaResponse>("/meta"),
    staleTime: Infinity,
  });
  if (data?.messaging_mode !== "simulated") return null;
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-300 bg-emerald-50 text-emerald-700 px-2.5 py-0.5 text-[0.65rem] font-semibold uppercase tracking-wide">
      <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
      Demo mode — simulated messaging
    </span>
  );
}
```

- [ ] **Step 5: Wire the pages**

- `CaseManagerDashboard.tsx`: add `import { EscalationQueue } from "@/components/clinical/EscalationQueue";` and render `<EscalationQueue />` as the FIRST child inside the top-level `space-y-6` div, directly after the header block — the queue is the case manager's primary surface.
- `ClinicianDashboard.tsx`: add `import { MyTasksWidget } from "@/components/clinical/MyTasksWidget";` and render `<MyTasksWidget />` as the first widget in the page's main content area (top of the existing grid or directly under the page header).
- `AdminDashboard.tsx`: add `import { OutcomesPanel } from "@/components/clinical/OutcomesPanel";` and render `<OutcomesPanel />` directly above the existing `<RoiCalculator />` (line ~40). Then update `RoiCalculator` to per-bed pricing: inside the component (it already has `const [beds, setBeds] = useState(300)`), add

```tsx
  const PRICE_PER_BED_MONTH = 12; // USD — mid-point of $8–15/bed/month
  const annualPlatformCost = beds * PRICE_PER_BED_MONTH * 12;
```

and add a line to the results section showing the platform cost and net ROI:

```tsx
  <div className="text-sm text-slate-600 mt-2">
    Platform cost: <span className="font-mono font-semibold">${annualPlatformCost.toLocaleString()}/yr</span>
    {" "}(${PRICE_PER_BED_MONTH}/bed/month × {beds} beds)
  </div>
```

If the calculator displays estimated savings, add net = savings − cost beneath it using the same styling; keep all existing inputs.
- `AppShell.tsx`: add `import { DemoBadge } from "@/components/core/DemoBadge";` and render `<DemoBadge />` in the header bar next to the app title/logo.

- [ ] **Step 6: Verify** — `npm run lint` && `npm test` → clean/green. In the app: case manager sees the seeded red-flag escalation and can resolve it with notes; clinician dashboard shows role-filtered tasks; admin dashboard shows outcomes + per-bed pricing; the demo badge shows in the header.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/components/clinical/EscalationQueue.tsx frontend/src/components/clinical/MyTasksWidget.tsx frontend/src/components/clinical/OutcomesPanel.tsx frontend/src/components/core/DemoBadge.tsx frontend/src/pages/CaseManagerDashboard.tsx frontend/src/pages/ClinicianDashboard.tsx frontend/src/pages/AdminDashboard.tsx frontend/src/components/AppShell.tsx
git commit -m "feat(frontend): escalation queue, my-tasks widget, outcomes panel, demo badge, per-bed ROI"
```

---

### Task 13: Full verification + demo walkthrough

- [ ] **Step 1: Backend gates**

```powershell
cd backend
py -m ruff check app/ scripts/
py -m pytest
```
Expected: lint clean, all tests pass.

- [ ] **Step 2: Frontend gates**

```powershell
cd frontend
npm run lint
npm test
npm run build
```
Expected: all clean/green.

- [ ] **Step 3: End-to-end demo loop** (all three services running, fresh `dev.db`)

1. Log in as physician → `/ward` shows the grouped board with seeded plans.
2. Pick an unplanned patient → "Start discharge planning" → row moves to *on track* with open-task chip.
3. Open the patient → Transition tab → tick all tasks → "Confirm discharge" → 4 check-ins appear as `scheduled`.
4. Seeded discharged patient: simulated phone shows the day-2 message; type "chest pain" → RED FLAG + escalation.
5. Log in as case manager → escalation queue shows the red flag → resolve with notes.
6. Log in as admin → outcomes panel shows discharges tracked / response rate; ROI shows per-bed pricing.
7. Header shows the demo-mode badge throughout.

- [ ] **Step 4: Commit any fixes, then final commit**

```bash
git add -A
git commit -m "chore(transitions): verification fixes for care transitions v1"
```

---

## Self-review checklist (run after writing, fixed inline)

1. **Spec coverage:** board ✅ (T10), checklists from risk factors ✅ (T3/T5/T11), WhatsApp check-ins bilingual ✅ (T4), escalation queue ✅ (T6/T12), outcomes loop ✅ (T7/T12), simulated provider + demo badge ✅ (T4/T12), send-retry/no-response/opt-out/unknown-sender/idempotency ✅ (T4/T7), ML-service-down default tasks ✅ (T3), CSV import ✅ (T8), per-bed ROI ✅ (T12). `/retrain` feed: outcomes are recorded as new `Admission` + `ReadmissionEvent` rows — the existing retrain path reads admissions, no change needed.
2. **Placeholder scan:** clean — no TBDs, no "similar to Task N", every code step shows the code.
3. **Type consistency:** `PlanRead.tasks: list[TaskRead]` matches frontend `TransitionPlan.tasks: TransitionTask[]`; `simulate-reply` returns `ResponseRead` matching `CheckinResponseItem`; board row fields match across T5/T9/T10; `groupForRow(row, today)` signature consistent in T9 test and T10 usage.
