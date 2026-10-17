# connectED — Frontend Integration Guide & API Reference

This document provides everything the frontend team needs to build, connect, and test the entire connectED web application without needing any additional clarifications.

---

## 1. Quick Facts & Environment

| Property | Value |
| :--- | :--- |
| **API Base URL (Local)** | `http://localhost:8000` |
| **API Prefix** | `/api/v1` |
| **Interactive Swagger Docs** | `http://localhost:8000/docs` |
| **Contract Spec Files** | `backend/openapi.json` |
| **Supported Frontend Ports (CORS)** | `http://localhost:5173` (Vite), `http://localhost:3000` (Next/React) |
| **Authentication Type** | Bearer Token: `Authorization: Bearer <access_token>` |
| **Total Endpoints** | 23 |

---

## 2. How to Run the Backend Locally (Windows / macOS / Linux)

If you want to run the FastAPI backend on your local machine (`C:\Users\Dell` or Mac):

```bash
# 1. Ensure you have Python 3.11+ installed
python --version

# 2. From the repository root, create and activate a virtual environment
# Windows (PowerShell/CMD):
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the environment file
# Windows:
copy .env.example .env
# macOS/Linux:
cp .env.example .env

# 5. Start the FastAPI development server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Once started, visit:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **OpenAPI Schema**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## 3. Authentication & Headers

Protected endpoints require the standard `Authorization` header:
```http
Authorization: Bearer <jwt_access_token>
Content-Type: application/json
```
Tokens expire after 24 hours (`1440 minutes`).

---

## 4. Complete Endpoints & Data Contracts

### 4.1 Authentication (`/api/v1/auth`)

#### `POST /api/v1/auth/register` (Public)
Register a new user.
- **Request Body**:
```json
{
  "email": "student@university.edu",
  "password": "SecurePassword123!",
  "role": "student", // Options: "student", "alumni", "faculty", "recruiter", "founder", "admin"
  "name": "Alex Johnson",
  "headline": "CS Undergraduate & AI Enthusiast",
  "institution": "Stanford University",
  "department": "Computer Science",
  "degree": "B.S.",
  "graduation_year": 2026,
  "skills": ["Python", "FastAPI", "React", "Machine Learning"]
}
```
- **Response `201 Created`**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1Ni...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "67123abc456def7890123456",
    "email": "student@university.edu",
    "role": "student",
    "name": "Alex Johnson",
    "is_active": true,
    "telegram_linked": false,
    "created_at": "2026-10-18T00:00:00Z"
  }
}
```

#### `POST /api/v1/auth/login` (Public)
Authenticate with credentials.
- **Request Body**:
```json
{
  "email": "student@university.edu",
  "password": "SecurePassword123!"
}
```
- **Response `200 OK`**: Same as `TokenResponse` above.

#### `GET /api/v1/auth/me` (Protected)
Fetch the current authenticated user's session.
- **Response `200 OK`**:
```json
{
  "id": "67123abc456def7890123456",
  "email": "student@university.edu",
  "role": "student",
  "name": "Alex Johnson",
  "is_active": true,
  "telegram_linked": false,
  "created_at": "2026-10-18T00:00:00Z"
}
```

#### `POST /api/v1/auth/logout` (Protected)
- **Response `200 OK`**:
```json
{
  "success": true,
  "message": "Successfully logged out"
}
```

---

### 4.2 Profiles (`/api/v1/profiles`, `/students`, `/alumni`)

#### `GET /api/v1/profiles/me` (Protected)
- **Response `200 OK`**:
```json
{
  "user_id": "67123abc456def7890123456",
  "role": "student",
  "name": "Alex Johnson",
  "headline": "CS Undergraduate & AI Enthusiast",
  "institution": "Stanford University",
  "department": "Computer Science",
  "degree": "B.S.",
  "graduation_year": 2026,
  "current_organization": null,
  "current_role": null,
  "skills": ["Python", "FastAPI", "React"],
  "interests": ["Distributed Systems", "AI Agents"],
  "bio": "Passionate about full-stack systems.",
  "profile_visibility": "public"
}
```

#### `PATCH /api/v1/profiles/me` (Protected)
Update profile fields.
- **Request Body** (all fields optional):
```json
{
  "headline": "Incoming Software Engineering Intern",
  "skills": ["Python", "FastAPI", "React", "TypeScript", "TailwindCSS"],
  "bio": "Updated bio..."
}
```
- **Response `200 OK`**: Updated `ProfileMeResponse`.

#### `GET /api/v1/students/{user_id}` (Protected)
- **Response `200 OK`**: Student profile summary with skills, courses, interests.

#### `GET /api/v1/alumni/{user_id}` (Protected)
- **Response `200 OK`**: Alumni profile including `current_organization`, `current_role`, `industry`, `mentorship_preferences`.

#### `GET /api/v1/alumni/{user_id}/verification` (Protected)
- **Response `200 OK`**:
```json
{
  "user_id": "alumni_id_123",
  "name": "Dr. Sarah Chen",
  "verification_status": "verified", // "verified", "pending", "unverified", "rejected"
  "verified_at": "2026-01-15T12:00:00Z",
  "evidence_source": "institutional_email",
  "freshness_score": 0.95,
  "profile_freshness": "fresh", // "fresh", "stale", "unknown"
  "last_verified_by": "system"
}
```

---

### 4.3 AI Mentor Recommendations & Mentorship Requests

#### `GET /api/v1/mentors/recommendations` (Protected - Student)
AI-scored alumni/peer mentor recommendations tailored to student skills and interests.
- **Query Params**: `limit` (default: 10), `offset` (default: 0)
- **Response `200 OK`**:
```json
{
  "items": [
    {
      "mentor_id": "67123abc456def7890123999",
      "name": "Elena Rostova",
      "current_role": "Staff Software Engineer @ Google",
      "skills": ["Distributed Systems", "Python", "System Design"],
      "match_score": 0.94,
      "reasons": [
        { "code": "SKILL_OVERLAP", "label": "Shares 4 skills with your profile" },
        { "code": "ALUMNI_CONNECTION", "label": "Graduated from Stanford CS" }
      ],
      "profile_freshness": "fresh",
      "can_request": true
    }
  ],
  "algorithm_version": "v1.2-neural-ranker",
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

#### `POST /api/v1/mentorship-requests` (Protected - Student)
Send a mentorship connection request.
- **Request Body**:
```json
{
  "mentor_id": "67123abc456def7890123999",
  "message": "Hi Elena! I would love your advice on preparing for staff-level distributed systems interviews."
}
```
- **Response `201 Created`**:
```json
{
  "id": "req_67123def...",
  "student_id": "67123abc456def7890123456",
  "mentor_id": "67123abc456def7890123999",
  "message": "Hi Elena! I would love your advice...",
  "status": "pending", // "pending", "accepted", "declined", "cancelled", "expired"
  "created_at": "2026-10-18T02:00:00Z",
  "updated_at": "2026-10-18T02:00:00Z",
  "deadline": "2026-10-20T02:00:00Z"
}
```

#### `GET /api/v1/mentorship-requests` (Protected)
List incoming or outgoing mentorship requests.
- **Query Params**: `status` (optional filter), `limit`, `offset`
- **Response `200 OK`**: List of requests with pagination metadata.

#### `GET /api/v1/mentorship-requests/{request_id}` (Protected)
- **Response `200 OK`**: Specific request details.

#### `POST /api/v1/mentorship-requests/{request_id}/cancel` (Protected)
- **Response `200 OK`**:
```json
{
  "id": "req_67123def...",
  "status": "cancelled",
  "message": "Mentorship request cancelled successfully",
  "updated_at": "2026-10-18T02:30:00Z"
}
```

---

### 4.4 Meeting Coordination (`/api/v1/meeting-proposals`)

#### `GET /api/v1/mentorship-requests/{request_id}/meeting-proposals` (Protected)
List proposed meeting times for an accepted mentorship request.

#### `POST /api/v1/mentorship-requests/{request_id}/meeting-proposals` (Protected)
Propose a meeting date/time.
- **Request Body**:
```json
{
  "proposed_time": "2026-10-22T15:00:00Z",
  "timezone_str": "America/Los_Angeles",
  "note": "Let's do a 30-min intro call on Google Meet."
}
```

#### `POST /api/v1/meeting-proposals/{proposal_id}/respond` (Protected)
Accept or decline a meeting proposal.
- **Request Body**:
```json
{
  "action": "accept", // "accept" or "decline"
  "note": "Looking forward to it!"
}
```

---

### 4.5 Faculty & Research Projects

#### `GET /api/v1/faculty/recommendations` (Protected)
- **Response `200 OK`**:
```json
{
  "items": [
    {
      "faculty_id": "fac_123",
      "name": "Prof. David Miller",
      "department": "Computer Science",
      "institution": "Stanford University",
      "research_areas": ["Autonomous Agents", "Reinforcement Learning"],
      "match_score": 0.89,
      "match_reason": "High relevance to your Machine Learning focus",
      "active_projects_count": 2
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

#### `GET /api/v1/research-projects` (Protected)
- **Query Params**: `department`, `research_area`, `limit`, `offset`
- **Response `200 OK`**: Open research lab listings.

---

### 4.6 Opportunities, Communities & Notifications

#### `GET /api/v1/opportunities` (Protected)
List internships, research openings, startup roles.
- **Query Params**: `type` (`"internship"`, `"full_time"`, `"research"`, `"project"`), `limit`, `offset`

#### `POST /api/v1/opportunities` (Protected)
Create an opportunity posting (for recruiters, faculty, or alumni).

#### `GET /api/v1/communities` (Protected)
List campus / professional interest communities.

#### `GET /api/v1/notifications` (Protected)
List user notifications (mentorship updates, meeting proposals, messages).
- **Query Params**: `unread_only` (`true`/`false`), `limit`, `offset`

---

### 4.7 Knowledge Graph (`/api/v1/graph/me`)

#### `GET /api/v1/graph/me` (Protected)
Generates nodes and edges connecting the user to skills, alumni, faculty, and mutual interests for interactive network visualization (e.g., using `vis.js`, `D3.js`, or `Cytoscape`).
- **Response `200 OK`**:
```json
{
  "nodes": [
    { "id": "user_me", "type": "user", "label": "Alex Johnson", "properties": {} },
    { "id": "skill_python", "type": "skill", "label": "Python", "properties": {} },
    { "id": "mentor_elena", "type": "mentor", "label": "Elena Rostova", "properties": {} }
  ],
  "edges": [
    { "source": "user_me", "target": "skill_python", "type": "HAS_SKILL", "properties": {} },
    { "source": "mentor_elena", "target": "skill_python", "type": "EXPERT_IN", "properties": {} }
  ]
}
```

---

### 4.8 Telegram Bot Integration (`/api/v1/telegram`)

#### `POST /api/v1/telegram/link/initiate` (Protected)
Generate a deep link to link the student/mentor's Telegram account to `@ZeplyAIBot` for real-time instant notifications.
- **Response `200 OK`**:
```json
{
  "linking_token": "link_abc123xyz...",
  "bot_username": "ZeplyAIBot",
  "deep_link": "https://t.me/ZeplyAIBot?start=link_abc123xyz...",
  "expires_at": "2026-10-18T03:00:00Z",
  "instructions": "Click the deep link or open @ZeplyAIBot and send /start link_abc123xyz..."
}
```

---

### 4.9 System Health Check

#### `GET /health` (Public)
- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```
