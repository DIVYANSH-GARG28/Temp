# connectED Backend

connectED is an AI-powered professional networking platform connecting students, alumni, faculty, recruiters, and startup founders. It transforms a static alumni directory into an intelligent network for mentorship, career guidance, research, jobs, and collaboration.

---

## 1. Technology Stack

- **Language:** Python 3.12+ (tested on Python 3.14)
- **Framework:** FastAPI (ASGI async web server)
- **Database:** MongoDB (via non-blocking `motor` async driver)
- **Data Validation & Serialization:** Pydantic v2
- **Authentication:** Bearer Access Tokens (JWT via HTTP `Authorization: Bearer <token>` header) + `bcrypt` password hashing
- **AI Semantic Matching:** Sentence Transformers (`all-MiniLM-L6-v2`) with weighted multi-criteria scoring and fallback
- **Knowledge Graph:** NetworkX (`networkx.Graph`)
- **Background Jobs:** Persistent, crash-resilient 48-hour request expiration worker
- **Testing:** `pytest`, `pytest-asyncio`, `httpx`, `mongomock-motor`

---

## 2. Directory Structure

```
/Users/apple/Desktop/Temp/
├── app/
│   ├── __init__.py
│   ├── main.py                     # FastAPI application, lifespan, CORS, error handlers
│   ├── core/
│   │   ├── config.py               # Pydantic Settings from .env
│   │   ├── security.py             # Bcrypt hashing & JWT token management
│   │   ├── database.py             # Motor MongoDB client & index initialization
│   │   └── exceptions.py           # Standard error response formatting & exception handlers
│   ├── schemas/                    # Pydantic V2 request & response models
│   │   ├── common.py               # StandardErrorResponse, UserRole enum
│   │   ├── auth.py                 # Register, Login, Token, UserResponse
│   │   ├── profile.py              # ProfileMe, Student, Alumni, Verification schemas
│   │   ├── mentor.py               # MatchReason, RecommendationsResponse
│   │   ├── mentorship.py           # Request lifecycle schemas
│   │   ├── meeting.py              # Meeting proposal & mutual confirmation schemas
│   │   ├── telegram.py             # Linking token & webhook schemas
│   │   ├── research.py             # Faculty recommendations & research projects
│   │   ├── opportunity.py          # Job, internship, collaboration, cofounder schemas
│   │   ├── graph.py                # GraphNode, GraphEdge, GraphResponse
│   │   └── community.py            # Communities & notifications schemas
│   ├── repositories/               # MongoDB persistence layer (atomic single-document operations)
│   │   ├── base.py                 # MongoDB doc-to-dict serializer
│   │   ├── user_repository.py
│   │   ├── profile_repository.py
│   │   ├── mentorship_repository.py
│   │   ├── meeting_repository.py
│   │   ├── telegram_repository.py
│   │   ├── opportunity_repository.py
│   │   ├── research_repository.py
│   │   └── community_repository.py
│   ├── services/                   # Business logic layer
│   │   ├── auth_service.py
│   │   ├── profile_service.py
│   │   ├── matching_service.py     # Sentence Transformers & weighted scoring
│   │   ├── mentorship_service.py   # Request lifecycle, 48h deadline, next-mentor fallback
│   │   ├── meeting_service.py      # Proposal negotiation & mutual confirmation
│   │   ├── telegram_service.py     # Account linking & webhook dispatch
│   │   ├── graph_service.py        # NetworkX knowledge graph generator
│   │   ├── opportunity_service.py  # Role-gated opportunity creation
│   │   ├── research_service.py     # Faculty research matching
│   │   └── notification_service.py
│   ├── jobs/
│   │   └── expiration_worker.py    # Persistent, crash-resilient 48h expiration worker
│   └── api/
│       ├── deps.py                 # Authentication & RoleChecker dependencies
│       └── v1/
│           ├── api_router.py       # Aggregator router with prefix /api/v1
│           ├── auth.py
│           ├── profiles.py
│           ├── mentors.py
│           ├── mentorship.py
│           ├── meetings.py
│           ├── telegram.py
│           ├── faculty_research.py
│           ├── opportunities.py
│           ├── graph.py
│           └── communities_notifications.py
├── tests/                          # Asynchronous automated pytest suite
│   ├── conftest.py                 # In-memory mongomock fixtures & test client
│   ├── test_auth.py
│   ├── test_profiles.py
│   ├── test_mentors.py
│   ├── test_mentorship.py
│   ├── test_meetings.py
│   ├── test_telegram.py
│   ├── test_graph.py
│   ├── test_opportunities.py
│   └── test_faculty_research.py
├── connected-openapi-v1-draft.yaml  # OpenAPI 3.1.0 complete YAML spec matching exact routes
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 3. Mandatory Endpoint Inventory

All endpoints use the prefix `/api/v1`.

### A. Authentication
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `POST` | `/api/v1/auth/register` | Register a user (student, alumni, faculty, recruiter, founder, admin) | Public |
| `POST` | `/api/v1/auth/login` | Authenticate user & issue Bearer JWT token | Public |
| `POST` | `/api/v1/auth/logout` | Invalidate current session token | Authenticated |
| `GET` | `/api/v1/auth/me` | Retrieve authenticated user identity | Authenticated |

### B. User Profiles
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `GET` | `/api/v1/profiles/me` | Retrieve current user's profile | Authenticated |
| `PATCH` | `/api/v1/profiles/me` | Partial update of user's profile | Authenticated |
| `GET` | `/api/v1/students/{user_id}` | Retrieve a visible student profile | Authenticated |
| `GET` | `/api/v1/alumni/{user_id}` | Retrieve a visible alumni profile | Authenticated |
| `GET` | `/api/v1/alumni/{user_id}/verification` | Retrieve alumni verification status and freshness | Authenticated |

### C. AI Mentor Recommendations
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `GET` | `/api/v1/mentors/recommendations` | Retrieve ranked mentor recommendations | Authenticated |
*Query parameters:* `limit`, `offset`, `skill`, `career_goal`.

### D. Mentorship Requests
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `POST` | `/api/v1/mentorship-requests` | Explicitly create request (sets 48h deadline) | Authenticated Student |
| `GET` | `/api/v1/mentorship-requests` | List requests visible to current user | Authenticated Participant |
| `GET` | `/api/v1/mentorship-requests/{request_id}` | Retrieve a specific request | Authenticated Participant |
| `POST` | `/api/v1/mentorship-requests/{request_id}/cancel` | Cancel an eligible pending request | Authenticated Requester |

### E. Meeting Coordination
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `GET` | `/api/v1/mentorship-requests/{request_id}/meeting-proposals` | List proposals for an accepted mentorship | Authenticated Participants |
| `POST` | `/api/v1/mentorship-requests/{request_id}/meeting-proposals` | Propose meeting times | Authenticated Participants |
| `POST` | `/api/v1/meeting-proposals/{proposal_id}/respond` | Accept or decline proposal (confirms on mutual agreement) | Authenticated Participants |

### F. Telegram Integration
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `POST` | `/api/v1/telegram/link/initiate` | Generate secure, single-use linking token | Authenticated User |
| `POST` | `/api/v1/webhooks/telegram` | Ingest bot updates & mentor callbacks | Telegram Webhook Header |

### G. Faculty and Research Projects
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `GET` | `/api/v1/faculty/recommendations` | Retrieve faculty recommendations | Authenticated |
| `GET` | `/api/v1/research-projects` | Browse open faculty research projects | Authenticated |

### H. Opportunities
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `GET` | `/api/v1/opportunities` | Browse opportunities (`job`, `internship`, `collaboration`, `cofounder`) | Authenticated |
| `POST` | `/api/v1/opportunities` | Create opportunity | Recruiter, Founder, Faculty, Alumni, Admin |

### I. Knowledge Graph
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `GET` | `/api/v1/graph/me` | Retrieve user's personal knowledge graph | Authenticated |

### J. Communities and Notifications
| Method | Endpoint | Purpose | Access |
|---|---|---|---|
| `GET` | `/api/v1/communities` | List discoverable communities | Authenticated |
| `GET` | `/api/v1/notifications` | List notifications for current user | Authenticated |

---

## 4. Standard Error Contract

All application errors return:
```json
{
  "error": {
    "code": "MENTOR_NOT_AVAILABLE",
    "message": "This mentor is no longer accepting requests.",
    "details": {}
  }
}
```

---

## 5. Setup & Running Locally

### Prerequisites
- Python 3.12+
- MongoDB 6.0+ running locally or in Docker

### Step-by-Step Setup
1. Create and activate a Python virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create your `.env` configuration:
   ```bash
   cp .env.example .env
   # Edit .env and fill in MONGODB_URI, JWT_SECRET_KEY etc.
   ```
4. Start the development server:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```
5. View API Documentation:
   - **Swagger UI:** `http://127.0.0.1:8000/docs`
   - **ReDoc:** `http://127.0.0.1:8000/redoc`
   - **OpenAPI JSON:** `http://127.0.0.1:8000/openapi.json`
   - **Contract Specification:** `connected-openapi-v1-draft.yaml`

---

## 6. Seed Demo Data

Populate the database with realistic students, alumni mentors, faculty, recruiters, research projects, opportunities, and communities for instant demo testing:

```bash
python scripts/seed_data.py
```

**Demo credentials** (all use password `Demo1234!`):

| Role | Email |
|---|---|
| Student | `aisha.student@university.edu` |
| Student | `raj.student@university.edu` |
| Alumni Mentor | `alex.mentor@example.com` |
| Alumni Mentor | `priya.mentor@example.com` |
| Alumni Mentor | `marcus.mentor@example.com` |
| Faculty | `dr.chen@university.edu` |
| Recruiter | `recruiter@techcorp.com` |

---

## 7. Running Automated Tests

Run the full pytest suite:
```bash
pytest -v
```

The test suite runs with an isolated in-memory MongoDB mock (`mongomock-motor`), enabling fast, deterministic execution without requiring a live MongoDB daemon. **47 tests, 0 failures.**

---

## 8. AI Mentor Matching

The `GET /api/v1/mentors/recommendations` endpoint uses a **weighted multi-criteria scoring algorithm**:

| Signal | Weight |
|---|---|
| Skill overlap (student ∩ alumni skills) | 45% |
| Semantic similarity (career goals + bio) | 35% |
| Profile freshness score | 20% |

**Two operating modes:**

- **Full AI mode** (optional): Install `sentence-transformers` for real semantic embeddings:
  ```bash
  pip install sentence-transformers  # Requires PyTorch (~2GB)
  ```
  The model `all-MiniLM-L6-v2` loads automatically on startup.

- **Fallback mode** (default): When `sentence-transformers` is not installed, a deterministic 64-dimensional token-frequency hash embedding is used. Recommendations still work correctly; they are less semantically nuanced but significantly faster and lighter.

---

## 9. Security Notes

### JWT Token Revocation
Logged-out tokens are stored in an **in-process Python set** (`_REVOKED_TOKENS`). This means:
- Token revocation is **lost on server restart** — a revoked token becomes valid again until its `exp` claim expires.
- For production, replace with a MongoDB-backed token blocklist with a TTL index.
- For the hackathon/MVP, this is acceptable because JWT `exp` ensures tokens expire naturally within `ACCESS_TOKEN_EXPIRE_MINUTES`.

### Rate Limiting
No application-level rate limiting is implemented. For production deployment, configure rate limits at the reverse proxy layer (nginx `limit_req_zone`, Cloudflare, or an API gateway) targeting `POST /api/v1/auth/login` and `POST /api/v1/auth/register`.

### Duplicate Mentorship Requests
The backend prevents a student from opening a second `pending` request to the same mentor. Attempting to do so returns `HTTP 409 DUPLICATE_REQUEST`.

---

## 10. Mentorship Lifecycle — Complete API Reference

```
POST   /api/v1/mentorship-requests              Create request (student)
GET    /api/v1/mentorship-requests              List requests visible to caller
GET    /api/v1/mentorship-requests/{id}         Get a specific request
POST   /api/v1/mentorship-requests/{id}/cancel  Cancel pending request (student only)
POST   /api/v1/mentorship-requests/{id}/respond Accept or decline (mentor only)
```

**Mentor respond body:**
```json
{ "accept": true }
```

State machine: `pending → accepted | declined | cancelled | expired`
