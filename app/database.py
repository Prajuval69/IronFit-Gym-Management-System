"""
database.py — SQLAlchemy Engine, Session & Dependency
======================================================
This file is the single source of truth for your database connection.

HOW IT WORKS:
  1. DATABASE_URL tells SQLAlchemy how to reach PostgreSQL.
  2. engine  — the low-level connection pool to the DB.
  3. SessionLocal — a factory that creates individual DB sessions (like
     opening a connection per request and closing it when done).
  4. Base — every SQLAlchemy model inherits from this; calling
     Base.metadata.create_all(engine) creates all tables automatically.
  5. get_db — a FastAPI dependency injected into every route that needs
     the DB. It yields a session, and always closes it when the request
     ends (even on errors) — critical for avoiding connection leaks.

CHANGE ONLY THIS ONE LINE to point to your own PostgreSQL instance:
    DATABASE_URL = "postgresql://USER:PASSWORD@HOST:PORT/DBNAME"
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ─────────────────────────────────────────────────────────────────────────────
# ✏️  UPDATE THIS LINE with your PostgreSQL credentials before running
# ─────────────────────────────────────────────────────────────────────────────
DATABASE_URL = "postgresql://postgres:tiger@localhost:5432/ironfit_db"
# Format : "postgresql://<username>:<password>@<host>:<port>/<database_name>"
# Example: "postgresql://john:secret123@localhost:5432/ironfit_db"
# ─────────────────────────────────────────────────────────────────────────────

# create_engine creates a connection pool.
# pool_pre_ping=True checks that connections are alive before using them —
# prevents "server closed the connection unexpectedly" errors.
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# SessionLocal is a class. Each time you call SessionLocal() you get a
# fresh database session tied to one request.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class all models inherit from.
# It holds the metadata registry — the knowledge of every table.
Base = declarative_base()


def get_db():
    """
    FastAPI dependency — yields a DB session per request.

    Usage in a route:
        from database import get_db
        from sqlalchemy.orm import Session
        from fastapi import Depends

        @app.get("/something")
        def my_route(db: Session = Depends(get_db)):
            ...

    The try/finally guarantees the session is always closed, even when
    an exception is raised inside the route.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
