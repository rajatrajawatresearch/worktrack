# WorkTrack

A lightweight, multi-company **employee attendance & location-based workforce management** platform.
Employees punch in / take breaks / punch out from their phone; the **backend validates their GPS
location** against the company's configured work location before recording anything. Company admins
manage employees and view live attendance + reports; super admins manage companies.

- **Backend, database, auth and business logic are fully self-owned** — no Firebase / Supabase /
  Appwrite / BaaS. Just FastAPI + PostgreSQL that you control.
- Designed for a realistic scale: ~50 companies, ~200 employees each (~10k total). Not over-engineered.

## Table of contents
1. [Features](#features) · 2. [Tech stack](#tech-stack) · 3. [Project structure](#project-structure)
4. [Quick start (Docker)](#quick-start-docker) · 5. [Local development](#local-development)
6. [Environment variables](#environment-variables) · 7. [Database & migrations](#database--migrations)
8. [Testing](#testing) · 9. [Deployment](#deployment) · 10. [Free deployment — what YOU need to do](#free-deployment--what-you-need-to-do)
11. [Backups](#backups) · 12. [API](#api) · 13. [Known limitations](#known-limitations) · 14. [Future improvements](#future-improvements)

---

## Features

**Employee (mobile)** — login, view today's attendance & live working time, punch in, start/end break,
punch out (all GPS-validated by the backend), attendance history, profile.

**Company admin (web)** — manage employees (create / edit / deactivate / reset password), configure
company settings & work location/radius, live dashboard (present / absent / working / on-break /
completed), attendance table with filters, reports + CSV export.

**Super admin (web)** — create & manage companies, provision company admins, configure locations &
radius, system-level stats.

**Cross-cutting** — RBAC (`SUPER_ADMIN` / `COMPANY_ADMIN` / `EMPLOYEE`), strict multi-tenant isolation
(a company can never read another's data), audit logging, consistent JSON error envelope,
OpenAPI/Swagger docs.

## Tech stack
| Layer | Tech |
|---|---|
| Mobile | React Native + Expo + TypeScript |
| Admin web | React + Vite + TypeScript (hand-written CSS, minimal deps) |
| Backend | Python, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic |
| Database | PostgreSQL 16 (portable models also run on SQLite for tests) |
| Auth | JWT access (15m) + refresh (30d, rotated & server-revocable), Argon2 password hashing |
| Infra | Docker, Docker Compose, Nginx | 
| CI | GitHub Actions (ruff + pytest, frontend build/typecheck) |

## Project structure
```
annaapp/
  backend/        FastAPI app (api / services / repositories / models / schemas / core), tests, alembic
  admin/          React + Vite + TS admin dashboard
  mobile/         Expo + React Native + TS employee app
  infrastructure/ nginx config, backup/restore scripts
  docs/           architecture, product, database, api, security, attendance-rules, deployment, testing, CONTRACT
  .github/workflows/ci.yml
  docker-compose.yml            (development)
  docker-compose.prod.yml       (production: nginx + backend + postgres)
  render.yaml                   (free-tier cloud blueprint)
  .env.example
```
Backend follows clean layering: **API → Service → Repository → SQLAlchemy → PostgreSQL** (no business
logic in route handlers, and none in the mobile app — the backend is the final authority on GPS).

## Quick start (Docker)
```bash
cp .env.example .env            # optional: edit secrets
docker compose up --build
```
This starts PostgreSQL + the API, **runs migrations automatically**, and **seeds a demo company**.
- API: http://localhost:8000  ·  Swagger: http://localhost:8000/docs  ·  Health: http://localhost:8000/health

**Seeded demo logins** (dev only — change in production):
| Role | Email | Password |
|---|---|---|
| Super admin | `superadmin@worktrack.local` | `ChangeMe123!` |
| Company admin | `admin@demo.local` | `Admin123!` |
| Employee | `john@demo.local` | `Employee123!` |

Demo work location: Bengaluru `12.9716, 77.5946`, radius `150 m`. To test a punch-in, send coordinates
within 150 m of that point (the mobile app uses your real GPS).

## Local development

**Backend**
```bash
cd backend
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL="postgresql+psycopg://worktrack:worktrack@localhost:5432/worktrack"
export JWT_SECRET="$(openssl rand -hex 32)"
alembic upgrade head
python -m app.seed --demo          # create super admin + demo company
uvicorn app.main:app --reload      # http://localhost:8000/docs
```

**Admin web**
```bash
cd admin
cp .env.example .env                # set VITE_API_BASE_URL=http://localhost:8000/api/v1
npm install
npm run dev                         # http://localhost:5173
```

**Mobile (Expo)**
```bash
cd mobile
cp .env.example .env                # set EXPO_PUBLIC_API_BASE_URL to your machine LAN IP:8000/api/v1
npm install
npm start                           # open in Expo Go / emulator
```
> On a physical phone use your computer's LAN IP (e.g. `http://192.168.1.20:8000/api/v1`), not
> `localhost`. Android emulator: `http://10.0.2.2:8000/api/v1`.

## Environment variables
See [`.env.example`](.env.example). Key ones:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Postgres DSN. `postgres://` / `postgresql://` are auto-normalized to `postgresql+psycopg://`. |
| `JWT_SECRET` | Long random secret (`openssl rand -hex 32`). **Required in production.** |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` / `JWT_REFRESH_TOKEN_EXPIRE_DAYS` | Token lifetimes (default 15 / 30). |
| `CORS_ORIGINS` | Comma-separated allowed origins for the admin app. |
| `DEFAULT_ALLOWED_RADIUS_METERS` (150) / `MAX_ACCEPTABLE_ACCURACY_METERS` (100) / `DEFAULT_TIMEZONE` (Asia/Kolkata) | Attendance policy defaults; overridable per company. |
| `LOGIN_RATE_LIMIT_ATTEMPTS` / `LOGIN_RATE_LIMIT_WINDOW_SECONDS` | Login throttling (5 / 300). |
| `SUPERADMIN_EMAIL` / `SUPERADMIN_PASSWORD` | Used by the seed script only. |
| `SEED_SUPERADMIN` / `SEED_DEMO` | `1` to auto-seed on container start. |
| `VITE_API_BASE_URL` (admin) / `EXPO_PUBLIC_API_BASE_URL` (mobile) | API base incl. `/api/v1`. |

Never commit a real `.env`.

## Database & migrations
Migrations use **Alembic**. Never edit the production schema by hand.
```bash
cd backend
alembic upgrade head                                   # apply all migrations
alembic revision --autogenerate -m "add xyz"           # create a new migration after model changes
alembic downgrade -1                                    # roll back one migration
alembic history                                         # list revisions
```
The baseline migration `0001` materializes the full schema from the models. Tables:
`users, companies, company_locations, employees, attendance, attendance_breaks, refresh_tokens,
audit_logs` + future scaffolding `shifts, holidays, leave_requests`. See [`docs/database.md`](docs/database.md).

## Testing
```bash
cd backend
. .venv/bin/activate
ruff check .                # lint
pytest                      # 39 tests (auth, RBAC, tenant isolation, GPS, attendance, working-time, reports)
```
Tests run on in-memory SQLite (no Docker needed). Coverage highlights: **Company A cannot access
Company B**, GPS radius 50/149/151 m + poor-accuracy + missing/invalid coords, duplicate-attendance
prevention, invalid state transitions, working-time math, CSV export. See [`docs/testing.md`](docs/testing.md).

Frontend: `cd admin && npm run build` · `cd mobile && npm run typecheck`.

## Deployment

### Self-hosted VPS (fully owned — recommended per spec)
```bash
# on the server
git clone <your repo> /opt/worktrack && cd /opt/worktrack
cp .env.example .env         # set strong JWT_SECRET, POSTGRES_PASSWORD, CORS_ORIGINS, SUPERADMIN_*
cd admin && npm install && npm run build && cd ..     # build admin static files
docker compose -f docker-compose.prod.yml up -d --build
```
Topology: **Internet → Nginx (80/443) → FastAPI (internal) → PostgreSQL (internal, not exposed)**.
Nginx serves the admin SPA, proxies `/api`, `/docs`, `/health`, adds security headers and login
rate-limiting. For HTTPS, mount certs and enable the 443 block in `infrastructure/nginx/default.conf`
(use Let's Encrypt / Caddy / a reverse proxy of your choice). Full guide: [`docs/deployment.md`](docs/deployment.md).

### Free cloud (fastest to a live URL)
Uses `render.yaml` (Render.com free tier). This uses a **managed** Postgres — convenient and free,
but a departure from the "self-owned DB" preference; use the VPS path if you must own the DB entirely.

## Free deployment — what YOU need to do
The code + configs are ready. These steps need **your** accounts/clicks (I can't create third-party
accounts or authenticate browsers for you):

**Backend + DB + Admin on Render (one free account):**
1. Push is already done to `github.com/neurosynthlabs/annaapp` (private).
2. Go to **render.com** → sign up / log in (free) with the account that owns the repo.
3. **New + → Blueprint** → select `neurosynthlabs/annaapp` → Render reads `render.yaml` and proposes:
   a free Postgres, the API (Docker), and the admin static site.
4. When prompted, set the `sync:false` env vars: `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD`,
   `CORS_ORIGINS` (your admin URL), and admin's `VITE_API_BASE_URL` (`https://<api>.onrender.com/api/v1`).
5. Click **Apply**. First deploy runs migrations + seeds. Log in with your superadmin creds.
   > Free web services sleep on inactivity (a few seconds cold start on first request).

**Admin alternatively on Vercel/Netlify (free):** point it at the `admin/` folder, build `npm run build`,
output `dist`, and set `VITE_API_BASE_URL`. (Vercel CLI is installed — run `vercel login` yourself, then
`cd admin && vercel` to deploy.)

**Mobile (free):** `cd mobile && npx expo start` and open in **Expo Go** on your phone (set
`EXPO_PUBLIC_API_BASE_URL` to your deployed API). For installable builds, create a free **Expo (EAS)**
account and run `eas build` — the build minutes free tier applies.

If you'd rather I target a specific platform (Fly.io, Railway, a particular VPS), tell me and I'll add
the exact config.

## Backups
```bash
./infrastructure/scripts/backup.sh                 # gzip pg_dump into ./backups, prunes >7 days
./infrastructure/scripts/restore.sh ./backups/worktrack_YYYYMMDD_HHMMSS.sql.gz
# schedule daily via cron:  0 2 * * * cd /opt/worktrack && ./infrastructure/scripts/backup.sh
```

## API
Interactive docs at `/docs` (Swagger) and `/redoc`. Machine-readable contract in
[`docs/CONTRACT.md`](docs/CONTRACT.md); full reference in [`docs/api.md`](docs/api.md). Base path
`/api/v1`. Consistent envelopes:
```json
{ "success": true, "data": { } }
{ "success": false, "error": { "code": "OUTSIDE_ATTENDANCE_RADIUS", "message": "…", "details": { "distance_meters": 420, "allowed_radius_meters": 150 } } }
```

## Known limitations
- **GPS spoofing** can't be fully prevented in V1 by coordinates alone. The system records GPS +
  accuracy + server timestamp and validates distance server-side; stronger anti-spoofing (mock-location
  detection, device binding/attestation, consistency checks) is designed-for but not implemented.
- Login rate limiting is in-memory (per process) — fine at this scale; front it with Nginx limiting
  (already configured) or add a shared store if you scale to many workers.
- Reports are generated in-process (CSV) — appropriate for the target scale, not a BI engine.
- Free-tier hosting uses a managed DB and sleeping services (cold starts).
- One primary work location per company is used for validation (multi-location schema exists for later).

## Future improvements
Leave management, shift scheduling, holiday calendars, multiple geofenced offices, overtime, approval
workflows, push notifications, payroll integration, face verification, device binding, and suspicious-
attendance detection. The schema and architecture are structured so these can be added as modules
without disruptive migrations.

---
Built as a maintainable product, not a demo: simple, secure, correct attendance math, strict
multi-tenant isolation, reliable server-side GPS validation, low infra cost.
