# WorkTrack — API & Data Contract (Source of Truth)

> This file is the **canonical contract** shared by backend, admin web, and mobile.
> All clients MUST follow the shapes below. The backend is the final authority.

## Base

- Base URL: `/api/v1`
- All responses are JSON.
- Auth: `Authorization: Bearer <access_token>` header on protected routes.
- Timestamps in responses are ISO-8601 UTC strings (e.g. `2026-09-13T04:02:11Z`).
- IDs are UUID strings.

## Response envelopes

Success (single):
```json
{ "success": true, "data": { ... } }
```
Success (list, paginated):
```json
{ "success": true, "data": [ ... ], "pagination": { "page": 1, "page_size": 20, "total": 137, "total_pages": 7 } }
```
Error (always this shape — never a raw stack trace):
```json
{ "success": false, "error": { "code": "OUTSIDE_ATTENDANCE_RADIUS", "message": "You are outside the allowed attendance area.", "details": { "distance_meters": 420, "allowed_radius_meters": 150 } } }
```

## Error codes

| HTTP | code | meaning |
|-----|------|---------|
| 400 | `VALIDATION_ERROR` | request body/query invalid |
| 401 | `INVALID_CREDENTIALS` | login failed |
| 401 | `NOT_AUTHENTICATED` | missing/invalid/expired access token |
| 401 | `INVALID_REFRESH_TOKEN` | refresh token invalid/expired/revoked |
| 403 | `FORBIDDEN` | authenticated but not allowed (role/tenant) |
| 404 | `NOT_FOUND` | resource missing or not in your tenant |
| 409 | `CONFLICT` | duplicate (e.g. employee_code, company code) |
| 409 | `ALREADY_PUNCHED_IN` | attendance already open today |
| 409 | `NOT_PUNCHED_IN` | no open attendance |
| 409 | `ALREADY_ON_BREAK` | active break exists |
| 409 | `NOT_ON_BREAK` | no active break |
| 409 | `ALREADY_PUNCHED_OUT` | attendance already completed |
| 409 | `ON_BREAK_CANNOT_PUNCH_OUT` | must end break first |
| 422 | `GPS_ACCURACY_TOO_LOW` | accuracy worse than allowed (details: accuracy, max) |
| 422 | `OUTSIDE_ATTENDANCE_RADIUS` | too far (details: distance_meters, allowed_radius_meters) |
| 422 | `INVALID_COORDINATES` | lat/long out of range |
| 429 | `RATE_LIMITED` | too many login attempts |
| 500 | `INTERNAL_ERROR` | unexpected (message is generic) |

## Roles

`SUPER_ADMIN` | `COMPANY_ADMIN` | `EMPLOYEE`

## JWT payload (access & refresh)

```json
{ "sub": "<user_id>", "role": "EMPLOYEE", "company_id": "<uuid|null>", "type": "access|refresh", "jti": "<uuid>", "iat": 1700000000, "exp": 1700000900 }
```
`company_id` is null for SUPER_ADMIN. Clients MUST NOT send company_id in bodies; server derives it from the token.

## Attendance status enum
`IN_PROGRESS` | `ON_BREAK` | `COMPLETED` | `ABSENT` | `PRESENT` | `MISSED_PUNCH` | `MANUAL_ADJUSTMENT`

## Break type enum
`REGULAR` | `LUNCH` | `OTHER`

## Endpoints

### Auth
- `POST /auth/login` body `{ "email", "password" }` → `{ access_token, refresh_token, token_type:"bearer", user:{ id, email, role, company_id } }`
- `POST /auth/refresh` body `{ "refresh_token" }` → `{ access_token, refresh_token, token_type }` (refresh rotated)
- `POST /auth/logout` body `{ "refresh_token" }` → `{ "revoked": true }`
- `GET /me` → `{ user:{...}, employee:{...}|null, company:{...}|null }`

### Attendance (EMPLOYEE)
Location body for punch/break actions:
```json
{ "latitude": 12.9716, "longitude": 77.5946, "accuracy": 18.0, "client_timestamp": "2026-09-13T04:02:00Z" }
```
- `GET  /attendance/today` → today's attendance state (or null-ish empty state) + computed `current_work_minutes`
- `POST /attendance/punch-in` (location) → attendance record
- `POST /attendance/break/start` (location) → attendance record with active break
- `POST /attendance/break/end` (location) → attendance record
- `POST /attendance/punch-out` (location) → attendance record with totals
- `GET  /attendance/history?from=&to=&page=&page_size=` → paginated attendance list

### Employees (COMPANY_ADMIN, SUPER_ADMIN)
- `GET   /employees?search=&department=&status=&page=&page_size=` (company-scoped)
- `POST  /employees` `{ email, phone?, first_name, last_name, employee_code, department?, designation?, joining_date?, password }`
- `GET   /employees/{id}`
- `PATCH /employees/{id}` (partial)
- `POST  /employees/{id}/reset-password` `{ new_password }`
- `GET   /employees/{id}/attendance?from=&to=&page=&page_size=`

### Companies (SUPER_ADMIN; COMPANY_ADMIN read-own + settings)
- `GET   /companies` (super: all paginated; company_admin: list containing only own company)
- `POST  /companies` `{ name, code, timezone?, admin_email, admin_password, location:{ name, address?, latitude, longitude, allowed_radius_meters? } }` → creates company + primary location + COMPANY_ADMIN user
- `GET   /companies/{id}`
- `PATCH /companies/{id}` `{ name?, status?, timezone?, max_accuracy_meters?, work_start_time?, work_end_time?, late_grace_minutes?, standard_work_minutes? }`
- `GET   /companies/{id}/locations`
- `POST  /companies/{id}/locations`
- `PATCH /companies/{id}/locations/{loc_id}`

### Dashboard & admin attendance (COMPANY_ADMIN, SUPER_ADMIN)
- `GET /dashboard/summary?date=YYYY-MM-DD` → `{ total_employees, present, absent, in_progress, on_break, completed }`
- `GET /attendance?date=&employee_id=&department=&status=&page=&page_size=` (admin list, company-scoped)
- `GET /attendance/{id}` (admin detail, tenant-checked)

### Reports (COMPANY_ADMIN, SUPER_ADMIN)
- `GET /reports/attendance?type=daily|monthly|employee|late|missing|hours&from=&to=&employee_id=&format=json|csv`
  - `format=csv` → `text/csv` download; `format=json` → paginated JSON.

### System (SUPER_ADMIN)
- `GET /system/stats` → `{ companies, users, employees, attendance_today }`

### Health
- `GET /health` (public) → `{ status:"ok" }`

## Config constants (backend, overridable per-company where noted)
- `DEFAULT_ALLOWED_RADIUS_METERS = 150` (per company_location)
- `MAX_ACCEPTABLE_ACCURACY_METERS = 100` (per company)
- `DEFAULT_TIMEZONE = "Asia/Kolkata"` (per company)
- access token 15 min, refresh 30 days.

## Distance rule
Haversine between employee GPS and the company's primary/active location.
`valid` iff `distance_meters <= location.allowed_radius_meters` AND `accuracy <= company.max_accuracy_meters`.
