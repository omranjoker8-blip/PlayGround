"""Small SQLite-compatible facade for the PostgreSQL/Supabase backend.

The application was originally written against sqlite3.  Keeping this adapter
here lets the same business logic run locally on SQLite and in Vercel against
Supabase PostgreSQL while the migration is completed incrementally.
"""
import re
import sqlite3

import psycopg
from psycopg import errors as pg_errors


def _translate(sql: str) -> str:
    stripped = sql.strip()
    upper = stripped.upper()

    # SQLite-only pragmas are harmless no-ops for PostgreSQL.
    if upper.startswith("PRAGMA "):
        return "SELECT 1"
    if upper == "VACUUM":
        return "SELECT 1"

    if "sqlite_master" in sql:
        if re.search(r"SELECT\s+name\s+FROM\s+sqlite_master", sql, re.I):
            return "SELECT tablename AS name FROM pg_tables WHERE schemaname = 'public'"
        if re.search(r"SELECT\s+count\(\*\)\s+FROM\s+sqlite_master", sql, re.I):
            return "SELECT count(*) FROM pg_tables WHERE schemaname = 'public'"

    had_insert_ignore = bool(re.search(r"INSERT\s+OR\s+IGNORE\s+INTO", sql, re.I))
    sql = re.sub(r"INSERT\s+OR\s+IGNORE\s+INTO", "INSERT INTO", sql, flags=re.I)
    if had_insert_ignore:
        sql += " ON CONFLICT DO NOTHING"
    if upper.startswith("INSERT OR REPLACE INTO LINK_CODES"):
        sql = re.sub(r"INSERT\s+OR\s+REPLACE\s+INTO", "INSERT INTO", sql, count=1, flags=re.I)
        sql += " ON CONFLICT (code) DO UPDATE SET web_user_id = EXCLUDED.web_user_id, expires_at = EXCLUDED.expires_at"
    elif upper.startswith("INSERT OR REPLACE INTO CATEGORY_DESCRIPTION"):
        sql = re.sub(r"INSERT\s+OR\s+REPLACE\s+INTO", "INSERT INTO", sql, count=1, flags=re.I)
        sql += " ON CONFLICT (category_name) DO UPDATE SET description = EXCLUDED.description"

    sql = re.sub(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", "BIGSERIAL PRIMARY KEY", sql, flags=re.I)
    # SQLite INTEGER is signed 64-bit. PostgreSQL INTEGER is only 32-bit,
    # while this project stores Telegram IDs and web IDs larger than 2^31.
    sql = re.sub(r"\bINTEGER\b", "BIGINT", sql, flags=re.I)
    sql = re.sub(r"datetime\(['\"]now['\"]\)", "CURRENT_TIMESTAMP", sql, flags=re.I)
    sql = re.sub(r"strftime\(['\"]%Y-%m['\"],\s*created_at\)", "TO_CHAR(created_at, 'YYYY-MM')", sql, flags=re.I)
    sql = re.sub(r"strftime\(['\"]%Y-%m['\"],\s*['\"]now['\"]\)", "TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM')", sql, flags=re.I)
    sql = re.sub(r"\bMAX\(\s*0\s*,", "GREATEST(0,", sql, flags=re.I)
    # The project uses qmark placeholders throughout its SQLite queries.
    return sql.replace("?", "%s")


class Cursor:
    def __init__(self, connection):
        self.connection = connection
        self.raw = connection.raw.cursor()
        self._lastrowid = None

    def execute(self, sql, params=None):
        translated = _translate(sql)
        savepoint = "compat_statement"
        try:
            self.connection.raw.execute(f"SAVEPOINT {savepoint}")
            self.raw.execute(translated, params or ())
        except pg_errors.UniqueViolation as exc:
            self.connection.raw.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            self.connection.raw.execute(f"RELEASE SAVEPOINT {savepoint}")
            raise sqlite3.IntegrityError(str(exc)) from exc
        except pg_errors.DatabaseError as exc:
            self.connection.raw.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            self.connection.raw.execute(f"RELEASE SAVEPOINT {savepoint}")
            raise sqlite3.OperationalError(str(exc)) from exc
        else:
            self.connection.raw.execute(f"RELEASE SAVEPOINT {savepoint}")

        self._lastrowid = None
        if translated.lstrip().upper().startswith("INSERT"):
            savepoint = "compat_lastrowid"
            try:
                self.connection.raw.execute(f"SAVEPOINT {savepoint}")
                with self.connection.raw.cursor() as id_cursor:
                    id_cursor.execute("SELECT lastval()")
                    self._lastrowid = id_cursor.fetchone()[0]
                self.connection.raw.execute(f"RELEASE SAVEPOINT {savepoint}")
            except Exception:
                self._lastrowid = None
                try:
                    self.connection.raw.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                    self.connection.raw.execute(f"RELEASE SAVEPOINT {savepoint}")
                except Exception:
                    pass
        return self

    def executemany(self, sql, params_seq):
        savepoint = "compat_many"
        try:
            self.connection.raw.execute(f"SAVEPOINT {savepoint}")
            self.raw.executemany(_translate(sql), params_seq)
        except pg_errors.UniqueViolation as exc:
            self.connection.raw.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            self.connection.raw.execute(f"RELEASE SAVEPOINT {savepoint}")
            raise sqlite3.IntegrityError(str(exc)) from exc
        except pg_errors.DatabaseError as exc:
            self.connection.raw.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
            self.connection.raw.execute(f"RELEASE SAVEPOINT {savepoint}")
            raise sqlite3.OperationalError(str(exc)) from exc
        else:
            self.connection.raw.execute(f"RELEASE SAVEPOINT {savepoint}")
        return self

    def fetchone(self):
        return self.raw.fetchone()

    def fetchall(self):
        return self.raw.fetchall()

    @property
    def rowcount(self):
        return self.raw.rowcount

    @property
    def lastrowid(self):
        return self._lastrowid


class Connection:
    def __init__(self, url):
        self.raw = psycopg.connect(url, prepare_threshold=None)

    def cursor(self):
        return Cursor(self)

    def execute(self, sql, params=None):
        return self.cursor().execute(sql, params)

    def commit(self):
        self.raw.commit()

    def rollback(self):
        self.raw.rollback()

    def close(self):
        self.raw.close()


def connect(url):
    return Connection(url)
