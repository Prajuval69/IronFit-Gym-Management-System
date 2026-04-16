"""
models.py — SQLAlchemy ORM Models (Database Tables)
=====================================================
Each class here maps to a PostgreSQL table.

WHAT IS AN ORM MODEL?
  An ORM (Object-Relational Mapper) model lets you work with database rows
  as Python objects instead of writing raw SQL.  SQLAlchemy translates your
  Python code into SQL automatically.

  Example:
    Instead of:  INSERT INTO plans (name, price ...) VALUES (...)
    You write:   db.add(Plan(name="Basic", price=500, ...))

TABLE RELATIONSHIPS:
  Plan ──< Membership   (one plan → many memberships, linked by plan_id)
  Membership ──< ClassBooking (one membership → many bookings)

  These are represented by ForeignKey columns and relationship() helpers.
  relationship() lets you do  plan.memberships  to get all memberships for
  a plan — without writing a JOIN query.

WHY STORE fee_breakdown AS TEXT?
  fee_breakdown is a Python dict (nested object). PostgreSQL doesn't have
  a native "dict" type, so we serialise it to a JSON string with json.dumps
  and deserialise it on read with json.loads — handled in crud.py.
"""

import json
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from app.database import Base


class Plan(Base):
    """
    Represents the 'plans' table.
    Columns mirror the original in-memory dict structure exactly so
    that all existing API responses stay identical.
    """
    __tablename__ = "plans"

    id                = Column(Integer, primary_key=True, index=True)
    name              = Column(String(100), unique=True, nullable=False)
    duration_months   = Column(Integer, nullable=False)
    price             = Column(Integer, nullable=False)
    includes_classes  = Column(Boolean, default=False, nullable=False)
    includes_trainer  = Column(Boolean, default=False, nullable=False)

    # One plan → many memberships
    # cascade="all, delete-orphan": deleting a plan also deletes its memberships
    # (guarded by the API 400 check before it ever reaches here)
    memberships = relationship("Membership", back_populates="plan")


class Membership(Base):
    """
    Represents the 'memberships' table.
    Stores enrolment records + computed fee fields.
    """
    __tablename__ = "memberships"

    membership_id      = Column(Integer, primary_key=True, index=True)
    member_name        = Column(String(150), nullable=False)
    phone              = Column(String(20),  nullable=False)
    plan_id            = Column(Integer, ForeignKey("plans.id"), nullable=False)
    plan_name          = Column(String(100), nullable=False)
    duration_months    = Column(Integer,  nullable=False)
    start_month        = Column(String(20),  nullable=False)
    payment_mode       = Column(String(20),  nullable=False, default="cash")
    referral_code      = Column(String(50),  nullable=False, default="")
    monthly_equivalent = Column(Float,   nullable=False)
    fee_breakdown      = Column(Text,    nullable=True)   # JSON string
    total_fee          = Column(Float,   nullable=False)
    status             = Column(String(20),  nullable=False, default="active")
    includes_classes   = Column(Boolean, nullable=False, default=False)
    includes_trainer   = Column(Boolean, nullable=False, default=False)

    # Many-to-one: each membership belongs to one plan
    plan = relationship("Plan", back_populates="memberships")

    # One membership → many class bookings
    bookings = relationship("ClassBooking", back_populates="membership")

    def to_dict(self) -> dict:
        """
        Convert ORM row to a plain Python dict that matches the original
        in-memory membership dict format 100%.  API responses stay identical.
        fee_breakdown is deserialised from JSON text back to a dict.
        """
        return {
            "membership_id":      self.membership_id,
            "member_name":        self.member_name,
            "phone":              self.phone,
            "plan_id":            self.plan_id,
            "plan_name":          self.plan_name,
            "duration_months":    self.duration_months,
            "start_month":        self.start_month,
            "payment_mode":       self.payment_mode,
            "referral_code":      self.referral_code,
            "monthly_equivalent": self.monthly_equivalent,
            "fee_breakdown":      json.loads(self.fee_breakdown) if self.fee_breakdown else {},
            "total_fee":          self.total_fee,
            "status":             self.status,
            "includes_classes":   self.includes_classes,
            "includes_trainer":   self.includes_trainer,
        }


class ClassBooking(Base):
    """
    Represents the 'class_bookings' table.
    Stores individual class bookings tied to a membership.
    """
    __tablename__ = "class_bookings"

    booking_id    = Column(Integer, primary_key=True, index=True)
    member_name   = Column(String(150), nullable=False)
    class_name    = Column(String(100), nullable=False)
    class_date    = Column(String(20),  nullable=False)   # stored as "YYYY-MM-DD" string
    membership_id = Column(Integer, ForeignKey("memberships.membership_id"), nullable=False)
    status        = Column(String(20), nullable=False, default="booked")

    # Many-to-one: each booking belongs to one membership
    membership = relationship("Membership", back_populates="bookings")

    def to_dict(self) -> dict:
        """Convert ORM row to dict matching original booking dict format."""
        return {
            "booking_id":    self.booking_id,
            "member_name":   self.member_name,
            "class_name":    self.class_name,
            "class_date":    self.class_date,
            "membership_id": self.membership_id,
            "status":        self.status,
        }
