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
