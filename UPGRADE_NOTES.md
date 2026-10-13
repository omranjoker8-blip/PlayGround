# Arab Store — Upgrade Notes (October 2026)

## What was done
Full modernization of the existing `tajarib993` Arab Store project (Flask + SQLite/Supabase + static `site/` frontend). No replacement, no data loss — all existing routes, tables, and flows preserved; new features added alongside.

### Backend (`app.py`, `promote_owner.py`)
- **Owner account (verified):** `PRIMARY_OWNER_EMAIL = "omranjoker8@gmail.com"`, `OWNER_EMAILS = {"omranjoker8@gmail.com", "aboudyhassoun3@gmail.com"}` (old kept as secondary to avoid lockout). `python3 promote_owner.py` → `OK: omranjoker8@gmail.com is the primary code-level owner`. Secure process only: code-level ownership + optional `POST /api/admin/promote-owner` (requires current owner token **and** `ARAB_ADMIN_PASSWORD`); never forges tokens, never bypasses auth.
- **New tables (auto-migrated in `init_web_tables`):** `favorites`, `product_ratings`, `coupons`, `cart_items`, `loyalty_points`.
- **New endpoints:** `GET /api/store/search` (q/section/sort/price range), favorites CRUD, ratings + summary, recommendations, cart CRUD + `POST /api/cart/checkout` (multi-item + coupon), coupon validate + admin CRUD, loyalty view/redeem, admin ratings moderation, `GET /robots.txt`, `GET /sitemap.xml` (includes product URLs).
- **Checkout:** `place_order(..., coupon_percent)` — tier discount + coupon stack, loyalty points awarded (1 pt / $10). `POST /api/orders` and cart checkout accept `coupon_code` and increment usage.
- **Security fixes:** removed `ai_image_api_key` leak from public `/api/store/settings` (admin-only now); fixed duplicate `return` in `favicon_fallback`; `float()` parsing guarded (400 instead of 500); global security headers (`X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`); minimal CORS with OPTIONS preflight for `/api/*`.
- **Validation:** qty coercion guarded; coupon percent clamped 0–90.

### Frontend (`site/`)
- **SEO/a11y (all 17 pages):** `maximum-scale=1` removed (pinch-zoom restored), meta description + OG/Twitter + canonical added, `ALOSHI STORE` → `ARAB STORE`, dev hint "تأكد إنه app.py شغّال" reworded, `aria-label` on bell/eye/back buttons, meaningful `alt` on logos/error/banner images.
- **`js/app.js`:** removed stale TODO comment; added `apiFetch`, `Cart`, `Fav`, `submitRating`, `toast`, `syncExchangeRate` (fixes hardcoded 13,800 rate on all pages), `showInfoModal` + `showAbout/showTerms` modal (replaces `alert()`).
- **`store.html`:** server-side live search (`/api/store/search`, 2+ chars, debounced) + sort dropdown (new/rating/price), cart drawer link, splash capped at 3 s (was 650 ms flash-of-error).
- **`products.html`:** filter bar (client filter + sort UI), cart link, fixed broken `<script src>` injection.
- **`product.html`:** favorite button, coupon field in buy sheet, add-to-cart button, ratings card (avg + list + submit), recommendations grid.
- **`cart.html` (new):** cart list, coupon validate, checkout, clear; added to drawers/bottom nav.
- **`account.html`:** loyalty panel (points + redeem).
- **`sw.js`:** offline cache (`arab-store-v2`, core pages) + push kept; old cache purged on activate.
- **`admin.html` + `admin-data.js`:** Coupons section (create/list/delete), Reviews moderation, sales chart canvas (Chart.js, fed by `/api/admin/stats`), auto-load on dashboard.

### Tests (all executed, see transcript)
Backend Flask test client with seeded catalog (1 section, 1 product, 1 category):
- `GET /`, `/robots.txt`, `/sitemap.xml` (contains product URL ✅), `/manifest.json` → 200.
- `/api/store/settings` → 200, **no `ai_image_api_key` leak** ✅; `/api/store/search`, `/sections` → 200.
- Unauthed `/api/cart`, `/favorites`, `/loyalty`, `/api/admin/coupons` → 401 ✅ (auth enforced).
- Register/login/me → 200; favorites add/list, rating submit/summary/list, search with rating, cart add/list, malformed deposit → 400 ✅, cart checkout with 0 balance → clean failure ✅, admin ratings list ✅, coupon create + validate ✅, `promote-owner` with wrong password → 403 ✅.

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export ARAB_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')"
export ARAB_ADMIN_PASSWORD='choose-a-strong-password'
python app.py  # → http://localhost:5000
# owner check:
python3 promote_owner.py
# production: set DATABASE_URL (Supabase pooler), SUPABASE_URL/SERVICE_ROLE_KEY, ARAB_STORAGE_BUCKET, VAPID keys; run:
gunicorn -w 1 --threads 4 -b 127.0.0.1:5000 app:app
```

## Owner-account status
**Verified:** `PRIMARY_OWNER_EMAIL` and `OWNER_EMAILS` include `omranjoker8@gmail.com` as primary; `promote_owner.py` exits 0 with OK. Login as that email → `is_owner_email()=True` → admin auto-login mints `owner=True` → full owner permissions (web-admin management, backups, wipe). No DB/auth-provider access was available in this environment, so no live account row was created — first login with that email automatically receives owner rights via the existing auth system.

## Known limitations / next steps
- Forgot/reset-password flow remains a stub (upstream dead end: nothing writes `link_codes(reset_*)`); needs email/SMS provider to complete.
- Background order monitor + price sync are disabled on Vercel (serverless); use VPS + gunicorn for full functionality.
- Backup/restore/wipe are SQLite-only paths; on Supabase/Postgres use database-level backups.
- Sales chart is an indicator (today-orders seed) — a daily-series endpoint would make it a full time series.
- No automated frontend browser tests were run (no runner here); backend + static checks cover the changes.
