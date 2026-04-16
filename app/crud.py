"""
crud.py — Database Operations (Create, Read, Update, Delete)
=============================================================
WHAT IS crud.py?
  This file contains every function that talks to the database.
  Routes in main.py call these functions instead of manipulating lists.

  This separation is called the "Repository Pattern" — it keeps routes
  thin and all DB logic testable in one place.

WHY NOT PUT DB QUERIES DIRECTLY IN ROUTES?
  • Easier to unit-test — mock crud functions, not FastAPI routes.
  • Reusable — multiple routes can call the same DB function.
  • Cleaner routes — routes only do HTTP logic, not SQL logic.

HOW db.commit() AND db.refresh() WORK:
  db.add(obj)     — stages the object (like git add)
  db.commit()     — writes it to the database (like git commit)
  db.refresh(obj) — re-reads the row from the DB so auto-generated
                    fields (id, defaults) are populated in the Python
                    object — critical after INSERT.

PANDAS INTEGRATION:
  Analytics functions use pd.read_sql() to load query results into a
  DataFrame.  This is far more efficient than loading all rows and then
  converting — SQLAlchemy runs the SQL, Pandas reads the result set.
"""

import json
import math
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from app import models


# ─────────────────────────────────────────────────────────────────────────────
# HELPER: fee calculation (unchanged from original)
# ─────────────────────────────────────────────────────────────────────────────

def calculate_membership_fee(base_price: int, duration_months: int,
                              payment_mode: str, referral_code: str = "") -> dict:
    """
    Pure Python helper — no DB access needed.
    Computes the final fee with duration discounts, referral, and EMI fee.
    Kept identical to original so all fee logic is preserved.
    """
    discount_pct   = 0
    discount_label = "No discount"

    if duration_months >= 12:
        discount_pct   = 20
        discount_label = "20% discount (12+ months)"
    elif duration_months >= 6:
        discount_pct   = 10
        discount_label = "10% discount (6+ months)"

    after_duration    = base_price * (1 - discount_pct / 100)
    referral_discount = 0.0
    if referral_code.strip():
        referral_discount = after_duration * 0.05
        after_duration   -= referral_discount

    processing_fee = 200 if payment_mode == "emi" else 0
    total_fee      = after_duration + processing_fee

    return {
        "base_price":        base_price,
        "duration_discount": f"{discount_pct}%",
        "discount_label":    discount_label,
        "referral_discount": round(referral_discount, 2),
        "processing_fee":    processing_fee,
        "total_fee":         round(total_fee, 2),
    }


# ─────────────────────────────────────────────────────────────────────────────
# PLANS — CRUD
# ─────────────────────────────────────────────────────────────────────────────

def get_all_plans(db: Session) -> list[models.Plan]:
    """Return all plans ordered by id."""
    return db.query(models.Plan).order_by(models.Plan.id).all()


def get_plan_by_id(db: Session, plan_id: int) -> Optional[models.Plan]:
    """Return a single Plan or None if not found."""
    return db.query(models.Plan).filter(models.Plan.id == plan_id).first()


def get_plan_by_name(db: Session, name: str) -> Optional[models.Plan]:
    """Case-insensitive lookup to detect duplicates on create."""
    return (
        db.query(models.Plan)
        .filter(models.Plan.name.ilike(name))   # ilike = case-insensitive LIKE
        .first()
    )


def create_plan(db: Session, plan_data) -> models.Plan:
    """
    Insert a new Plan row.
    Steps:
      1. Build the ORM object.
      2. db.add() — stage it.
      3. db.commit() — write to DB.
      4. db.refresh() — reload from DB so .id is populated.
    """
    plan = models.Plan(
        name             = plan_data.name,
        duration_months  = plan_data.duration_months,
        price            = plan_data.price,
        includes_classes = plan_data.includes_classes,
        includes_trainer = plan_data.includes_trainer,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)   # ← CRITICAL: populates plan.id
    return plan


def update_plan(db: Session, plan_id: int,
                price: Optional[int] = None,
                includes_classes: Optional[bool] = None,
                includes_trainer: Optional[bool] = None) -> Optional[models.Plan]:
    """
    Partial update — only change fields that are not None.
    Pattern: fetch → modify in Python → commit (SQLAlchemy detects the change).
    """
    plan = get_plan_by_id(db, plan_id)
    if not plan:
        return None
    if price            is not None: plan.price            = price
    if includes_classes is not None: plan.includes_classes = includes_classes
    if includes_trainer is not None: plan.includes_trainer = includes_trainer
    db.commit()
    db.refresh(plan)
    return plan


def delete_plan(db: Session, plan_id: int) -> Optional[models.Plan]:
    """
    Delete a plan row.
    Returns the plan object (for the response message) or None if not found.
    The calling route checks for active memberships BEFORE calling this.
    """
    plan = get_plan_by_id(db, plan_id)
    if not plan:
        return None
    db.delete(plan)
    db.commit()
    return plan


def has_active_memberships(db: Session, plan_id: int) -> int:
    """Return count of active memberships for a plan (used in DELETE guard)."""
    return (
        db.query(models.Membership)
        .filter(
            models.Membership.plan_id == plan_id,
            models.Membership.status  == "active",
        )
        .count()
    )


def filter_plans(db: Session,
                 max_price:        Optional[int]  = None,
                 max_duration:     Optional[int]  = None,
                 includes_classes: Optional[bool] = None,
                 includes_trainer: Optional[bool] = None) -> list[models.Plan]:
    """
    Dynamic filtering — each filter is applied only when the param is not None.
    This avoids adding unnecessary WHERE clauses for params the caller didn't supply.
    """
    query = db.query(models.Plan)
    if max_price       is not None: query = query.filter(models.Plan.price           <= max_price)
    if max_duration    is not None: query = query.filter(models.Plan.duration_months <= max_duration)
    if includes_classes is not None: query = query.filter(models.Plan.includes_classes == includes_classes)
    if includes_trainer is not None: query = query.filter(models.Plan.includes_trainer == includes_trainer)
    return query.order_by(models.Plan.id).all()


def plan_to_dict(plan: models.Plan) -> dict:
    """Convert a Plan ORM object to a plain dict (matches original list format)."""
    return {
        "id":               plan.id,
        "name":             plan.name,
        "duration_months":  plan.duration_months,
        "price":            plan.price,
        "includes_classes": plan.includes_classes,
        "includes_trainer": plan.includes_trainer,
    }


# ─────────────────────────────────────────────────────────────────────────────
# MEMBERSHIPS — CRUD
# ─────────────────────────────────────────────────────────────────────────────

def get_all_memberships(db: Session) -> list[models.Membership]:
    return db.query(models.Membership).order_by(models.Membership.membership_id).all()


def get_membership_by_id(db: Session, membership_id: int) -> Optional[models.Membership]:
    return (
        db.query(models.Membership)
        .filter(models.Membership.membership_id == membership_id)
        .first()
    )


def create_membership(db: Session, request, plan: models.Plan) -> models.Membership:
    """
    Enrol a member.
    1. Calculate fee using the helper.
    2. Serialise fee_breakdown dict to JSON text for storage.
    3. Insert row and refresh to get auto-generated membership_id.
    """
    fee_details        = calculate_membership_fee(
        plan.price, plan.duration_months, request.payment_mode, request.referral_code
    )
    monthly_equivalent = round(fee_details["total_fee"] / plan.duration_months, 2)

    membership = models.Membership(
        member_name        = request.member_name,
        phone              = request.phone,
        plan_id            = plan.id,
        plan_name          = plan.name,
        duration_months    = plan.duration_months,
        start_month        = request.start_month,
        payment_mode       = request.payment_mode,
        referral_code      = request.referral_code,
        monthly_equivalent = monthly_equivalent,
        fee_breakdown      = json.dumps(fee_details),   # dict → JSON string
        total_fee          = fee_details["total_fee"],
        status             = "active",
        includes_classes   = plan.includes_classes,
        includes_trainer   = plan.includes_trainer,
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    return membership


def set_membership_status(db: Session, membership_id: int, status: str) -> Optional[models.Membership]:
    """Shared helper for freeze and reactivate."""
    m = get_membership_by_id(db, membership_id)
    if not m:
        return None
    m.status = status
    db.commit()
    db.refresh(m)
    return m


def search_memberships(db: Session, member_name: str) -> list[models.Membership]:
    """Case-insensitive substring search on member_name."""
    return (
        db.query(models.Membership)
        .filter(models.Membership.member_name.ilike(f"%{member_name}%"))
        .all()
    )


def sort_memberships(db: Session, sort_by: str, order: str) -> list[models.Membership]:
    """Sort memberships by total_fee or duration_months."""
    col   = getattr(models.Membership, sort_by)
    col   = col.desc() if order == "desc" else col.asc()
    return db.query(models.Membership).order_by(col).all()


def paginate_memberships(db: Session, page: int, limit: int):
    """Return one page of memberships and pagination metadata."""
    total       = db.query(models.Membership).count()
    total_pages = max(1, math.ceil(total / limit))
    offset      = (page - 1) * limit
    items       = (
        db.query(models.Membership)
        .order_by(models.Membership.membership_id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return total, total_pages, items


# ─────────────────────────────────────────────────────────────────────────────
# CLASS BOOKINGS — CRUD
# ─────────────────────────────────────────────────────────────────────────────

def get_active_membership_with_classes(db: Session, member_name: str) -> Optional[models.Membership]:
    """
    Find an active membership for a member that includes classes.
    Used by the book_class route to gate access.
    """
    return (
        db.query(models.Membership)
        .filter(
            models.Membership.member_name.ilike(member_name),
            models.Membership.status          == "active",
            models.Membership.includes_classes == True,
        )
        .first()
    )


def create_booking(db: Session, request, membership_id: int) -> models.ClassBooking:
    booking = models.ClassBooking(
        member_name   = request.member_name,
        class_name    = request.class_name,
        class_date    = request.class_date,
        membership_id = membership_id,
        status        = "booked",
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_all_bookings(db: Session) -> list[models.ClassBooking]:
    return db.query(models.ClassBooking).order_by(models.ClassBooking.booking_id).all()


def get_booking_by_id(db: Session, booking_id: int) -> Optional[models.ClassBooking]:
    return (
        db.query(models.ClassBooking)
        .filter(models.ClassBooking.booking_id == booking_id)
        .first()
    )


def delete_booking(db: Session, booking_id: int) -> Optional[models.ClassBooking]:
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        return None
    db.delete(booking)
    db.commit()
    return booking


# ─────────────────────────────────────────────────────────────────────────────
# DATA ENGINEERING — Pandas helpers
# ─────────────────────────────────────────────────────────────────────────────

def load_memberships_df(db: Session) -> pd.DataFrame:
    """
    Load ALL membership rows into a Pandas DataFrame.

    WHY pd.read_sql()?
      pd.read_sql() executes the SQL query and streams results directly
      into a DataFrame — more efficient than fetching ORM objects and
      converting each one to a dict.

      query.statement  → the compiled SQL SELECT statement
      db.bind          → the engine (connection) to execute it against

    The resulting DataFrame has the same column names as the original
    in-memory list of dicts, so all existing analytics code works unchanged.
    """
    query = db.query(models.Membership)
    return pd.read_sql(query.statement, db.bind)


def load_plans_df(db: Session) -> pd.DataFrame:
    """Load all plan rows into a Pandas DataFrame."""
    query = db.query(models.Plan)
    return pd.read_sql(query.statement, db.bind)
