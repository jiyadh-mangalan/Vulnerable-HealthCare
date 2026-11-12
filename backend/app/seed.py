"""Seed demo users documented in README (idempotent)."""

from sqlalchemy.orm import Session

from . import models
from .database import SessionLocal
from .vulnerable_utils import weak_hash_password


def seed_demo_users() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(models.User).filter(models.User.email == "admin@healthcare.com").first():
            return

        admin = models.User(
            email="admin@healthcare.com",
            full_name="System Administrator",
            hashed_password=weak_hash_password("admin123"),
            role=models.RoleEnum.ADMIN,
        )
        doctor_user = models.User(
            email="drsmith@healthcare.com",
            full_name="Dr. John Smith",
            hashed_password=weak_hash_password("doctor123"),
            role=models.RoleEnum.DOCTOR,
        )
        patient_user = models.User(
            email="jdoe@healthcare.com",
            full_name="Jane Doe",
            hashed_password=weak_hash_password("patient123"),
            role=models.RoleEnum.PATIENT,
        )
        db.add_all([admin, doctor_user, patient_user])
        db.flush()

        db.add(
            models.Doctor(
                user_id=doctor_user.id,
                specialty="General Practice",
                license_number="MD-10001",
            )
        )
        db.add(
            models.Patient(
                user_id=patient_user.id,
            )
        )
        db.commit()
    finally:
        db.close()
