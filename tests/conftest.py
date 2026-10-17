import asyncio
import pytest
import pytest_asyncio
import httpx
from mongomock_motor import AsyncMongoMockClient

from app.core.database import db_manager, init_db_indexes, set_test_database
from app.core.security import create_access_token, hash_password
from app.main import app

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    mock_client = AsyncMongoMockClient()
    mock_db = mock_client["connected_test"]
    set_test_database(mock_db)
    await init_db_indexes(mock_db)
    yield mock_db

@pytest_asyncio.fixture
async def async_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def student_auth(setup_test_db):
    user_data = {
        "email": "student@connected.edu",
        "hashed_password": hash_password("Password123!"),
        "role": "student",
        "name": "Jane Student",
        "is_active": True,
        "created_at": None,
    }
    from app.repositories.user_repository import user_repo
    user = await user_repo.create_user(user_data)
    
    from app.repositories.profile_repository import profile_repo
    await profile_repo.create_profile({
        "user_id": user["id"],
        "role": "student",
        "name": "Jane Student",
        "headline": "CS Student @ connectED",
        "institution": "connectED University",
        "department": "Computer Science",
        "degree": "B.S.",
        "graduation_year": 2026,
        "skills": ["Python", "FastAPI", "React"],
        "career_goals": ["Backend Engineering", "AI Systems"],
        "visibility": "public",
        "verification_status": "unverified",
        "profile_freshness": "current",
    })

    token = create_access_token(subject=user["id"], role="student", email="student@connected.edu")
    return {
        "user": user,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }

@pytest_asyncio.fixture
async def alumni_auth(setup_test_db):
    user_data = {
        "email": "alumni@connected.edu",
        "hashed_password": hash_password("Password123!"),
        "role": "alumni",
        "name": "Alex Alumni",
        "is_active": True,
        "created_at": None,
    }
    from app.repositories.user_repository import user_repo
    user = await user_repo.create_user(user_data)

    from app.repositories.profile_repository import profile_repo
    await profile_repo.create_profile({
        "user_id": user["id"],
        "role": "alumni",
        "name": "Alex Alumni",
        "headline": "Senior Staff Engineer @ Google",
        "institution": "connectED University",
        "current_organization": "Google",
        "current_role": "Senior Staff Engineer",
        "degree": "M.S.",
        "graduation_year": 2018,
        "skills": ["Python", "FastAPI", "Distributed Systems", "Machine Learning"],
        "bio": "Experienced backend engineer passionate about mentoring next-generation builders.",
        "mentorship_preferences": {
            "accepting_requests": True,
            "max_mentees": 5,
            "preferred_topics": ["Backend Engineering", "System Design"],
            "preferred_communication": "Telegram",
        },
        "visibility": "public",
        "verification_status": "verified",
        "profile_freshness": "current",
    })

    token = create_access_token(subject=user["id"], role="alumni", email="alumni@connected.edu")
    return {
        "user": user,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }

@pytest_asyncio.fixture
async def recruiter_auth(setup_test_db):
    user_data = {
        "email": "recruiter@techcorp.com",
        "hashed_password": hash_password("Password123!"),
        "role": "recruiter",
        "name": "Rachel Recruiter",
        "is_active": True,
        "created_at": None,
    }
    from app.repositories.user_repository import user_repo
    user = await user_repo.create_user(user_data)
    token = create_access_token(subject=user["id"], role="recruiter", email="recruiter@techcorp.com")
    return {
        "user": user,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }
