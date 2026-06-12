"""Import all ORM models so Alembic autogenerate sees them."""
from app.models.hospital import Department, Hospital  # noqa: F401
from app.models.user import Role, RoleName, User  # noqa: F401
from app.models.patient import Admission, Patient  # noqa: F401
from app.models.prediction import (  # noqa: F401
    ModelVersion,
    Prediction,
    Recommendation,
    RiskFactor,
)
from app.models.intervention import Intervention, InterventionStatus  # noqa: F401
from app.models.report import Report  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
from app.models.consent import ConsentRecord  # noqa: F401
