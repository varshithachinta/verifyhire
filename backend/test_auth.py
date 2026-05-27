"""
STEP 8: Test Flow
Run with: pytest test_auth.py -v
"""
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

# ── Setup ──────────────────────────────────────────────────────────────────
# For testing, swap to SQLite (no PostgreSQL needed)
import os
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["SYNC_DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-minimum-32-characters-long"

from app.main import app
from app.core.database import Base, engine


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as c:
        yield c


# ── Tests ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_worker(client):
    r = await client.post("/auth/register", json={
        "email": "worker@test.com",
        "password": "testpass123",
        "role": "worker"
    })
    assert r.status_code == 201
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_register_employer(client):
    r = await client.post("/auth/register", json={
        "email": "employer@test.com",
        "password": "testpass123",
        "role": "employer"
    })
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_login(client):
    r = await client.post("/auth/login", json={
        "email": "worker@test.com",
        "password": "testpass123"
    })
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_duplicate_email(client):
    r = await client.post("/auth/register", json={
        "email": "worker@test.com",
        "password": "testpass123",
        "role": "worker"
    })
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_worker_profile(client):
    # Login first
    login = await client.post("/auth/login", json={
        "email": "worker@test.com", "password": "testpass123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.get("/worker/profile", headers=headers)
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_update_worker_profile(client):
    login = await client.post("/auth/login", json={
        "email": "worker@test.com", "password": "testpass123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.patch("/worker/profile", headers=headers, json={
        "full_name": "Ravi Kumar",
        "bio": "Experienced electrician with 5 years of experience in wiring and installation",
        "location": "Hyderabad",
    })
    assert r.status_code == 200
    assert r.json()["full_name"] == "Ravi Kumar"


@pytest.mark.asyncio
async def test_add_skill(client):
    login = await client.post("/auth/login", json={
        "email": "worker@test.com", "password": "testpass123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.post("/worker/skills", headers=headers, json={
        "skill_name": "electrician",
        "years_experience": 5
    })
    assert r.status_code == 201
    assert r.json()["skill_name"] == "electrician"


@pytest.mark.asyncio
async def test_create_job(client):
    login = await client.post("/auth/login", json={
        "email": "employer@test.com", "password": "testpass123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.post("/employer/jobs", headers=headers, json={
        "title": "Electrician Needed",
        "description": "Looking for a skilled electrician for wiring and installation work",
        "required_skills": ["electrician", "wiring", "electrical"],
        "location": "Hyderabad",
        "employment_type": "full_time",
        "salary_min": 20000,
        "salary_max": 35000,
    })
    assert r.status_code == 201
    assert r.json()["title"] == "Electrician Needed"


@pytest.mark.asyncio
async def test_get_matches(client):
    login = await client.post("/auth/login", json={
        "email": "worker@test.com", "password": "testpass123"
    })
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = await client.get("/worker/matches", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert "matches" in data
    assert "total_jobs_evaluated" in data
    print(f"\n  Matches found: {len(data['matches'])}")
    if data["matches"]:
        top = data["matches"][0]
        print(f"  Top match: '{top['job']['title']}' | Score: {top['final_score']}")
