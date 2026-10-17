#!/usr/bin/env python3
"""
connectED Seed Data Script — for DEVELOPMENT and DEMO ENVIRONMENTS ONLY.

DO NOT run this against a production database.
All seeded accounts use demo credentials (Demo1234!) and are NOT real identities.
Alumni marked verification_status='verified' are fictional demonstration profiles.

Usage:
    python scripts/seed_data.py            # safe on local/dev DB
    python scripts/seed_data.py --confirm-demo  # required if MONGODB_URI contains 'mongodb+srv'

This script is idempotent:
    - Users: skipped if email already exists.
    - Research projects: skipped if (faculty_id, title) already exists.
    - Opportunities: skipped if (organization, title) already exists.
    - Communities: skipped if name already exists.
"""
import asyncio, os, sys
from datetime import datetime, timezone
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
load_dotenv()
from app.core.database import connect_to_mongo, get_database
from app.core.security import hash_password

USERS = [
    {"email": "aisha.student@university.edu", "name": "Aisha Khan", "password": "Demo1234!", "role": "student",
     "skills": ["Python","FastAPI","MongoDB","Machine Learning"], "career_goals": ["AI/ML Engineer"],
     "institution": "connectED University", "department": "Computer Science", "degree": "B.Sc.",
     "headline": "CS junior passionate about AI", "bio": "Looking for mentorship in AI.",
     "research_interests": ["Machine Learning","NLP"], "graduation_year": 2026,
     "mentorship_preferences": {"accepting_requests": False}},
    {"email": "raj.student@university.edu", "name": "Raj Sharma", "password": "Demo1234!", "role": "student",
     "skills": ["Product Management","React","Node.js"], "career_goals": ["Product Manager"],
     "institution": "connectED University", "department": "Business", "degree": "B.Tech.",
     "headline": "Final-year student exploring startups", "bio": "Aspiring PM in fintech.",
     "research_interests": ["HCI"], "graduation_year": 2025,
     "mentorship_preferences": {"accepting_requests": False}},
    {"email": "alex.mentor@example.com", "name": "Alex Johnson", "password": "Demo1234!", "role": "alumni",
     "skills": ["Python","Go","Kubernetes","Distributed Systems","FastAPI","MongoDB"],
     "current_role": "Senior Software Engineer", "current_organization": "Google",
     "institution": "connectED University", "degree": "M.Sc.", "graduation_year": 2018,
     "headline": "SWE @ Google | Distributed Systems", "bio": "Love mentoring engineers.",
     "mentorship_preferences": {"accepting_requests": True, "max_mentees": 3},
     "verification_status": "verified", "profile_freshness": "current", "freshness_score": 0.95},
    {"email": "priya.mentor@example.com", "name": "Priya Nair", "password": "Demo1234!", "role": "alumni",
     "skills": ["Python","Machine Learning","Natural Language Processing","PyTorch"],
     "current_role": "ML Research Scientist", "current_organization": "DeepMind",
     "institution": "connectED University", "degree": "Ph.D.", "graduation_year": 2019,
     "headline": "ML Scientist @ DeepMind | NLP", "bio": "Happy to guide students into AI research.",
     "mentorship_preferences": {"accepting_requests": True, "max_mentees": 2},
     "verification_status": "verified", "profile_freshness": "current", "freshness_score": 0.92},
    {"email": "marcus.mentor@example.com", "name": "Marcus Williams", "password": "Demo1234!", "role": "alumni",
     "skills": ["Product Management","Fundraising","Leadership","React"],
     "current_role": "Founder & CEO", "current_organization": "Stealth Startup",
     "institution": "connectED University", "degree": "M.B.A.", "graduation_year": 2015,
     "headline": "Startup Founder | 2x Exits", "bio": "Mentoring next-gen founders.",
     "mentorship_preferences": {"accepting_requests": True, "max_mentees": 5},
     "verification_status": "verified", "profile_freshness": "current", "freshness_score": 0.88},
    {"email": "dr.chen@university.edu", "name": "Dr. Wei Chen", "password": "Demo1234!", "role": "faculty",
     "skills": ["Machine Learning","Robotics","Computer Vision","Python"],
     "institution": "connectED University", "department": "Computer Science", "degree": "Ph.D.",
     "headline": "Professor | AI & Robotics Lab", "bio": "Leading researcher in AI robotics.",
     "research_interests": ["Machine Learning","Robotics","Computer Vision","Reinforcement Learning"],
     "mentorship_preferences": {"accepting_requests": True}},
    {"email": "recruiter@techcorp.com", "name": "Sarah Mitchell", "password": "Demo1234!", "role": "recruiter",
     "skills": ["Recruiting","Technical Hiring"], "institution": "TechCorp Inc.",
     "headline": "Senior Technical Recruiter @ TechCorp", "bio": "Connecting engineers with opportunities.",
     "mentorship_preferences": {"accepting_requests": False}},
]

async def seed():
    # Fail-closed Atlas guard: require explicit confirmation if URI looks like a cloud cluster
    mongo_uri = os.environ.get("MONGODB_URI", "")
    is_atlas = "mongodb+srv" in mongo_uri or "mongodb.net" in mongo_uri
    confirmed = "--confirm-demo" in sys.argv
    if is_atlas and not confirmed:
        print(
            "ERROR: MONGODB_URI appears to point to a remote/Atlas cluster.\n"
            "       Re-run with --confirm-demo to proceed on this database."
        )
        sys.exit(1)

    await connect_to_mongo()
    db = get_database()
    print("Starting seed (demo data only, idempotent) ...")
    faculty_id = None
    recruiter_id = None
    for u in USERS:
        existing = await db.users.find_one({"email": u["email"]})
        if existing:
            print(f"  Skipping {u['email']} - exists")
            if u["role"] == "faculty": faculty_id = str(existing["_id"])
            if u["role"] == "recruiter": recruiter_id = str(existing["_id"])
            continue
        now = datetime.now(timezone.utc)
        res = await db.users.insert_one({
            "email": u["email"], "name": u["name"],
            "hashed_password": hash_password(u["password"]),
            "role": u["role"], "is_active": True,
            "created_at": now, "updated_at": now,
        })
        uid = str(res.inserted_id)
        if u["role"] == "faculty": faculty_id = uid
        if u["role"] == "recruiter": recruiter_id = uid
        await db.profiles.insert_one({
            "user_id": uid, "role": u["role"], "name": u["name"],
            "headline": u.get("headline",""), "bio": u.get("bio",""),
            "institution": u.get("institution",""), "department": u.get("department"),
            "degree": u.get("degree"), "graduation_year": u.get("graduation_year"),
            "current_role": u.get("current_role"), "current_organization": u.get("current_organization"),
            "skills": u.get("skills",[]), "career_goals": u.get("career_goals",[]),
            "research_interests": u.get("research_interests",[]),
            "mentorship_preferences": u.get("mentorship_preferences",{}),
            "verification_status": u.get("verification_status","unverified"),
            "profile_freshness": u.get("profile_freshness","current"),
            "freshness_score": u.get("freshness_score", 0.9),
            "created_at": now, "updated_at": now,
        })
        print(f"  Created {u['role']}: {u['name']}")
    if faculty_id:
        for proj in [
            {"title": "Federated Learning for Healthcare AI", "research_area": "Machine Learning",
             "description": "Federated ML on medical data without centralising patient info.",
             "required_skills": ["Python","Machine Learning","PyTorch"], "availability": "open",
             "application_instructions": "Submit CV and research statement."},
            {"title": "Knowledge Graph from Academic Literature", "research_area": "Natural Language Processing",
             "description": "NLP pipelines to build research knowledge graphs.",
             "required_skills": ["Python","NLP","NetworkX"], "availability": "open",
             "application_instructions": "Email your GitHub profile."},
        ]:
            now = datetime.now(timezone.utc)
            existing_proj = await db.research_projects.find_one(
                {"faculty_id": faculty_id, "title": proj["title"]}
            )
            if existing_proj:
                print(f"  Skipping research project '{proj['title']}' - exists")
                continue
            await db.research_projects.insert_one(
                {"faculty_id": faculty_id, "faculty_name": "Dr. Wei Chen",
                 "created_at": now, "updated_at": now, **proj}
            )
            print(f"  Research project: {proj['title']}")
    if recruiter_id:
        for opp in [
            {"type": "internship", "title": "Backend Engineering Intern - Summer 2025",
             "description": "12-week internship on Platform Engineering.", "organization": "TechCorp Inc.",
             "location": "San Francisco (Hybrid)", "required_skills": ["Python","Kubernetes"],
             "application_url": "https://techcorp.com/careers", "contact_email": "recruiter@techcorp.com", "is_active": True},
            {"type": "job", "title": "Junior ML Engineer - Full-Time",
             "description": "Join TechCorp AI recommendation systems.", "organization": "TechCorp Inc.",
             "location": "Remote", "required_skills": ["Python","Machine Learning","PyTorch"],
             "application_url": "https://techcorp.com/careers", "contact_email": "recruiter@techcorp.com", "is_active": True},
        ]:
            now = datetime.now(timezone.utc)
            existing_opp = await db.opportunities.find_one(
                {"organization": opp["organization"], "title": opp["title"]}
            )
            if existing_opp:
                print(f"  Skipping opportunity '{opp['title']}' - exists")
                continue
            await db.opportunities.insert_one(
                {"creator_id": recruiter_id, "creator_role": "recruiter", "created_at": now, **opp}
            )
            print(f"  Opportunity: {opp['title']}")
    for comm in [
        {"name": "AI & Machine Learning Circle", "description": "AI, ML, data science community.",
         "category": "Research & Technology", "member_count": 47, "is_private": False},
        {"name": "Startup Founders Network", "description": "Connect with founders on campus.",
         "category": "Entrepreneurship", "member_count": 23, "is_private": False},
    ]:
        now = datetime.now(timezone.utc)
        existing_comm = await db.communities.find_one({"name": comm["name"]})
        if existing_comm:
            print(f"  Skipping community '{comm['name']}' - exists")
            continue
        await db.communities.insert_one({"created_at": now, "updated_at": now, **comm})
        print(f"  Community: {comm['name']}")
    print("Seed complete! All demo passwords: Demo1234! — DEVELOPMENT USE ONLY.")

if __name__ == "__main__":
    asyncio.run(seed())
