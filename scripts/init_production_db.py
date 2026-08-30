"""
init_production_db.py
---------------------
ONE-TIME production database initializer.

Creates/uses the target database, applies database/schema.sql,
database/seed_data.sql (only when the DB is empty) and the extra
tables from run_migrations.py (doctor_ratings, teleconsultations,
system_settings).

Usage (against the deployed DB):
    py -3.11 scripts/init_production_db.py \
        --host <HOST> --port 3306 \
        --user <USER> --password <PASSWORD> \
        --name rpm_system

Connection details also fall back to the DB_* environment variables
(the same ones the app reads), so you can instead export them:
    Set DB_HOST / DB_PORT / DB_USER / DB_PASSWORD / DB_NAME

IMPORTANT: schema.sql deliberately DROPs every table — this script is
INTENDED for a fresh/empty database only. It refuses to seed a database
that already contains users.
"""
import argparse
import os
import re
import runpy
import sys

from pathlib import Path

import mysql.connector

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA = REPO_ROOT / "database" / "schema.sql"
SEED = REPO_ROOT / "database" / "seed_data.sql"

# Ensure Unicode output (arrows/checks) works on Windows cp1252 consoles too.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


def parse_args():
    p = argparse.ArgumentParser(description="Initialize the rpm_system production database.")
    p.add_argument("--host", default=os.getenv("DB_HOST", "localhost"))
    p.add_argument("--port", type=int, default=int(os.getenv("DB_PORT", "3306")))
    p.add_argument("--user", default=os.getenv("DB_USER", "root"))
    p.add_argument("--password", default=os.getenv("DB_PASSWORD", ""))
    p.add_argument("--name", default=os.getenv("DB_NAME", "rpm_system"))
    p.add_argument("--skip-seed", action="store_true",
                   help="Apply schema + migrations but leave the DB empty (no demo accounts).")
    return p.parse_args()


def split_statements(sql_text: str):
    """Yield trimmed SQL statements, dropping comment lines and blank chunks."""
    lines = [ln for ln in sql_text.splitlines()
             if ln.strip() and not ln.strip().startswith("--")]
    body = "\n".join(lines)
    # schema.sql assumes the mysql CLI: it issues CREATE DATABASE / USE.
    # We already connect to the right database, so strip both statements.
    body = re.sub(r"CREATE DATABASE.*?;", "", body, flags=re.I | re.S)
    body = re.sub(r"^[ \t]*USE .*?;", "", body, flags=re.I | re.S | re.M)
    for chunk in body.split(";"):
        stmt = chunk.strip()
        if stmt:
            yield stmt


# Tables added later by run_migrations.py — schema.sql's DROP list does NOT
# include them, so they must be removed first or DROP TABLE users fails.
MIGRATION_TABLES = ["system_settings", "teleconsultations", "doctor_ratings"]


def connect_without_db(args, charset="utf8mb4"):
    return mysql.connector.connect(
        host=args.host, port=args.port, user=args.user,
        password=args.password, charset=charset,
    )


def run_statement(conn, stmt):
    cur = conn.cursor(buffered=True)
    cur.execute(stmt)
    conn.commit()
    cur.close()


def main():
    args = parse_args()

    print(f"→ Connecting to {args.user}@{args.host}:{args.port}")
    try:
        admin_conn = connect_without_db(args)
    except mysql.connector.Error as e:
        sys.exit(f"✗ Connection failed: {e}")

    # Ensure the target database exists (safe even if it already does).
    admin_cur = admin_conn.cursor()
    admin_cur.execute(
        f"CREATE DATABASE IF NOT EXISTS `{args.name}` "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    admin_conn.commit()
    admin_conn.close()
    print(f"✓ Database `{args.name}` ready")

    # Put connection details into the environment so run_migrations.py picks them up.
    os.environ["DB_HOST"] = args.host
    os.environ["DB_PORT"] = str(args.port)
    os.environ["DB_NAME"] = args.name
    os.environ["DB_USER"] = args.user
    os.environ["DB_PASSWORD"] = args.password

    conn = mysql.connector.connect(
        host=args.host, port=args.port, user=args.user,
        password=args.password, database=args.name, charset="utf8mb4",
    )

    # -- schema.sql (destructive, intended for fresh DBs) -------------
    print("→ Removing migration tables (not covered by schema.sql DROPs) ...")
    for table in MIGRATION_TABLES:
        run_statement(conn, f"DROP TABLE IF EXISTS `{table}`")
    print("→ Applying database/schema.sql ...")
    for stmt in split_statements(SCHEMA.read_text(encoding="utf-8")):
        run_statement(conn, stmt)
    print("✓ Schema applied")

    # -- seed_data.sql (only when there is nothing in the users table) --
    cur = conn.cursor(buffered=True)
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]
    cur.close()

    if args.skip_seed or user_count > 0:
        print(f"⏭  Skipping seed data ({user_count} existing users).")
    else:
        print("→ Applying database/seed_data.sql (demo accounts) ...")
        for stmt in split_statements(SEED.read_text(encoding="utf-8")):
            run_statement(conn, stmt)
        print("✓ Seed data applied (admin@rpm.com / admin1234, doctor@rpm.com, patient@rpm.com)")

    conn.close()

    # -- extra tables (doctor_ratings, teleconsultations, system_settings) --
    print("→ Running run_migrations.py (extra tables) ...")
    runpy.run_path(str(REPO_ROOT / "run_migrations.py"), run_name="__main__")
    print("\n✅ Production database initialization complete!")


if __name__ == "__main__":
    main()