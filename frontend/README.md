# connectED frontend

React, Vite, and TypeScript frontend for connectED.

## Getting started

1. Copy `.env.example` to `.env.local`.
2. Set `VITE_API_BASE_URL` to the FastAPI origin or its `/api/v1` base URL. Either form is accepted.
3. `VITE_API_AUTH_MODE` defaults to `bearer`, as specified by the supplied integration guide. Set it to `cookie` only if the backend is configured for cookie authentication.
4. Run `npm install`, then `npm run dev`.

The Vite development server proxies `/api` requests to the configured API origin. The browser client uses `/api/v1` and never accesses MongoDB directly. Run `npm run build` for a production build.

## Current implementation

- Animated public landing page with an interactive, scoped crosshair and reduced-motion support.
- Login, sign-up, and logout call the FastAPI bearer-token endpoints. Login/registration hold the expiring access token in `sessionStorage`; passwords are not persisted. Dashboard and mentor-discovery routes require a valid client session and return to login when the API rejects that session. Password reset is not implemented.
- Responsive dashboard and mentor-discovery views.
- Profile view/edit supports `headline`, `skills`, and `bio`. Dashboard includes student-only mentor recommendations, request history/details/counts, request creation and sender-only cancellation, faculty recommendations, graph nodes/connections, opportunities, research projects, communities, notifications, and meeting proposals.
- Mentor search routes to discovery; cards display only scores, explanations, skills, and freshness returned by the API.
- Loading, empty, network, and API error states.
- Notifications are read-only because the backend currently exposes no mark-read endpoint. Meeting proposals require an accepted mentorship; responses indicate confirmation only when both participants accept.

## API integration record

The backend source is maintained separately in `connected-backend` (FastAPI app under `backend`). The configured API prefix is `/api/v1`. All protected operations use the bearer token from the login or registration response. The central client validates response fields, displays API failures, and clears the local session after an HTTP 401. Mentor request creation first calls the backend's one-use recommendation approval endpoint, then creates the request.

| Method and path | Request | Response used |
| --- | --- | --- |
| `POST /api/v1/auth/register` | `email`, `password`, `role`, `name` | `access_token`, `token_type`, `expires_in`, `user` |
| `POST /api/v1/auth/login` | `email`, `password` | `access_token`, `token_type`, `expires_in`, `user` |
| `GET /api/v1/auth/me` | — | Authenticated `user` |
| `POST /api/v1/auth/logout` | — | `success`, `message` |
| `GET /api/v1/profiles/me` | — | Profile identity, education/work details, skills, goals, preferences, visibility, verification, freshness |
| `PATCH /api/v1/profiles/me` | Optional `headline`, `skills`, `bio` | Updated profile |
| `GET /api/v1/mentors/recommendations` | `limit`, `offset` | Mentor items, scores, reasons, freshness, pagination |
| `POST /api/v1/mentors/{mentor_id}/approve` | — | Approval status and expiry |
| `GET /api/v1/mentorship-requests` | Optional `status`, `limit`, `offset` | Request items and pagination |
| `GET /api/v1/mentorship-requests/{request_id}` | — | Request details |
| `POST /api/v1/mentorship-requests` | `mentor_id`, `message` (10–1500 characters; prior approval required) | Created request and server status/deadline |
| `POST /api/v1/mentorship-requests/{request_id}/cancel` | — | Cancelled status and message |
| `GET /api/v1/faculty/recommendations` | — | Faculty matches and pagination |
| `GET /api/v1/graph/me` | — | Graph `nodes` and `edges` |
| `GET /api/v1/opportunities` | Optional `type`, `limit`, `offset` | Opportunity items and pagination |
| `GET /api/v1/research-projects` | Optional `research_area`, `limit`, `offset` | Research-project items and pagination |
| `GET /api/v1/communities` | Optional `limit`, `offset` | Community items and pagination |
| `GET /api/v1/notifications` | Optional `limit`, `offset` | Notification items and pagination |
| `GET /api/v1/mentorship-requests/{request_id}/meeting-proposals` | — | Meeting proposals |
| `POST /api/v1/mentorship-requests/{request_id}/meeting-proposals` | `proposed_time`, `timezone_str`, optional `note` | Created proposal |
| `POST /api/v1/meeting-proposals/{proposal_id}/respond` | `action` (`accept` or `decline`), optional `note` | Updated proposal/status |

These routes and schemas were checked against the separately cloned backend source. A running backend and database were not available for live request testing. Frontend configuration uses `VITE_API_BASE_URL` and `VITE_API_AUTH_MODE`; backend configuration reads `MONGODB_URI`, `MONGODB_DATABASE`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `FRONTEND_ORIGIN`, and `ALLOWED_ORIGINS`. The frontend `.env.example` and backend `backend/.env.example` contain safe example values only. Never put MongoDB credentials or backend secrets in frontend environment files.

Start the backend from `connected-backend\backend` after configuring its local `.env` and installing `requirements.txt`:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend from this directory after creating `.env.local` from `.env.example`:

```powershell
npm install
npm run dev
```

There is no frontend test or lint script in `package.json`; `npm run build` runs the TypeScript project build and Vite production build.
