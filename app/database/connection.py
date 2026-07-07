"""
connection.py
-------------
Manages a single, reusable MySQL connection pool for the entire
application.

Why pooling: Streamlit reruns the script on every user interaction.
Opening a brand-new TCP connection to MySQL on every rerun would be slow
and would exhaust MySQL's max_connections limit once multiple doctors/
patients use the system concurrently. A connection pool solves this by
creating a fixed number of connections up front and handing them out
(and taking them back) as needed.

Usage:
    from app.database.connection import db

    with db.get_connection() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id = %s", (1,))
        row = cursor.fetchone()
"""

from contextlib import contextmanager
import logging

import mysql.connector
from mysql.connector import pooling

from app.core.config import Config
from app.core.exceptions import DatabaseConnectionError

logger = logging.getLogger(__name__)


class Database:
    """
    Thin wrapper around a MySQLConnectionPool.

    Design decision: implemented as a module-level singleton instance
    (see bottom of file) rather than a classic __new__-based singleton
    class. Simpler, explicit, and avoids the subtle bugs that come with
    overriding __new__.
    """

    _pool: pooling.MySQLConnectionPool | None = None

    def __init__(self, pool_name: str = "rpm_pool", pool_size: int = 5):
        self._pool_name = pool_name
        self._pool_size = pool_size

    def _initialize_pool(self) -> None:
        """Lazily creates the connection pool on first use."""
        if self._pool is not None:
            return

        try:
            self._pool = pooling.MySQLConnectionPool(
                pool_name=self._pool_name,
                pool_size=self._pool_size,
                host=Config.DB.host,
                port=Config.DB.port,
                database=Config.DB.name,
                user=Config.DB.user,
                password=Config.DB.password,
                autocommit=False,   # explicit commit/rollback control per-transaction
                charset="utf8mb4",
            )
            logger.info("MySQL connection pool '%s' initialized (size=%d)",
                        self._pool_name, self._pool_size)
        except mysql.connector.Error as e:
            logger.error("Failed to initialize MySQL connection pool: %s", e)
            raise DatabaseConnectionError(
                f"Could not connect to MySQL database '{Config.DB.name}' "
                f"at {Config.DB.host}:{Config.DB.port}. "
                f"Check that MySQL is running and .env credentials are correct."
            ) from e

    @contextmanager
    def get_connection(self):
        """
        Context manager that yields a pooled connection and guarantees
        it is returned to the pool afterward (conn.close() on a pooled
        connection returns it to the pool rather than actually closing
        the socket).

        On any exception, the transaction is rolled back before the
        connection is released, so a failed multi-statement operation
        never leaves partial writes behind.
        """
        self._initialize_pool()

        conn = None
        try:
            conn = self._pool.get_connection()
            yield conn
        except mysql.connector.Error as e:
            if conn is not None:
                conn.rollback()
            logger.error("Database error, transaction rolled back: %s", e)
            raise DatabaseConnectionError(f"Database operation failed: {e}") from e
        finally:
            if conn is not None:
                conn.close()  # returns connection to the pool, does not close the socket


# Module-level singleton — import this instance everywhere.
db = Database()
