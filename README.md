<<<<<<< HEAD
# connectED - AI-Powered Alumni Knowledge Graph

## 1. Project Overview

connectED is an AI-powered professional networking platform
that connects students with alumni, faculty, recruiters,
and professionals for mentorship, career guidance, and collaboration.

This module uses a Knowledge Graph to represent people,
skills, companies, and their relationships.

## 2. Problem Statement

Students often struggle to find relevant alumni who can
guide them toward their career goals.

A Knowledge Graph helps organize professional information
and discover useful connections between students and alumni.

## 3. Technologies Used

- Python
- NetworkX
- JSON
- Python unittest

## 4. Main Features

- Build a graph of students, alumni, skills, and companies.
- Find alumni with a particular skill.
- Display alumni professional details.
- Identify a student's existing skills.
- Export the Knowledge Graph to JSON.
- Test core functions automatically.

## 5. Project Structure

connectED/
- knowledge_graph.py
- sample_data.py
- test_knowledge_graph.py
- README.md
- knowledge_graph.json (generated when the program runs)

## 6. Installation

Install Python and then install NetworkX:

    python -m pip install networkx

## 7. Run the Project

Run the Knowledge Graph:

    python knowledge_graph.py

Run the tests:

    python -m unittest test_knowledge_graph.py -v

## 8. Sample Demonstration

The sample dataset includes:

- Student: Aarav
- Alumni: Riya and Kabir
- Skills: Python, Machine Learning, and SQL
- Companies: Google and Microsoft

The system can find alumni who have Python or
Machine Learning skills.

## 9. Future Improvements

- Add more students and alumni.
- Include mentorship and career-goal relationships.
- Connect the graph to a real database.
- Integrate the graph with a recommendation system.
- Build an API for the frontend.

## 10. Data Disclaimer

The included people and professional details are fictional
demonstration data. They do not represent verified real-world records
=======
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
>>>>>>> 9d4587353e4cb60b99d408d1f8ac196da787a96b
