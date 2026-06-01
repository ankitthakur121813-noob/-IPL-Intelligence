"""
db.py — Database connection manager
=====================================
Supports both SQLite (local dev) and PostgreSQL (production/cloud).

To use SQLite  →  no changes needed, works out of the box.
To use PostgreSQL →  set these environment variables:
    DB_ENGINE=postgresql
    DB_HOST=localhost
    DB_PORT=5432
    DB_NAME=ipl
    DB_USER=postgres
    DB_PASSWORD=yourpassword

Or set a full connection string:
    DATABASE_URL=postgresql://user:password@host:5432/ipl

To load data into PostgreSQL run:
    python setup_db.py --engine postgresql
"""

import os
import sqlite3

# ── Detect which engine to use ────────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")
DB_ENGINE    = os.environ.get("DB_ENGINE", "sqlite").lower()

# Heroku / Railway / Render set DATABASE_URL automatically
if DATABASE_URL.startswith("postgres"):
    DB_ENGINE = "postgresql"

SQLITE_PATH = os.environ.get("SQLITE_PATH", "ipl.db")


def get_connection():
    """
    Return a live database connection.
    Caller is responsible for closing it (or use as context manager).

    SQLite  → returns sqlite3.Connection
    PostgreSQL → returns psycopg2.connection
    """
    if DB_ENGINE == "postgresql":
        try:
            import psycopg2
        except ImportError:
            raise ImportError(
                "psycopg2 not installed. Run:  pip install psycopg2-binary"
            )

        if DATABASE_URL:
            conn = psycopg2.connect(DATABASE_URL)
        else:
            conn = psycopg2.connect(
                host     = os.environ.get("DB_HOST",     "localhost"),
                port     = int(os.environ.get("DB_PORT", "5432")),
                dbname   = os.environ.get("DB_NAME",     "ipl"),
                user     = os.environ.get("DB_USER",     "postgres"),
                password = os.environ.get("DB_PASSWORD", ""),
            )
        return conn

    else:  # sqlite (default)
        if not os.path.exists(SQLITE_PATH):
            raise FileNotFoundError(
                f"{SQLITE_PATH} not found. Run:  python setup_db.py"
            )
        conn = sqlite3.connect(f"file:{SQLITE_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn


def read_sql(query: str, params: dict = None):
    """
    Execute a SELECT query and return a Pandas DataFrame.
    Works identically for SQLite and PostgreSQL — same call, same result.

    Example:
        df = read_sql("SELECT * FROM batting_stats LIMIT :n", {"n": 10})
    """
    import pandas as pd

    if DB_ENGINE == "postgresql":
        # psycopg2 uses %(name)s placeholders; convert from :name style
        import re
        pg_query = re.sub(r":(\w+)", r"%(\1)s", query)
        with get_connection() as conn:
            return pd.read_sql_query(pg_query, conn, params=params)
    else:
        with get_connection() as conn:
            return pd.read_sql_query(query, conn, params=params or {})


def current_engine() -> str:
    return DB_ENGINE
