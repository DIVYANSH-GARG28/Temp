<div align="center">

# connectED

### Find your people. Find your way.

An alumni and student networking platform for mentorship, career guidance, research, and meaningful professional connections.

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/UI-React-61DAFB?logo=react&logoColor=20232A)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.9-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)

</div>

---

## Contents

- [About](#about)
- [What you can do](#what-you-can-do)
- [Technology](#technology)
- [Project structure](#project-structure)
- [Run locally](#run-locally)
- [Tests and production build](#tests-and-production-build)
- [API overview](#api-overview)
- [Configuration and security](#configuration-and-security)
- [Contributing](#contributing)

## About

Finding the right mentor or professional connection can be difficult when alumni information lives in a static directory. **connectED** helps students discover relevant alumni and faculty, request mentorship, and explore opportunities through a connected professional network.

The project includes a React web app, a FastAPI backend, MongoDB persistence, profile-based recommendations, and a knowledge graph API.

## What you can do

- Discover alumni mentors and review recommendation explanations.
- Create profiles and manage mentorship requests.
- Explore faculty recommendations, research projects, and career opportunities.
- View a personal network graph and browse communities.
- Coordinate mentorship meetings and receive notifications.
- Link Telegram accounts for bot-based interactions.

## Technology

| Area | Technologies |
| --- | --- |
| Frontend | React, TypeScript, Vite, React Router |
| Backend | Python, FastAPI, Pydantic, Uvicorn |
| Data and authentication | MongoDB, PyMongo, JWT, bcrypt |
| Recommendations and graph | Semantic matching with a fallback mode, NetworkX |
| Testing | pytest, pytest-asyncio |

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/v1/            # Versioned API routes
│   │   ├── core/              # Configuration, database, security
│   │   ├── repositories/      # MongoDB data access
│   │   ├── schemas/           # Request and response models
│   │   └── services/          # Application and matching logic
│   ├── scripts/               # Seed data and webhook utilities
│   ├── tests/                 # Backend test suite
│   └── requirements.txt
├── frontend/
│   ├── src/pages/             # Landing, auth, dashboard, mentors
│   ├── src/components/        # Shared UI components
│   └── package.json
├── recommendation-engine/     # Recommendation and profile-processing modules
└── knowledge_graph_visualization.png
```

## Run locally

### Prerequisites

- Python 3.12 or newer
- Node.js and npm
- MongoDB running locally or an accessible MongoDB connection string

### 1. Configure and start the backend

In PowerShell, from the repository root:

```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend\.env` and set `MONGODB_URI` and `MONGODB_DATABASE` for your MongoDB instance. For any deployment beyond local development, replace the example `JWT_SECRET_KEY` with a secure secret and configure allowed frontend origins.

Start the API:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The backend provides interactive API references at [Swagger UI](http://localhost:8000/docs) and [ReDoc](http://localhost:8000/redoc). Its OpenAPI contract is in [`backend/openapi.json`](backend/openapi.json).

### 2. Configure and start the frontend

In a second PowerShell window, from the repository root:

```powershell
cd frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

The frontend is served at [http://localhost:5173](http://localhost:5173). The example configuration points it to the local API at `http://localhost:8000/api/v1`; adjust `VITE_API_BASE_URL` in `frontend\.env.local` if your backend runs elsewhere.

## Tests and production build

Run the backend tests:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pytest -v
```

Build the frontend for production:

```powershell
cd frontend
npm run build
```

## API overview

All application endpoints are versioned under `/api/v1`. The API includes authentication, profiles, mentor and faculty recommendations, mentorship requests and meeting proposals, research projects, opportunities, personal graph data, communities, notifications, and Telegram integration. For exact routes, request schemas, and response formats, use the [OpenAPI contract](backend/openapi.json) or run the backend and open `/docs`.

## Configuration and security

- Backend settings are loaded from `backend/.env`; use `backend/.env.example` as a starting point.
- Frontend settings use `frontend/.env.local`. Only expose frontend variables prefixed with `VITE_`; never put backend credentials or secrets there.
- Do not commit `.env`, `.env.local`, access tokens, or production credentials.

## Contributing

1. Create a branch for your change.
2. Keep frontend and backend behavior aligned with the API contract.
3. Run the relevant backend tests and frontend production build.
4. Open a pull request describing the change and how it was verified.

---

<div align="center">

Built to make meaningful connections easier.

</div>
