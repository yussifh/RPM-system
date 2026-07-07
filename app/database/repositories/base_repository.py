"""
base_repository.py
-------------------
Shared query-execution logic for every concrete repository.

Design decision: this is the ONLY place in the entire codebase that
directly executes SQL. Every concrete repository (UserRepository,
VitalsRepository, ...) inherits from this class rather than writing its
own cursor/commit/rollback boilerplate. Benefits:

  1. 100% parameterized queries enforced in one place — no repository
     can accidentally string-format a value into SQL.
  2. MySQL error codes (e.g., 1062 = duplicate key) are translated into
     our own domain exceptions HERE, so Service/UI code never needs to
     know a single thing about MySQL error codes.
  3. Adding cross-cutting behavior later (query logging, slow-query
     detection, retry-on-deadlock) means editing one file, not eight.
"""

import logging
from typing import Any, Optional

import mysql.connector

from app.database.connection import db
from app.core.exceptions import (
    DatabaseConnectionError,
    DuplicateRecordError,
    RecordNotFoundError,
)

logger = logging.getLogger(__name__)

# MySQL error codes we specifically translate into domain exceptions.
# Reference: https://dev.mysql.com/doc/mysql-errors/8.0/en/server-error-reference.html
_ERR_DUPLICATE_ENTRY = 1062
_ERR_ROW_IS_REFERENCED = 1451   # FK RESTRICT violation on DELETE
_ERR_NO_REFERENCED_ROW = 1452   # FK violation on INSERT/UPDATE


class BaseRepository:
    """Base class providing safe, reusable query execution helpers."""

    def execute_query(self, sql: str, params: tuple = ()) -> list[dict]:
        """
        Runs a SELECT and returns all matching rows as a list of dicts.
        Use for read operations.
        """
        with db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(sql, params)
                return cursor.fetchall()
            finally:
                cursor.close()

    def execute_one(self, sql: str, params: tuple = ()) -> Optional[dict]:
        """
        Runs a SELECT expected to return zero or one row.
        Returns None if no row matched (caller decides whether that's
        an error via RecordNotFoundError, depending on context).
        """
        with db.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                cursor.execute(sql, params)
                return cursor.fetchone()
            finally:
                cursor.close()

    def execute_write(self, sql: str, params: tuple = ()) -> dict[str, Any]:
        """
        Runs an INSERT/UPDATE/DELETE inside an explicit transaction.
        Returns {'lastrowid': int, 'rowcount': int}.

        Commits on success; the connection context manager (see
        connection.py) automatically rolls back on any exception.
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(sql, params)
                conn.commit()
                return {"lastrowid": cursor.lastrowid, "rowcount": cursor.rowcount}
            except mysql.connector.Error as e:
                conn.rollback()
                self._raise_domain_exception(e)
            finally:
                cursor.close()

    def execute_many(self, sql: str, param_list: list[tuple]) -> int:
        """
        Bulk INSERT/UPDATE using executemany — used by seed scripts and
        any future batch-import functionality. Returns total row count
        affected.
        """
        with db.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.executemany(sql, param_list)
                conn.commit()
                return cursor.rowcount
            except mysql.connector.Error as e:
                conn.rollback()
                self._raise_domain_exception(e)
            finally:
                cursor.close()

    @staticmethod
    def _raise_domain_exception(error: mysql.connector.Error) -> None:
        """Translates raw MySQL errors into our domain-specific exceptions."""
        if error.errno == _ERR_DUPLICATE_ENTRY:
            raise DuplicateRecordError(
                "A record with this unique value already exists."
            ) from error
        if error.errno in (_ERR_ROW_IS_REFERENCED, _ERR_NO_REFERENCED_ROW):
            raise RecordNotFoundError(
                "Operation failed due to a related record constraint "
                "(e.g., referenced record missing or still in use)."
            ) from error
        logger.error("Unhandled MySQL error (errno=%s): %s", error.errno, error)
        raise DatabaseConnectionError(f"Database write failed: {error}") from error
