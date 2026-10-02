# API — Frontend Developer Reference

Auth starter: email login, JWT access token, httpOnly refresh cookie, organisation
onboarding via Django Admin. No inventory or purchase APIs.

## Start a new project

The GitHub repo name sets the image: `ghcr.io/<owner>/<repo>` (`:dev` on every
push to `main`, `:latest` and the release version on a GitHub Release).

| What | Where to change it | Starter default |
|------|--------------------|-----------------|
| GHCR image | GitHub repo name | `ghcr.io/<owner>/<repo>` |
| Frontend compose image | `API_IMAGE` in `.env` next to the compose file | `ghcr.io/<owner>/<repo>:dev` |
| Product name | `PROJECT_NAME` | `API` |
| Postgres | `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `dev` |
| Compose project / volume | `name:` and volume in compose files | `dev` / `dev_postgres_data` |
| Refresh cookie | `REFRESH_COOKIE_NAME` | `dev_refresh` |
| From-address | `DEFAULT_FROM_EMAIL` | `noreply@localhost` |
| Frontend URL | `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` |

Keep Postgres values identical in `.env`, `.env.api`, and the compose `db` service.

---

## Base URL

| Environment | URL |
|---|---|
| Local dev (Docker) | `http://localhost:8000` |
| Production | `https://your-railway-domain.up.railway.app` |

```env
# Vite
VITE_API_URL=http://localhost:8000

# Create React App
REACT_APP_API_URL=http://localhost:8000
```

---

## Interactive Docs

| Tool | URL |
|---|---|
| Swagger UI | `http://localhost:8000/api/docs/` |
| Frontend guide | `http://localhost:8000/api/docs/frontend/` |
| ReDoc | `http://localhost:8000/api/redoc/` |
| Raw OpenAPI schema | `http://localhost:8000/api/schema/` |

Docs routes are superuser-only. Log in at `/admin/` first.

---

## Quick Start for Frontend Devs

You don't need to clone the API source. Pull the pre-built image:

```bash
# 1. Copy the frontend compose file into your React project root
cp path/to/this-repo/docker-compose.frontend-dev.yml .

# 2. Django env for the API container
cp path/to/this-repo/.env.frontend.example .env.api

# 3. Image name for Compose (next to the compose file — not .env.api)
echo API_IMAGE=ghcr.io/<owner>/<repo>:dev > .env

# 4. Start the API
docker compose -f docker-compose.frontend-dev.yml up
```

API: http://localhost:8000  
Mailpit inbox: http://localhost:8025

Create a superuser, add an organisation in `/admin/`, then set the password from
the welcome email in Mailpit.

---

## Request Headers

All JSON requests:

```http
Content-Type: application/json
```

Authenticated requests:

```http
Authorization: Bearer <access_token>
```

Cookie requests (`login`, `refresh`, `logout`) must send credentials
(`withCredentials: true` / `credentials: "include"`).

---

## Authentication Flow

### Overview

> **Account creation is admin-only.**  
> A super admin registers organisations (and their first central admin) through
> Django Admin at `/admin/`. The central admin receives a welcome email with a
> *Get Started* link, sets a password at `POST /api/auth/password/set/`, then logs in.

```
[Super admin] creates org + central admin in /admin/
  → Welcome email sent to central admin
  → Central admin clicks "Get Started" link
  → POST /api/auth/password/set/  (uid + token from URL + new_password)
  → POST /api/auth/login/         (email + password)
  → JSON { access } + httpOnly refresh cookie
Use the access token for API calls (expires in 15 min)
POST /api/auth/token/refresh/ with the cookie (empty body) for a new access token
On logout → POST /api/auth/logout/ (cookie is read and cleared)
```

### JWT Token Claims

The access token payload includes:

```json
{
  "user_id": "uuid",
  "user_type": "central_admin",
  "org_id": "uuid-of-org",
  "org_suffix": "acme_west"
}
```

For super admins: `org_id` and `org_suffix` are `null`.

---

### ~~Register (disabled)~~

`POST /api/auth/register/` is **not available**. Accounts are created by super
admins through Django Admin.

---

### 1. Set Password — Get-Started Link

```
POST /api/auth/password/set/
```

**Request body:**
```json
{
  "uid": "<uid from URL>",
  "token": "<token from URL>",
  "new_password": "StrongPass123!",
  "new_password2": "StrongPass123!"
}
```

**Success `200`:**
```json
{ "detail": "Password set successfully. You can now log in." }
```

**Errors `400`:**
```json
{
  "token": ["Link is invalid or has expired. Request a new welcome email."],
  "new_password2": ["Passwords do not match."]
}
```

The link expires in **7 days** and is one-time.

---

### 2. Login

```
POST /api/auth/login/
```

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "StrongPass123!"
}
```

**Success `200`:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGci..."
}
```

Set-Cookie: httpOnly refresh cookie (`REFRESH_COOKIE_NAME`, default `dev_refresh`),
path `/api/auth/`, SameSite Lax, 7 days. `refresh` is **not** in the JSON body.

**Error `401`:**
```json
{ "detail": "No active account found with the given credentials." }
```

**Error `400`** (organisation suspended):
```json
{
  "non_field_errors": [
    "Your organisation has been suspended. Please contact your administrator."
  ]
}
```

**Error `429`:** login is throttled (10/min production, 100/min development).

---

### 3. Refresh Access Token

Access tokens expire in **15 minutes**. Send the cookie; the body is empty.

```
POST /api/auth/token/refresh/
```

**Request body:** `{}` — a `refresh` field in JSON is ignored.

**Success `200`:**
```json
{ "access": "new_access_token..." }
```

The cookie is rotated. The previous refresh token is blacklisted.

**Error `401`:**
```json
{ "detail": "Refresh cookie is missing.", "code": "token_not_valid" }
```

---

### 4. Verify Token

```
POST /api/auth/token/verify/
```

```json
{ "token": "<access_token>" }
```

**Success `200`:** `{}`  
**Error `401`:** Token is invalid or expired.

---

### 5. Logout

Blacklists the refresh cookie and clears it. Auth header is optional.

```
POST /api/auth/logout/
```

**Request body:** `{}`

**Success `200`:**
```json
{ "detail": "Successfully logged out." }
```

---

## User Profile

### Get My Profile

```
GET /api/auth/me/
Authorization: Bearer <access_token>
```

**Success `200`:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "date_joined": "2026-09-08T12:00:00Z",
  "updated_at": "2026-09-08T12:00:00Z",
  "profile": {
    "user_type": "central_admin",
    "first_name": "Jane",
    "last_name": "Doe",
    "phone": "+1234567890",
    "full_name": "Jane Doe"
  },
  "org": {
    "id": "org-uuid",
    "name": "Acme Corp",
    "org_suffix": "acme_west",
    "location": "New York",
    "is_active": true,
    "registered_on": "2026-09-01T10:00:00Z"
  }
}
```

For super admins `org` is `null`.

---

### Update My Profile

```
PATCH /api/auth/me/
Authorization: Bearer <access_token>
```

```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "phone": "+919876543210"
}
```

`email`, `org`, and `user_type` are read-only.

**Success `200`:** Returns the updated object.

---

## Password Management

### Change Password (authenticated)

```
POST /api/auth/password/change/
Authorization: Bearer <access_token>
```

```json
{
  "old_password": "OldPass123!",
  "new_password": "NewPass456!",
  "new_password2": "NewPass456!"
}
```

**Success `200`:**
```json
{ "detail": "Password updated successfully." }
```

Outstanding refresh tokens are blacklisted and the cookie is cleared.

**Error `400`:**
```json
{ "old_password": ["Old password is incorrect."] }
```

---

### Forgot Password — Request Reset Link

```
POST /api/auth/password/reset/
```

```json
{ "email": "user@example.com" }
```

**Success `200`** (always, even if the email does not exist):
```json
{ "detail": "If an account with that email exists, a reset link has been sent." }
```

In development, open Mailpit at http://localhost:8025.

---

### Forgot Password — Confirm Reset

```
POST /api/auth/password/reset/confirm/
```

```json
{
  "uid": "<uid from email link>",
  "token": "<token from email link>",
  "new_password": "NewPass789!",
  "new_password2": "NewPass789!"
}
```

**Success `200`:**
```json
{ "detail": "Password has been reset successfully." }
```

Outstanding refresh tokens for that user are blacklisted.

**Error `400`:**
```json
{ "token": ["Reset link is invalid or has expired."] }
```

---

## System

### Health Check

```
GET /api/health/
```

No authentication required.

**Success `200`:**
```json
{ "status": "ok", "db": "ok", "redis": "ok" }
```

**Degraded `503`:**
```json
{ "status": "degraded", "db": "ok", "redis": "error" }
```

---

## Error Response Format

### Field validation errors
```json
{
  "email": ["Enter a valid email address."],
  "password": ["This password is too short."]
}
```

### Non-field errors
```json
{ "detail": "Authentication credentials were not provided." }
```

### Common HTTP status codes

| Code | Meaning |
|---|---|
| `200` | Success |
| `201` | Created |
| `400` | Validation error |
| `401` | Not authenticated or token expired |
| `403` | Authenticated but forbidden |
| `404` | Not found |
| `429` | Rate limit exceeded |
| `500` | Server error |
| `503` | Service unavailable |

---

## Rate Limiting

**`429 Too Many Requests`**
```json
{ "detail": "Request was throttled. Expected available in 42 seconds." }
```

| Limit | Rate |
|---|---|
| Unauthenticated | 100 requests / day |
| Authenticated | 1000 requests / day |
| Auth endpoints (login, refresh, logout, reset, set-password) | 10 / min (100 / min in development) |

```js
if (response.status === 429) {
  const retryAfter = response.headers.get('Retry-After');
}
```

---

## Pagination

List endpoints return:

```json
{
  "count": 100,
  "next": "http://localhost:8000/api/some-list/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

Default page size: **20**. Use `?page=2`.

---

## CORS

Default origins:

- `http://localhost:3000`
- `http://localhost:5173`

`CORS_ALLOW_CREDENTIALS` is on so the refresh cookie is sent. Production:
set `CORS_ALLOWED_ORIGINS` to the deployed frontend origin(s).

---

## Token Storage

| Token | Where |
|---|---|
| Access | Memory (React state / context). Put it on `Authorization: Bearer`. |
| Refresh | HttpOnly cookie set by the API. Browser sends it with `withCredentials`. |

Do not put the refresh token in `localStorage` or in a JSON body.

---

## Code Examples

### Axios setup

```js
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
});

let accessToken = null;
export const setAccessToken = (t) => { accessToken = t; };

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        const { data } = await axios.post(
          `${import.meta.env.VITE_API_URL}/api/auth/token/refresh/`,
          {},
          { withCredentials: true },
        );
        setAccessToken(data.access);
        original.headers.Authorization = `Bearer ${data.access}`;
        return api(original);
      } catch {
        setAccessToken(null);
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
```

### Login

```js
const login = async (email, password) => {
  const { data } = await api.post('/api/auth/login/', { email, password });
  setAccessToken(data.access);
  return data;
};
```

### Get profile

```js
const getProfile = async () => {
  const { data } = await api.get('/api/auth/me/');
  return data;
};
```

### Logout

```js
const logout = async () => {
  await api.post('/api/auth/logout/');
  setAccessToken(null);
};
```

### Forgot password

```js
const forgotPassword = async (email) => {
  await api.post('/api/auth/password/reset/', { email });
};
```

### Reset password

```js
const resetPassword = async (uid, token, newPassword, newPassword2) => {
  await api.post('/api/auth/password/reset/confirm/', {
    uid,
    token,
    new_password: newPassword,
    new_password2: newPassword2,
  });
};
```

---

## Development Email

Mailpit inbox: **http://localhost:8025** (SMTP on port 1025). Welcome and reset
emails land there in development.

---

## Changelog

| Version | Date | Notes |
|---|---|---|
| 1.0.0 | 2026-09-08 | Initial release |
| 1.1.0 | 2026-10-02 | HttpOnly refresh cookie, login throttle, cookie-only refresh |
