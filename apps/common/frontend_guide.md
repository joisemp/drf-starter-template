# Frontend guide (React + Vite + TypeScript)

Auth starter for a JWT API with an **httpOnly refresh cookie**. Endpoint JSON lives in
[`FRONTEND_API.md`](../../FRONTEND_API.md). The **Current endpoints** table below
is generated from the live OpenAPI schema.

## Start a new project

Copy this repository (or use it as a GitHub template). Then rename the starter
defaults — they are env vars and compose names, not hardcoded product names.

| What | Variable / file | Starter default |
|------|-----------------|-----------------|
| GitHub repo → GHCR image | repo name | `ghcr.io/<owner>/<repo>` |
| Frontend compose image | `API_IMAGE` in `.env` next to the compose file | `ghcr.io/<owner>/<repo>:dev` |
| Product name (emails, Swagger) | `PROJECT_NAME` | `API` |
| Postgres | `POSTGRES_DB` / `USER` / `PASSWORD` | `dev` |
| Compose project | `name:` in compose files | `dev`, `frontend-dev`, `fullstack` |
| Refresh cookie | `REFRESH_COOKIE_NAME` | `dev_refresh` |
| From-address | `DEFAULT_FROM_EMAIL` | `noreply@localhost` |
| Frontend origin | `FRONTEND_URL`, `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` |

Keep `POSTGRES_*` identical in `.env`, `.env.api`, and the compose `db` service.
The image tag `:dev` is published on every push to `main`.

## Auth contract

1. Superuser creates an organisation (and its first central admin) in `/admin/`.
2. Welcome email → `{FRONTEND_URL}/get-started?uid=...&token=...`
3. `POST /api/auth/password/set/` then `POST /api/auth/login/`
4. Login JSON is `{ "access": "..." }` only. Refresh is an httpOnly cookie on
   `/api/auth/` (`withCredentials: true`).
5. Access token: 15 minutes, `Authorization: Bearer`. Refresh: 7 days, rotated.
6. `POST /api/auth/token/refresh/` with an empty body and the cookie.
7. Logout and password change/reset blacklist outstanding refresh tokens.

Public `POST /api/auth/register/` does not exist.

## Axios client

```ts
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
});

let accessToken: string | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
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
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  },
);

export default api;
```

Never store the refresh token in `localStorage`. Never send it in JSON.

## Copy-paste helpers

```ts
export async function login(email: string, password: string) {
  const { data } = await api.post<{ access: string }>("/api/auth/login/", {
    email,
    password,
  });
  setAccessToken(data.access);
  return data;
}

export async function logout() {
  await api.post("/api/auth/logout/");
  setAccessToken(null);
}

export async function getMe() {
  const { data } = await api.get("/api/auth/me/");
  return data;
}

export async function setPassword(uid: string, token: string, password: string) {
  await api.post("/api/auth/password/set/", {
    uid,
    token,
    new_password: password,
    new_password2: password,
  });
}

export async function requestPasswordReset(email: string) {
  await api.post("/api/auth/password/reset/", { email });
}

export async function confirmPasswordReset(
  uid: string,
  token: string,
  password: string,
) {
  await api.post("/api/auth/password/reset/confirm/", {
    uid,
    token,
    new_password: password,
    new_password2: password,
  });
}
```

## Practice locally

1. Copy `docker-compose.frontend-dev.yml` into the React project.
2. Copy `.env.frontend.example` to `.env.api` (Django) and put `API_IMAGE` in
   `.env` next to the compose file.
3. `docker compose -f docker-compose.frontend-dev.yml up`
4. Create a superuser, log in at `/admin/`, add an organisation.
5. Open Mailpit at http://localhost:8025 for the get-started and reset links.

Swagger (superuser session): http://localhost:8000/api/docs/

Auth endpoints are throttled at 10/min in production and 100/min in development
(`429` when exceeded).
