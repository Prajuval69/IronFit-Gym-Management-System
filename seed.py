"""
seed.py — Seed Initial Data into PostgreSQL
============================================
This script inserts the default plans and sample memberships that
were previously hard-coded as Python lists in main.py.

Run ONCE after creating the database:
    python seed.py

It is safe to run multiple times — it skips rows that already exist.

WHY A SEPARATE SEED SCRIPT?
  • Keeps main.py clean — no startup data logic in the web server.
  • Can be re-run in CI/CD to reset a test database.
  • Easy to extend with more seed data later.
"""

import json
import sys
import os

# Allow running from the project root: python seed.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine, Base
from app import models

# Create all tables (safe to call even if tables already exist)
Base.metadata.create_all(bind=engine)


def seed():
    db = SessionLocal()
    try:
        # ── 1. Seed Plans ────────────────────────────────────────────────────
        default_plans = [
            {"id": 1, "name": "Basic",    "duration_months": 1,  "price": 500,  "includes_classes": False, "includes_trainer": False},
            {"id": 2, "name": "Standard", "duration_months": 3,  "price": 1200, "includes_classes": True,  "includes_trainer": False},
            {"id": 3, "name": "Premium",  "duration_months": 6,  "price": 2000, "includes_classes": True,  "includes_trainer": False},
            {"id": 4, "name": "Elite",    "duration_months": 12, "price": 3500, "includes_classes": True,  "includes_trainer": True},
            {"id": 5, "name": "Trial",    "duration_months": 1,  "price": 300,  "includes_classes": False, "includes_trainer": False},
        ]

        plans_added = 0
        for p in default_plans:
            exists = db.query(models.Plan).filter(models.Plan.id == p["id"]).first()
            if not exists:
                db.add(models.Plan(**p))
                plans_added += 1

        db.commit()
        print(f"✅ Plans seeded: {plans_added} new rows ({len(default_plans) - plans_added} already existed)")

        # ── 2. Seed Sample Memberships ───────────────────────────────────────
        seed_memberships = [
            {
                "membership_id": 1, "member_name": "Aarav Sharma",  "phone": "9876543210",
                "plan_id": 3, "plan_name": "Premium",  "duration_months": 6,
                "start_month": "January",  "payment_mode": "cash", "referral_code": "",
                "monthly_equivalent": 200.0, "total_fee": 1800.0, "status": "active",
                "includes_classes": True,  "includes_trainer": False,
                "fee_breakdown": json.dumps({"base_price": 2000, "duration_discount": "10%",
                    "discount_label": "10% discount (6+ months)", "referral_discount": 0.0,
                    "processing_fee": 0, "total_fee": 1800.0}),
            },
            {
                "membership_id": 2, "member_name": "Priya Mehta",   "phone": "9123456780",
                "plan_id": 4, "plan_name": "Elite",    "duration_months": 12,
                "start_month": "February", "payment_mode": "emi",  "referral_code": "REF123",
                "monthly_equivalent": 280.0, "total_fee": 3360.0, "status": "active",
                "includes_classes": True,  "includes_trainer": True,
                "fee_breakdown": json.dumps({"base_price": 3500, "duration_discount": "20%",
                    "discount_label": "20% discount (12+ months)", "referral_discount": 140.0,
                    "processing_fee": 200, "total_fee": 3360.0}),
            },
            {
                "membership_id": 3, "member_name": "Rohan Verma",   "phone": "9988776655",
                "plan_id": 1, "plan_name": "Basic",    "duration_months": 1,
                "start_month": "March",    "payment_mode": "cash", "referral_code": "",
                "monthly_equivalent": 500.0, "total_fee": 500.0,  "status": "frozen",
                "includes_classes": False, "includes_trainer": False,
                "fee_breakdown": json.dumps({"base_price": 500, "duration_discount": "0%",
                    "discount_label": "No discount", "referral_discount": 0.0,
                    "processing_fee": 0, "total_fee": 500.0}),
            },
            {
                "membership_id": 4, "member_name": "Sneha Patel",   "phone": "8877665544",
                "plan_id": 2, "plan_name": "Standard", "duration_months": 3,
                "start_month": "April",    "payment_mode": "cash", "referral_code": "SAVE5",
                "monthly_equivalent": 380.0, "total_fee": 1140.0, "status": "active",
                "includes_classes": True,  "includes_trainer": False,
                "fee_breakdown": json.dumps({"base_price": 1200, "duration_discount": "0%",
                    "discount_label": "No discount", "referral_discount": 60.0,
                    "processing_fee": 0, "total_fee": 1140.0}),
            },
            {
                "membership_id": 5, "member_name": "Kiran Reddy",   "phone": "7766554433",
                "plan_id": 4, "plan_name": "Elite",    "duration_months": 12,
                "start_month": "January",  "payment_mode": "emi",  "referral_code": "",
                "monthly_equivalent": 308.0, "total_fee": 3700.0, "status": "active",
                "includes_classes": True,  "includes_trainer": True,
                "fee_breakdown": json.dumps({"base_price": 3500, "duration_discount": "20%",
                    "discount_label": "20% discount (12+ months)", "referral_discount": 0.0,
                    "processing_fee": 200, "total_fee": 3700.0}),
            },
            {
                "membership_id": 6, "member_name": "Meena Iyer",    "phone": "6655443322",
                "plan_id": 3, "plan_name": "Premium",  "duration_months": 6,
                "start_month": "March",    "payment_mode": "cash", "referral_code": "REF123",
                "monthly_equivalent": 190.0, "total_fee": 1140.0, "status": "active",
                "includes_classes": True,  "includes_trainer": False,
                "fee_breakdown": json.dumps({"base_price": 2000, "duration_discount": "10%",
                    "discount_label": "10% discount (6+ months)", "referral_discount": 90.0,
                    "processing_fee": 0, "total_fee": 1140.0}),
            },
        ]

        memberships_added = 0
        for m_data in seed_memberships:
            exists = db.query(models.Membership).filter(
                models.Membership.membership_id == m_data["membership_id"]
            ).first()
            if not exists:
                db.add(models.Membership(**m_data))
                memberships_added += 1

        db.commit()
        print(f"✅ Memberships seeded: {memberships_added} new rows ({len(seed_memberships) - memberships_added} already existed)")
        print("\n🎉 Database seeding complete! You can now start the server.")

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
