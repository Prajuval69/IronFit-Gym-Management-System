"""
main.py — FastAPI Routes (All Endpoints)
=========================================
IronFit Gym Management System — PostgreSQL Edition
Internship Project | Innomatics Research Labs

ARCHITECTURE:
  Frontend (HTML/JS)
      ↓  HTTP requests
  main.py  (FastAPI routes — HTTP layer only)
      ↓  calls
  crud.py  (DB operations — SQLAlchemy queries)
      ↓  reads/writes
  PostgreSQL  (persistent storage)
      ↓  raw data loaded into
  Pandas DataFrames  (analytics / DE layer)

WHAT CHANGED FROM THE IN-MEMORY VERSION:
  • Every function now receives  db: Session = Depends(get_db)
    → FastAPI injects a fresh DB session per request automatically.
  • List operations (append, remove, list comprehensions) are replaced
    by crud.py functions (create_plan, get_plan_by_id, etc.).
  • Analytics endpoints now call crud.load_memberships_df(db) and
    crud.load_plans_df(db) to get Pandas DataFrames from the DB.
  • All response formats are IDENTICAL to the original so the existing
    frontend works without any changes.

ROUTE ORDER RULE (unchanged):
  Fixed routes (/plans/summary, /plans/filter, etc.) MUST be declared
  BEFORE the variable route /plans/{plan_id} to avoid routing conflicts.
"""

import math
from datetime import date
from typing import Optional

import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app import crud, models
from app.database import Base, engine, get_db
from app.schemas import ClassBookRequest, EnrollRequest, NewPlan

# ── Create all tables on startup (safe if tables already exist) ──────────────
# In production you would use Alembic migrations instead, but for a
# portfolio project this is the simplest approach.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="IronFit Gym Management System",
    description=(
        "Gym Management REST API — FastAPI + PostgreSQL + Pandas. "
        "Demonstrates data engineering skills: ETL pipelines, "
        "analytics aggregations, SQL-style joins, data quality checks, "
        "and batch processing — all via REST microservices.\n\n"
        "**Storage**: PostgreSQL via SQLAlchemy ORM\n"
        "**Analytics**: Pandas DataFrames loaded from DB via pd.read_sql()"
    ),
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════════════
# GENERAL
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["General"])
def home():
    """Q1 — Welcome route"""
    return {"message": "Welcome to IronFit Gym"}


# ══════════════════════════════════════════════════════════════════════════════
# PLANS — fixed routes BEFORE /plans/{plan_id}
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/plans", tags=["Plans"])
def get_all_plans(db: Session = Depends(get_db)):
    """Q2 — All plans with total, min_price, max_price"""
    plans = crud.get_all_plans(db)
    if not plans:
        return {"total": 0, "min_price": None, "max_price": None, "plans": []}
    plans_list = [crud.plan_to_dict(p) for p in plans]
    prices     = [p["price"] for p in plans_list]
    return {
        "total":     len(plans_list),
        "min_price": min(prices),
        "max_price": max(prices),
        "plans":     plans_list,
    }


@app.get("/plans/summary", tags=["Plans"])
def plans_summary(db: Session = Depends(get_db)):
    """Q5 — Stats: totals, cheapest, most expensive"""
    plans = crud.get_all_plans(db)
    if not plans:
        raise HTTPException(status_code=404, detail="No plans found.")
    plans_list     = [crud.plan_to_dict(p) for p in plans]
    with_classes   = [p for p in plans_list if p["includes_classes"]]
    with_trainer   = [p for p in plans_list if p["includes_trainer"]]
    cheapest       = min(plans_list, key=lambda p: p["price"])
    most_expensive = max(plans_list, key=lambda p: p["price"])
    return {
        "total_plans":         len(plans_list),
        "plans_with_classes":  len(with_classes),
        "plans_with_trainer":  len(with_trainer),
        "cheapest_plan":       {"name": cheapest["name"],       "price": cheapest["price"]},
        "most_expensive_plan": {"name": most_expensive["name"], "price": most_expensive["price"]},
    }


@app.get("/plans/filter", tags=["Plans"])
def filter_plans(
    max_price:        Optional[int]  = Query(None),
    max_duration:     Optional[int]  = Query(None),
    includes_classes: Optional[bool] = Query(None),
    includes_trainer: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """Q10 — Filter plans with optional query params"""
    result = crud.filter_plans(db, max_price, max_duration, includes_classes, includes_trainer)
    if not result:
        raise HTTPException(status_code=404, detail="No plans match the given filters.")
    return {"total_found": len(result), "plans": [crud.plan_to_dict(p) for p in result]}


@app.get("/plans/search", tags=["Plans"])
def search_plans(keyword: str = Query(...), db: Session = Depends(get_db)):
    """Q16 — Keyword search; special keywords: 'classes', 'trainer'"""
    kw    = keyword.lower()
    plans = crud.get_all_plans(db)
    if kw == "classes":
        result = [p for p in plans if p.includes_classes]
    elif kw == "trainer":
        result = [p for p in plans if p.includes_trainer]
    else:
        result = [p for p in plans if kw in p.name.lower()]
    return {"keyword": keyword, "total_found": len(result), "plans": [crud.plan_to_dict(p) for p in result]}


@app.get("/plans/sort", tags=["Plans"])
def sort_plans(
    sort_by: str = Query("price", description="price | name | duration_months"),
    order:   str = Query("asc",   description="asc | desc"),
    db: Session = Depends(get_db),
):
    """Q17 — Sort plans"""
    valid = ["price", "name", "duration_months"]
    if sort_by not in valid:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid}")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="order must be 'asc' or 'desc'")
    plans      = crud.get_all_plans(db)
    plans_list = [crud.plan_to_dict(p) for p in plans]
    sorted_plans = sorted(plans_list, key=lambda p: p[sort_by], reverse=(order == "desc"))
    return {"sort_by": sort_by, "order": order, "plans": sorted_plans}


@app.get("/plans/page", tags=["Plans"])
def paginate_plans(
    page:  int = Query(1, ge=1),
    limit: int = Query(2, ge=1),
    db: Session = Depends(get_db),
):
    """Q18 — Paginate plans"""
    plans       = [crud.plan_to_dict(p) for p in crud.get_all_plans(db)]
    total       = len(plans)
    total_pages = max(1, math.ceil(total / limit))
    if page > total_pages:
        raise HTTPException(status_code=404, detail=f"Page {page} exceeds total pages ({total_pages}).")
    start = (page - 1) * limit
    return {
        "page": page, "limit": limit, "total": total,
        "total_pages": total_pages,
        "plans": plans[start: start + limit],
    }


@app.get("/plans/browse", tags=["Plans"])
def browse_plans(
    keyword:          Optional[str]  = Query(None),
    includes_classes: Optional[bool] = Query(None),
    includes_trainer: Optional[bool] = Query(None),
    sort_by:          str            = Query("price"),
    order:            str            = Query("asc"),
    page:             int            = Query(1, ge=1),
    limit:            int            = Query(2, ge=1),
    db: Session = Depends(get_db),
):
    """Q20 — Combined: keyword → filter → sort → paginate"""
    result = [crud.plan_to_dict(p) for p in crud.get_all_plans(db)]

    if keyword is not None:
        kw = keyword.lower()
        if kw == "classes":    result = [p for p in result if p["includes_classes"]]
        elif kw == "trainer":  result = [p for p in result if p["includes_trainer"]]
        else:                  result = [p for p in result if kw in p["name"].lower()]

    if includes_classes is not None:
        result = [p for p in result if p["includes_classes"] == includes_classes]
    if includes_trainer is not None:
        result = [p for p in result if p["includes_trainer"] == includes_trainer]
    if sort_by in ["price", "name", "duration_months"]:
        result = sorted(result, key=lambda p: p[sort_by], reverse=(order == "desc"))

    total       = len(result)
    total_pages = max(1, math.ceil(total / limit))
    start       = (page - 1) * limit
    return {
        "metadata": {
            "keyword": keyword, "includes_classes": includes_classes,
            "includes_trainer": includes_trainer, "sort_by": sort_by, "order": order,
            "page": page, "limit": limit, "total_results": total, "total_pages": total_pages,
        },
        "plans": result[start: start + limit],
    }


# ── Variable route LAST (after all fixed /plans/* routes) ────────────────────

@app.get("/plans/{plan_id}", tags=["Plans"])
def get_plan_by_id(plan_id: int, db: Session = Depends(get_db)):
    """Q3 — Get a single plan by ID"""
    plan = crud.get_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan with ID {plan_id} not found.")
    return crud.plan_to_dict(plan)


@app.post("/plans", tags=["Plans"], status_code=201)
def create_plan(new_plan: NewPlan, db: Session = Depends(get_db)):
    """Q11 — Create plan; reject duplicate names (201)"""
    if crud.get_plan_by_name(db, new_plan.name):
        raise HTTPException(status_code=400, detail=f"A plan named '{new_plan.name}' already exists.")
    plan = crud.create_plan(db, new_plan)
    return {"message": "Plan created successfully!", "plan": crud.plan_to_dict(plan)}


@app.put("/plans/{plan_id}", tags=["Plans"])
def update_plan(
    plan_id:          int,
    price:            Optional[int]  = Query(None),
    includes_classes: Optional[bool] = Query(None),
    includes_trainer: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """Q12 — Update plan fields via optional query params"""
    plan = crud.update_plan(db, plan_id, price, includes_classes, includes_trainer)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")
    return {"message": "Plan updated successfully!", "plan": crud.plan_to_dict(plan)}


@app.delete("/plans/{plan_id}", tags=["Plans"])
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    """Q13 — Delete plan; block if active memberships exist"""
    plan = crud.get_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found.")
    active_count = crud.has_active_memberships(db, plan_id)
    if active_count:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete '{plan.name}': {active_count} active membership(s) exist.",
        )
    crud.delete_plan(db, plan_id)
    return {"message": f"Plan '{plan.name}' deleted successfully."}


# ══════════════════════════════════════════════════════════════════════════════
# MEMBERSHIPS — fixed routes first, variable last
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/memberships/search", tags=["Memberships"])
def search_memberships(member_name: str = Query(...), db: Session = Depends(get_db)):
    """Q19 — Search memberships by member name"""
    result = crud.search_memberships(db, member_name)
    return {"total_found": len(result), "memberships": [m.to_dict() for m in result]}


@app.get("/memberships/sort", tags=["Memberships"])
def sort_memberships(
    sort_by: str = Query("total_fee", description="total_fee | duration_months"),
    order:   str = Query("asc"),
    db: Session = Depends(get_db),
):
    """Q19 — Sort memberships"""
    valid = ["total_fee", "duration_months"]
    if sort_by not in valid:
        raise HTTPException(status_code=400, detail=f"sort_by must be one of {valid}")
    result = crud.sort_memberships(db, sort_by, order)
    return {"sort_by": sort_by, "order": order, "memberships": [m.to_dict() for m in result]}


@app.get("/memberships/page", tags=["Memberships"])
def paginate_memberships(
    page:  int = Query(1, ge=1),
    limit: int = Query(2, ge=1),
    db: Session = Depends(get_db),
):
    """Q19 — Paginate memberships"""
    total, total_pages, items = crud.paginate_memberships(db, page, limit)
    return {
        "page": page, "limit": limit, "total": total,
        "total_pages": total_pages,
        "memberships": [m.to_dict() for m in items],
    }


@app.get("/memberships", tags=["Memberships"])
def get_all_memberships(db: Session = Depends(get_db)):
    """Q4 — Return all memberships and total"""
    memberships = crud.get_all_memberships(db)
    return {"total": len(memberships), "memberships": [m.to_dict() for m in memberships]}


@app.post("/memberships", tags=["Memberships"], status_code=201)
def enroll_member(request: EnrollRequest, db: Session = Depends(get_db)):
    """Q6/Q8/Q9 — Enroll member with fee calculation, discounts, referral, EMI"""
    plan = crud.get_plan_by_id(db, request.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan ID {request.plan_id} not found.")
    membership = crud.create_membership(db, request, plan)
    return {"message": "Membership enrolled successfully!", "membership": membership.to_dict()}


@app.put("/memberships/{membership_id}/freeze", tags=["Memberships"])
def freeze_membership(membership_id: int, db: Session = Depends(get_db)):
    """Q15 — Freeze (pause) a membership"""
    m = crud.get_membership_by_id(db, membership_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Membership {membership_id} not found.")
    if m.status == "frozen":
        raise HTTPException(status_code=400, detail="Membership is already frozen.")
    m = crud.set_membership_status(db, membership_id, "frozen")
    return {"message": "Membership frozen.", "membership": m.to_dict()}


@app.put("/memberships/{membership_id}/reactivate", tags=["Memberships"])
def reactivate_membership(membership_id: int, db: Session = Depends(get_db)):
    """Q15 — Reactivate a frozen membership"""
    m = crud.get_membership_by_id(db, membership_id)
    if not m:
        raise HTTPException(status_code=404, detail=f"Membership {membership_id} not found.")
    if m.status == "active":
        raise HTTPException(status_code=400, detail="Membership is already active.")
    m = crud.set_membership_status(db, membership_id, "active")
    return {"message": "Membership reactivated.", "membership": m.to_dict()}


# ══════════════════════════════════════════════════════════════════════════════
# CLASS BOOKINGS
# ══════════════════════════════════════════════════════════════════════════════

@app.post("/classes/book", tags=["Classes"], status_code=201)
def book_class(request: ClassBookRequest, db: Session = Depends(get_db)):
    """Q14 — Book class; member must have active membership with includes_classes=True"""
    active_membership = crud.get_active_membership_with_classes(db, request.member_name)
    if not active_membership:
        raise HTTPException(
            status_code=403,
            detail=f"'{request.member_name}' does not have an active membership that includes classes.",
        )
    booking = crud.create_booking(db, request, active_membership.membership_id)
    return {"message": "Class booked successfully!", "booking": booking.to_dict()}


@app.get("/classes/bookings", tags=["Classes"])
def get_class_bookings(db: Session = Depends(get_db)):
    """Q14 — List all class bookings"""
    bookings = crud.get_all_bookings(db)
    return {"total": len(bookings), "bookings": [b.to_dict() for b in bookings]}


@app.delete("/classes/cancel/{booking_id}", tags=["Classes"])
def cancel_class(booking_id: int, db: Session = Depends(get_db)):
    """Q15 — Cancel a class booking"""
    booking = crud.delete_booking(db, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail=f"Booking ID {booking_id} not found.")
    return {"message": f"Class booking {booking_id} cancelled successfully."}


# ══════════════════════════════════════════════════════════════════════════════
# DATA ENGINEERING EXTENSIONS
# All analytics now load from PostgreSQL via pd.read_sql()
# ══════════════════════════════════════════════════════════════════════════════

@app.get("/analytics/revenue", tags=["Data Engineering"])
def revenue_analytics(db: Session = Depends(get_db)):
    """
    DE-1: Pandas-based revenue analytics.
    Data source: PostgreSQL memberships table via pd.read_sql().
    All groupby / agg logic is unchanged from the original.
    """
    df = crud.load_memberships_df(db)
    if df.empty:
        raise HTTPException(status_code=404, detail="No membership data available for analysis.")

    revenue_by_plan = (
        df.groupby("plan_name")["total_fee"]
        .agg(["sum", "mean", "count"])
        .rename(columns={"sum": "total_revenue", "mean": "avg_fee", "count": "member_count"})
        .round(2)
        .reset_index()
        .to_dict(orient="records")
    )

    revenue_by_mode = (
        df.groupby("payment_mode")["total_fee"]
        .agg(["sum", "count"])
        .rename(columns={"sum": "total_revenue", "count": "transactions"})
        .round(2)
        .reset_index()
        .to_dict(orient="records")
    )

    stats = df["total_fee"].describe().round(2).to_dict()

    return {
        "summary": {
            "total_members":          len(df),
            "active_members":         int((df["status"] == "active").sum()),
            "total_revenue":          round(float(df["total_fee"].sum()), 2),
            "avg_revenue_per_member": round(float(df["total_fee"].mean()), 2),
        },
        "revenue_by_plan":         revenue_by_plan,
        "revenue_by_payment_mode": revenue_by_mode,
        "fee_distribution_stats":  stats,
    }


@app.get("/analytics/members-with-plans", tags=["Data Engineering"])
def members_with_plans(
    status: Optional[str] = Query(None, description="Filter: active | frozen"),
    db: Session = Depends(get_db),
):
    """
    DE-2: SQL-style JOIN using Pandas merge().
    Loads both tables from PostgreSQL, merges on plan_id.
    Identical output to original — demonstrates RDBMS join concepts.
    """
    df_members = crud.load_memberships_df(db)
    if df_members.empty:
        raise HTTPException(status_code=404, detail="No membership data.")

    df_plans = crud.load_plans_df(db)[["id", "price", "includes_classes", "includes_trainer"]]
    df_plans = df_plans.rename(columns={"id": "plan_id", "price": "plan_list_price"})

    df_members_subset = df_members[
        ["membership_id", "member_name", "plan_id", "plan_name",
         "status", "payment_mode", "total_fee", "duration_months"]
    ]

    # Pandas merge = SQL INNER JOIN on plan_id
    joined = pd.merge(df_members_subset, df_plans, on="plan_id", how="inner")

    joined["effective_monthly"] = (joined["total_fee"] / joined["duration_months"]).round(2)
    joined["discount_vs_list"]  = (joined["plan_list_price"] - joined["effective_monthly"]).round(2)

    if status is not None:
        joined = joined[joined["status"] == status]

    return {
        "join_description": "memberships INNER JOIN plans ON plan_id",
        "total_records":    len(joined),
        "columns":          list(joined.columns),
        "data":             joined.to_dict(orient="records"),
    }


@app.get("/etl/pipeline-run", tags=["Data Engineering"])
def run_etl_pipeline(db: Session = Depends(get_db)):
    """
    DE-3: ETL Pipeline simulation.
    EXTRACT from PostgreSQL → TRANSFORM in Pandas → LOAD (return as JSON).
    Logic unchanged; data source switched from in-memory list to DB.
    """
    raw_df = crud.load_memberships_df(db)
    extract_count = len(raw_df)

    if raw_df.empty:
        raise HTTPException(status_code=404, detail="No data to process.")

    # TRANSFORM
    raw_df["member_name"] = raw_df["member_name"].str.title()

    def classify_tier(fee):
        if fee < 1000:   return "economy"
        elif fee < 2500: return "standard"
        else:            return "premium"

    raw_df["revenue_tier"] = raw_df["total_fee"].apply(classify_tier)
    raw_df["is_referral"]  = raw_df["referral_code"].apply(lambda x: bool(str(x).strip()))
    raw_df["value_score"]  = (raw_df["total_fee"] / raw_df["duration_months"]).round(2)

    analytics_df      = raw_df.drop(columns=["phone", "fee_breakdown"], errors="ignore")
    transformed_count = len(analytics_df)

    # LOAD (simulate)
    loaded_records = analytics_df.to_dict(orient="records")

    return {
        "pipeline_status": "SUCCESS",
        "run_date":        str(date.today()),
        "stages": {
            "extract":   {"records_read":       extract_count},
            "transform": {
                "records_processed":  transformed_count,
                "new_columns_added":  ["revenue_tier", "is_referral", "value_score"],
                "columns_normalised": ["member_name"],
                "pii_columns_dropped": ["phone", "fee_breakdown"],
            },
            "load": {
                "records_written": transformed_count,
                "destination":     "analytics_warehouse (simulated)",
            },
        },
        "transformed_data": loaded_records,
    }


@app.get("/analytics/data-quality", tags=["Data Engineering"])
def data_quality_report(db: Session = Depends(get_db)):
    """
    DE-4: Data Quality checks on the memberships table.
    Identical checks; data loaded from PostgreSQL.
    """
    df = crud.load_memberships_df(db)
    if df.empty:
        raise HTTPException(status_code=404, detail="No data to validate.")

    checks = {}

    null_counts = df.isnull().sum().to_dict()
    checks["null_check"] = {
        "status":      "PASS" if sum(null_counts.values()) == 0 else "FAIL",
        "null_counts": null_counts,
    }

    dup_ids = df[df.duplicated("membership_id")]["membership_id"].tolist()
    checks["duplicate_id_check"] = {
        "status":        "PASS" if not dup_ids else "FAIL",
        "duplicate_ids": dup_ids,
    }

    valid_statuses = {"active", "frozen", "cancelled"}
    invalid_status = df[~df["status"].isin(valid_statuses)]["membership_id"].tolist()
    checks["status_validity_check"] = {
        "status":             "PASS" if not invalid_status else "FAIL",
        "allowed_values":     list(valid_statuses),
        "invalid_record_ids": invalid_status,
    }

    invalid_phones = df[df["phone"].astype(str).str.len() < 10]["membership_id"].tolist()
    checks["phone_format_check"] = {
        "status":             "PASS" if not invalid_phones else "FAIL",
        "rule":               "phone length >= 10",
        "invalid_record_ids": invalid_phones,
    }

    def valid_referral(code):
        return str(code).strip() == "" or str(code).strip().isalnum()

    invalid_referrals = df[~df["referral_code"].apply(valid_referral)]["membership_id"].tolist()
    checks["referral_format_check"] = {
        "status":             "PASS" if not invalid_referrals else "FAIL",
        "rule":               "alphanumeric or empty",
        "invalid_record_ids": invalid_referrals,
    }

    overall = "PASS" if all(c["status"] == "PASS" for c in checks.values()) else "FAIL"

    return {
        "report_date":    str(date.today()),
        "dataset":        "memberships",
        "total_records":  len(df),
        "overall_status": overall,
        "checks":         checks,
    }


@app.get("/etl/batch-summary", tags=["Data Engineering"])
def batch_summary(
    batch_size: int = Query(2, ge=1, description="Records per batch"),
    db: Session = Depends(get_db),
):
    """
    DE-5: Batch processing simulation (Spark-style partitioning).
    Data loaded from PostgreSQL; batching logic unchanged.
    """
    df = crud.load_memberships_df(db)
    if df.empty:
        raise HTTPException(status_code=404, detail="No data for batch processing.")

    total   = len(df)
    batches = []

    for i in range(0, total, batch_size):
        batch_df = df.iloc[i: i + batch_size]
        batches.append({
            "batch_number":     (i // batch_size) + 1,
            "records_in_batch": len(batch_df),
            "batch_revenue":    round(float(batch_df["total_fee"].sum()), 2),
            "avg_fee":          round(float(batch_df["total_fee"].mean()), 2),
            "active_count":     int((batch_df["status"] == "active").sum()),
            "members":          batch_df["member_name"].tolist(),
        })

    return {
        "processing_mode": "batch",
        "batch_size":      batch_size,
        "total_records":   total,
        "total_batches":   len(batches),
        "note":            "Simulates Spark-style partitioned batch processing.",
        "batches":         batches,
    }
