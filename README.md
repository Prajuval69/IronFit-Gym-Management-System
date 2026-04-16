# 💪 IronFit Gym Management System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.2-150458?style=for-the-badge&logo=pandas&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)

**A production-style Gym Management REST API demonstrating full-stack data engineering skills.**  
Built during FastAPI Internship at **Innomatics Research Labs** · Extended for Associate Data Engineer role alignment.

[Features](#-features) · [Architecture](#-architecture) · [Quick Start](#-quick-start) · [API Reference](#-api-reference) · [Data Engineering](#-data-engineering-layer) · [Project Structure](#-project-structure)

</div>

---

## 🎯 What This Project Demonstrates

This is not just a CRUD app. It's a complete backend system designed to show real-world **Associate Data Engineer** skills:

| Skill | How It's Demonstrated |
|---|---|
| **Python & Problem Solving** | Clean helpers, list comprehensions, modular design |
| **REST Microservices** | 25+ endpoints across Plans, Memberships, Classes, Analytics |
| **PostgreSQL + SQLAlchemy** | ORM models, FK relationships, session management, dependency injection |
| **Pandas Analytics** | `groupby`, `agg`, `describe`, `merge` — all on live DB data |
| **ETL Pipeline Design** | Explicit Extract → Transform → Load stages |
| **SQL-style Joins** | `pd.merge()` simulating `INNER JOIN` across two tables |
| **Data Quality Framework** | 5 automated DQ checks with PASS/FAIL reporting |
| **Batch Processing** | Spark-style partitioned batch simulation |
| **Pydantic Validation** | Schema-enforced request validation (HTTP 422 on bad input) |
| **Error Handling** | 400, 403, 404, 422 — all handled correctly |

---

## 🏗 Architecture

```
┌─────────────────────────┐
│   Frontend (HTML/JS)    │  ← ironfit-frontend.html
└────────────┬────────────┘
             │ HTTP Requests
┌────────────▼────────────┐
│   FastAPI  (main.py)    │  ← Routes only — no business logic
└────────────┬────────────┘
             │ calls
┌────────────▼────────────┐
│   CRUD Layer (crud.py)  │  ← All DB queries live here
└────────────┬────────────┘
             │ reads/writes
┌────────────▼────────────┐
│      PostgreSQL         │  ← Persistent storage
└────────────┬────────────┘
             │ pd.read_sql()
┌────────────▼────────────┐
│   Pandas DataFrames     │  ← Analytics, ETL, DQ, Batch
└─────────────────────────┘
```

---

## ✨ Features

### Core Gym Management
- **Plans** — Full CRUD: create, read, update, delete with duplicate detection and active-member guard on delete
- **Memberships** — Enrol members with automatic fee calculation: duration discounts (10%/20%), referral codes (5% off), EMI processing fee
- **Class Bookings** — Book, list, and cancel classes with active-membership and feature gating
- **Membership Lifecycle** — Freeze and reactivate memberships

### Advanced Query Features
- **Filtering** — Filter plans by price, duration, includes_classes, includes_trainer
- **Keyword Search** — Full-text search with special `classes` and `trainer` keywords
- **Sorting** — Sort any resource by multiple fields, ascending or descending
- **Pagination** — Page-based pagination with `total_pages` metadata
- **Combined Browse** — Single endpoint for keyword → filter → sort → paginate pipeline

### Data Engineering Layer
- **Revenue Analytics** — Pandas `groupby` aggregations on live DB data
- **SQL-style JOIN** — `pd.merge()` between memberships and plans tables
- **ETL Pipeline** — Extract from PostgreSQL → Transform in Pandas → Load to analytics layer
- **Data Quality Report** — 5 automated checks: nulls, duplicate IDs, invalid statuses, phone format, referral format
- **Batch Processing** — Spark-style partitioned batch processing simulation

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- PostgreSQL 13+ installed and running

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/ironfit-gym-management.git
cd ironfit-gym-management
```

### 2. Create the Database

```bash
# Open PostgreSQL shell
psql -U postgres

# Run inside psql:
CREATE DATABASE ironfit_db;
\q
```

### 3. Configure the Connection

Open `app/database.py` and update line 25:

```python
# Replace with your actual credentials
DATABASE_URL = "postgresql://postgres:yourpassword@localhost:5432/ironfit_db"
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Seed the Database

```bash
python seed.py
```

```
✅ Plans seeded: 5 new rows
✅ Memberships seeded: 6 new rows
🎉 Database seeding complete!
```

### 6. Start the Server

```bash
uvicorn main:app --reload
```

| URL | What it opens |
|-----|--------------|
| http://127.0.0.1:8000/docs | Swagger UI — interactive API docs |
| http://127.0.0.1:8000/redoc | ReDoc API documentation |
| `ironfit-frontend.html` | Open directly in your browser |

---

## 📁 Project Structure

```
ironfit-gym-management/
│
├── main.py                  # FastAPI routes (HTTP layer only)
├── seed.py                  # One-time DB seeding script
├── requirements.txt         # All dependencies
├── ironfit-frontend.html    # Frontend UI (no changes needed)
│
└── app/
    ├── __init__.py          # Makes app/ a Python package
    ├── database.py          # Engine, SessionLocal, Base, get_db()
    ├── models.py            # SQLAlchemy ORM models → PostgreSQL tables
    ├── schemas.py           # Pydantic request/response schemas
    └── crud.py              # All database operations
```

### File Responsibilities

| File | Layer | Responsibility |
|------|-------|---------------|
| `database.py` | Infrastructure | DB connection, session factory, dependency |
| `models.py` | Data | SQLAlchemy ORM classes → PostgreSQL tables |
| `schemas.py` | Validation | Pydantic schemas for request/response |
| `crud.py` | Data Access | All SQL queries, Pandas DataFrame loading |
| `main.py` | HTTP | Routes, status codes, HTTP error handling |
| `seed.py` | Tooling | Idempotent initial data loader |

---

## 📖 API Reference

### Plans

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `GET` | `/plans` | All plans + min/max price stats | 200 |
| `GET` | `/plans/summary` | Aggregated stats (cheapest, most expensive) | 200 |
| `GET` | `/plans/filter` | Filter by `max_price`, `max_duration`, features | 200 |
| `GET` | `/plans/search?keyword=` | Keyword search; `classes`/`trainer` special | 200 |
| `GET` | `/plans/sort` | Sort by `price`, `name`, or `duration_months` | 200 |
| `GET` | `/plans/page` | Paginate with `page` + `limit` | 200 |
| `GET` | `/plans/browse` | Combined keyword→filter→sort→paginate | 200 |
| `GET` | `/plans/{id}` | Get single plan by ID | 200 / 404 |
| `POST` | `/plans` | Create new plan (rejects duplicate names) | 201 / 400 |
| `PUT` | `/plans/{id}` | Partial update via query params | 200 / 404 |
| `DELETE` | `/plans/{id}` | Delete (blocked if active members exist) | 200 / 400 / 404 |

### Memberships

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `GET` | `/memberships` | All memberships + total | 200 |
| `POST` | `/memberships` | Enrol with fee calculation + discounts | 201 / 404 / 422 |
| `GET` | `/memberships/search` | Search by `member_name` | 200 |
| `GET` | `/memberships/sort` | Sort by `total_fee` or `duration_months` | 200 |
| `GET` | `/memberships/page` | Paginate memberships | 200 |
| `PUT` | `/memberships/{id}/freeze` | Freeze active membership | 200 / 400 / 404 |
| `PUT` | `/memberships/{id}/reactivate` | Reactivate frozen membership | 200 / 400 / 404 |

### Classes

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `POST` | `/classes/book` | Book class (requires active + classes plan) | 201 / 403 |
| `GET` | `/classes/bookings` | List all bookings | 200 |
| `DELETE` | `/classes/cancel/{id}` | Cancel a booking | 200 / 404 |

### Data Engineering

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/analytics/revenue` | Pandas groupby revenue analytics |
| `GET` | `/analytics/members-with-plans` | SQL-style JOIN via `pd.merge()` |
| `GET` | `/etl/pipeline-run` | ETL: Extract → Transform → Load |
| `GET` | `/analytics/data-quality` | 5-check data quality report |
| `GET` | `/etl/batch-summary` | Spark-style batch processing |

---

## 🔬 Data Engineering Layer

### DE-1 · Revenue Analytics — `/analytics/revenue`
Uses `pd.read_sql()` to load the memberships table into a Pandas DataFrame, then applies `groupby` + `agg` + `describe` to produce plan-level and payment-mode-level revenue breakdowns.

### DE-2 · SQL-style JOIN — `/analytics/members-with-plans`
Loads both `memberships` and `plans` tables into DataFrames and joins them with `pd.merge(..., how="inner")` — demonstrating relational data modelling and join concepts without raw SQL.

### DE-3 · ETL Pipeline — `/etl/pipeline-run`
Explicit three-stage pipeline:
- **Extract** — pull raw records from PostgreSQL via `pd.read_sql()`
- **Transform** — normalise names, derive `revenue_tier`, flag referrals, compute `value_score`, drop PII columns
- **Load** — return transformed dataset (simulates writing to a data warehouse)

### DE-4 · Data Quality Report — `/analytics/data-quality`
Five automated checks on the memberships table:
1. Null / missing value check
2. Duplicate membership ID check
3. Invalid status value check (`active` / `frozen` / `cancelled` only)
4. Phone number format check (must be ≥ 10 digits)
5. Referral code format check (alphanumeric or empty)

Each check reports `PASS` or `FAIL` with the specific record IDs that failed.

### DE-5 · Batch Processing — `/etl/batch-summary`
Partitions membership records into configurable batches (like Spark RDD partitions). Each batch independently computes `total_revenue`, `avg_fee`, and `active_count` — demonstrating batch-vs-streaming awareness.

---

## 🛡 Validation & Error Handling

| Scenario | HTTP Status |
|----------|------------|
| Valid request | 200 / 201 |
| Resource not found | 404 |
| Business rule violation (e.g. deleting plan with active members) | 400 |
| Insufficient permissions (e.g. booking class without eligible membership) | 403 |
| Invalid request body (e.g. phone < 10 digits) | 422 |

Pydantic enforces all input constraints automatically — no manual validation code needed in routes.

---

## 📦 Tech Stack

| Tool | Version | Purpose |
|------|---------|---------|
| **FastAPI** | 0.111 | REST microservice framework |
| **SQLAlchemy** | 2.0 | ORM — Python objects ↔ PostgreSQL tables |
| **psycopg2-binary** | 2.9 | PostgreSQL driver |
| **Pydantic v2** | 2.7 | Request validation & schema enforcement |
| **Pandas** | 2.2 | Analytics, ETL, data quality, batch processing |
| **Uvicorn** | 0.29 | ASGI production server |
| **Swagger UI** | built-in | Auto-generated interactive API docs at `/docs` |

---

## 🧠 Key Design Decisions

**Why separate `crud.py` from `main.py`?**
Routes in `main.py` handle HTTP concerns only (status codes, request parsing, error responses). All database logic lives in `crud.py`. This is the Repository Pattern — it makes DB operations independently testable and reusable across multiple routes.

**Why `pd.read_sql()` instead of converting ORM objects?**
`pd.read_sql(query.statement, db.bind)` executes the SQL and streams results directly into a DataFrame in one round trip. Converting ORM objects one by one would be slower and more verbose.

**Why store `fee_breakdown` as JSON text?**
Serialising to JSON text (`json.dumps`) keeps the full breakdown in a single column without needing an extra table. It deserialises back to a dict on read via `json.loads` — no data loss, simpler schema.

**Why `Base.metadata.create_all()` instead of Alembic?**
For a portfolio/internship project, auto-creation on startup is the simplest approach. In a production system, you would use Alembic for versioned, reversible schema migrations.

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">
Built as part of the FastAPI Internship at <strong>Innomatics Research Labs</strong> 🚀<br>
Extended with PostgreSQL + Data Engineering features for Associate Data Engineer role alignment.
</div>
