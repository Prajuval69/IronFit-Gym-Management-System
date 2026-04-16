"""
schemas.py — Pydantic Schemas (Request & Response Validation)
==============================================================
Pydantic schemas serve two purposes:

  1. REQUEST schemas  — validate incoming JSON from the client.
     FastAPI uses these automatically; invalid data returns HTTP 422.

  2. RESPONSE schemas — declare the shape of data returned by the API.
     Using orm_mode = True (Pydantic v1) / from_attributes = True (v2)
     allows Pydantic to read data directly from SQLAlchemy ORM objects
     instead of requiring plain dicts.

WHY SEPARATE schemas.py from models.py?
  models.py = database layer (SQLAlchemy, talks to PostgreSQL)
  schemas.py = API layer    (Pydantic, talks to HTTP clients)
  Keeping them separate means you can expose only the fields you want
  (e.g. hide internal DB columns) and validate input independently of
  the DB schema — a standard industry pattern.

VALIDATION RULES (same as original):
  member_name  : min 2 characters
  plan_id      : must be > 0
  phone        : min 10 characters  → 5-digit phone → 422 Unprocessable Entity
  start_month  : min 3 characters
  plan name    : min 2 characters
  duration, price : must be > 0
"""

from pydantic import BaseModel, Field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# PLAN SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class NewPlan(BaseModel):
    """
    REQUEST body for POST /plans (create a new plan).
    Pydantic will reject any request that violates these constraints
    and return HTTP 422 automatically — no manual if-checks needed.
    """
    name:             str  = Field(..., min_length=2, example="Diamond")
    duration_months:  int  = Field(..., gt=0,         example=6)
    price:            int  = Field(..., gt=0,         example=2500)
    includes_classes: bool = Field(default=False)
    includes_trainer: bool = Field(default=False)


class PlanOut(BaseModel):
    """
    RESPONSE schema for a single plan.
    orm_mode / from_attributes lets us pass a SQLAlchemy Plan object
    directly and Pydantic will extract the fields automatically.
    """
    id:               int
    name:             str
    duration_months:  int
    price:            int
    includes_classes: bool
    includes_trainer: bool

    class Config:
        from_attributes = True   # Pydantic v2 (replaces orm_mode = True)


# ─────────────────────────────────────────────────────────────────────────────
# MEMBERSHIP SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class EnrollRequest(BaseModel):
    """
    REQUEST body for POST /memberships (enrol a member).
    Identical constraints to the original in-memory version.
    """
    member_name:   str = Field(..., min_length=2,  example="Aarav Sharma")
    plan_id:       int = Field(..., gt=0,           example=3)
    phone:         str = Field(..., min_length=10,  example="9876543210")
    start_month:   str = Field(..., min_length=3,   example="July")
    payment_mode:  str = Field(default="cash",      example="cash")
    referral_code: str = Field(default="",          example="REF123")


# ─────────────────────────────────────────────────────────────────────────────
# CLASS BOOKING SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class ClassBookRequest(BaseModel):
    """
    REQUEST body for POST /classes/book.
    class_date should be in YYYY-MM-DD format (validated by the route).
    """
    member_name: str = Field(..., example="Aarav Sharma")
    class_name:  str = Field(..., example="Zumba")
    class_date:  str = Field(..., example="2024-08-10")
