"""Baseline schema — all CareInsight tables.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-12
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enums
    role_name = sa.Enum(
        "admin", "physician", "resident", "nurse", "case_manager", "analyst",
        name="role_name",
    )
    intervention_status = sa.Enum(
        "planned", "completed", "declined", "not_applicable",
        name="intervention_status",
    )
    role_name.create(op.get_bind(), checkfirst=True)
    intervention_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "hospitals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False, unique=True),
        sa.Column("ehr_vendor", sa.String(40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("hospital_id", "code", name="uq_dept_hospital_code"),
    )

    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", role_name, nullable=False, unique=True),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("hospital_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mrn", sa.String(40), nullable=False),
        sa.Column("first_name", sa.String(120), nullable=False),
        sa.Column("last_name", sa.String(120), nullable=False),
        sa.Column("dob", sa.Date, nullable=False),
        sa.Column("sex", sa.String(20), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("hospital_id", "mrn", name="uq_patient_hospital_mrn"),
    )
    op.create_index("ix_patients_hospital_id", "patients", ["hospital_id"])

    op.create_table(
        "admissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("department_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("departments.id"), nullable=False),
        sa.Column("admission_type", sa.String(40), nullable=False),
        sa.Column("admitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("discharged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("length_of_stay", sa.Float, nullable=True),
        sa.Column("clinical_features", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_admissions_patient_id", "admissions", ["patient_id"])
    op.create_index("ix_admissions_department_admitted", "admissions",
                    ["department_id", "admitted_at"])

    op.create_table(
        "model_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("algorithm", sa.String(40), nullable=False),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cv_auc", sa.Float, nullable=True),
        sa.Column("test_auc", sa.Float, nullable=True),
        sa.Column("artifact_uri", sa.String(400), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", "version", name="uq_model_name_version"),
    )
    op.create_index(
        "uq_model_one_active", "model_versions", ["is_active"],
        unique=True, postgresql_where=sa.text("is_active = true"),
    )

    op.create_table(
        "predictions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("admissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("model_version_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("model_versions.id"), nullable=False),
        sa.Column("probability", sa.Float, nullable=False),
        sa.Column("risk_tier", sa.String(20), nullable=False),
        sa.Column("threshold_used", sa.Float, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_predictions_admission_id", "predictions", ["admission_id"])
    op.create_index("ix_predictions_model_version_id", "predictions", ["model_version_id"])

    op.create_table(
        "risk_factors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("feature_name", sa.String(120), nullable=False),
        sa.Column("humanized_label", sa.String(255), nullable=False),
        sa.Column("shap_value", sa.Float, nullable=False),
        sa.Column("rank", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_risk_factors_prediction_id", "risk_factors", ["prediction_id"])
    op.create_index("ix_risk_factor_prediction_rank", "risk_factors", ["prediction_id", "rank"])

    op.create_table(
        "recommendations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.String(500), nullable=False),
        sa.Column("category", sa.String(80), nullable=True),
        sa.Column("source", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_recommendations_prediction_id", "recommendations", ["prediction_id"])

    op.create_table(
        "interventions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("admission_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("admissions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("recommendations.id"), nullable=True),
        sa.Column("recorded_by_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", intervention_status, nullable=False),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_interventions_admission_id", "interventions", ["admission_id"])
    op.create_index("ix_interventions_recorded_by", "interventions", ["recorded_by_user_id"])

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("prediction_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("predictions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("generated_by_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("pdf_uri", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_reports_prediction_id", "reports", ["prediction_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=True),
        sa.Column("action", sa.String(40), nullable=False),
        sa.Column("resource_type", sa.String(60), nullable=True),
        sa.Column("resource_id", sa.String(80), nullable=True),
        sa.Column("request_ip", sa.String(60), nullable=True),
        sa.Column("payload", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_resource", "audit_logs", ["resource_type", "resource_id"])
    op.create_index("ix_audit_created_at", "audit_logs", ["created_at"])

    op.create_table(
        "consent_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("consent_type", sa.String(60), nullable=False),
        sa.Column("granted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_consent_records_patient_id", "consent_records", ["patient_id"])


def downgrade() -> None:
    op.drop_table("consent_records")
    op.drop_table("audit_logs")
    op.drop_table("reports")
    op.drop_table("interventions")
    op.drop_table("recommendations")
    op.drop_table("risk_factors")
    op.drop_table("predictions")
    op.drop_table("model_versions")
    op.drop_table("admissions")
    op.drop_table("patients")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_table("departments")
    op.drop_table("hospitals")
    sa.Enum(name="intervention_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="role_name").drop(op.get_bind(), checkfirst=True)
