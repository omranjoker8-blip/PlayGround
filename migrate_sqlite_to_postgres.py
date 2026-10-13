"""One-time migration of the local products.db into Supabase PostgreSQL.

Run this locally with DATABASE_URL set in the shell. Never commit the URL.
The source SQLite file is read-only during the migration.
"""
import os
import sqlite3


if not os.environ.get("DATABASE_URL"):
    raise SystemExit("Set DATABASE_URL to the Supabase Transaction Pooler URI first")

os.environ.setdefault("VERCEL", "1")
os.environ.setdefault("ARAB_SECRET_KEY", "migration-only-secret")
os.environ.setdefault("ARAB_ADMIN_PASSWORD", "migration-only-password")

import app  # noqa: E402,F401 - initializes the complete target schema
from db_compat import connect  # noqa: E402


source = sqlite3.connect(os.environ.get("SQLITE_SOURCE", "products.db"))
source.row_factory = sqlite3.Row
target = connect(os.environ["DATABASE_URL"])

try:
    table_names = [
        row[0]
        for row in source.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence' ORDER BY name"
        )
    ]
    for table in table_names:
        columns = [row[1] for row in source.execute(f'PRAGMA table_info("{table}")')]
        if not columns:
            continue
        quoted_table = '"' + table.replace('"', '""') + '"'
        quoted_columns = ", ".join('"' + c.replace('"', '""') + '"' for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        insert_sql = f"INSERT INTO {quoted_table} ({quoted_columns}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
        rows = source.execute(f'SELECT {quoted_columns} FROM {quoted_table}').fetchall()
        cursor = target.cursor()
        for row in rows:
            cursor.execute(insert_sql, tuple(row))
        target.commit()
        print(f"migrated {table}: {len(rows)} rows")

    cursor = target.cursor()
    cursor.raw.execute(
        "SELECT table_name, column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND column_default LIKE 'nextval(%'"
    )
    for table, column in cursor.raw.fetchall():
        quoted_table = '"' + table.replace('"', '""') + '"'
        quoted_column = '"' + column.replace('"', '""') + '"'
        cursor.raw.execute(
            "SELECT setval(pg_get_serial_sequence(%s, %s), "
            f"COALESCE(MAX({quoted_column}), 1), MAX({quoted_column}) IS NOT NULL) FROM {quoted_table}",
            (table, column),
        )
    target.commit()
    print("Migration completed")
finally:
    source.close()
    target.close()
