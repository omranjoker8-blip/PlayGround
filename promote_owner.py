#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Verify/grant store-owner access for omranjoker8@gmail.com — SECURE, no bypass.

Uses only the existing auth system:
 1. Checks OWNER_EMAILS in app.py (code-level owner).
 2. Optionally adds the email to web_admins table (requires running DB only,
    never forges tokens or passwords).
 3. Never prints secrets, never disables auth.

Usage:
  python3 promote_owner.py                      # check only
  python3 promote_owner.py --apply               # add to web_admins if DB present
"""
import os
import re
import sys

PRIMARY = "omranjoker8@gmail.com"


def check_code_owner():
    src = open("app.py", encoding="utf-8").read()
    m = re.search(r"OWNER_EMAILS\s*=\s*\{([^}]*)\}", src)
    emails = set(re.findall(r'"([^"]+)"', m.group(1)) if m else [])
    emails |= set(re.findall(r"'([^']+)'", m.group(1)) if m else [])
    pm = re.search(r'PRIMARY_OWNER_EMAIL\s*=\s*["\']([^"\']+)["\']', src)
    primary = pm.group(1) if pm else None
    return emails, primary


def apply_db_admin(email):
    import sqlite3
    candidates = [
        os.environ.get("ARAB_DATA_DIR", ""),
        os.path.dirname(os.path.abspath(__file__)),
        "/tmp/arab-store",
    ]
    db = None
    for d in candidates:
        if not d:
            continue
        p = os.path.join(d, "products.db")
        if os.path.isfile(p):
            db = p
            break
    if not db:
        return False, "no local products.db found (production uses DATABASE_URL — add via admin panel instead)"
    con = sqlite3.connect(db)
    try:
        con.execute("CREATE TABLE IF NOT EXISTS web_admins (email TEXT PRIMARY KEY, added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        con.execute("INSERT OR IGNORE INTO web_admins (email) VALUES (?)", (email,))
        con.commit()
    finally:
        con.close()
    return True, db


def main():
    emails, primary = check_code_owner()
    print(f"PRIMARY_OWNER_EMAIL = {primary}")
    print(f"OWNER_EMAILS = {sorted(emails)}")
    ok = (PRIMARY in emails) and (primary == PRIMARY)
    print(("OK: " if ok else "MISSING: ") + f"{PRIMARY} {'is' if ok else 'is NOT'} the primary code-level owner")
    if "--apply" in sys.argv:
        done, info = apply_db_admin(PRIMARY)
        print(("DB admin added via " if done else "DB note: ") + info)
    else:
        print("hint: run with --apply to also insert into local web_admins (SQLite dev only).")
        print("production (Supabase): log in as owner via /api/admin/login then POST /api/admin/promote-owner with admin_password.")
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
