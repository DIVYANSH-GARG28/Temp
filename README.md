# connectED

connectED is an AI-powered professional networking platform connecting students, alumni, faculty, recruiters, and startup founders. It transforms a static alumni directory into an intelligent network for mentorship, career guidance, research, jobs, and collaboration.

---

## Repository Structure

```
.
├── backend/                         # FastAPI + MongoDB async backend
│   ├── app/                         # Application source code
│   │   ├── api/v1/                  # REST API endpoints (25 operations)
│   │   ├── core/                    # Config, Security, DB, Exceptions
│   │   ├── jobs/                    # Expiration & Outbox workers
│   │   ├── repositories/            # PyMongo Async repositories
│   │   ├── schemas/                 # Pydantic v2 schemas
│   │   └── services/                # Business logic & AI matching
│   ├── tests/                       # Automated pytest suite (53 tests)
│   ├── scripts/                     # Seed data & Webhook management scripts
│   ├── openapi.json                 # OpenAPI 3.1.0 contract (authoritative)
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                 # Environment template
│   └── README.md                    # Backend documentation & API contract
└── README.md                        # Project root documentation
```

---

## Quickstart — Running the Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Interactive API documentation will be available at:
- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`

---

## Running Backend Tests

```bash
cd backend
pytest -v
```

---

## Frontend Integration

For API contracts, models, authentication headers, and error response schemas, refer to:
- **Interactive Swagger Docs:** `http://localhost:8000/docs`
- **OpenAPI 3.1.0 JSON Schema:** [`backend/openapi.json`](backend/openapi.json)
