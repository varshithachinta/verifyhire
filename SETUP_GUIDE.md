# VerifyHire — Complete Setup & Run Guide

## 🗂️ Final File Structure

```
verifyhire/
└── backend/
    ├── .env
    ├── requirements.txt
    ├── test_auth.py
    └── app/
        ├── __init__.py
        ├── main.py                      ← FastAPI app entry point
        ├── core/
        │   ├── config.py                ← Settings (pydantic-settings)
        │   ├── database.py              ← Async SQLAlchemy engine + session
        │   ├── security.py              ← JWT + bcrypt utilities
        │   └── deps.py                  ← Auth dependencies (require_worker etc.)
        ├── models/
        │   └── models.py                ← All SQLAlchemy models (6 tables)
        ├── schemas/
        │   └── schemas.py               ← All Pydantic request/response schemas
        ├── routes/
        │   ├── auth.py                  ← POST /auth/register, /login, /refresh, GET /me
        │   ├── worker.py                ← GET/PATCH /worker/profile, skills CRUD
        │   ├── employer.py              ← GET/PATCH /employer/profile, jobs CRUD
        │   ├── videos.py                ← POST /worker/videos/upload (triggers pipeline)
        │   └── matches.py               ← GET /worker/matches
        └── services/
            ├── ai_pipeline.py           ← Full AI pipeline (ffmpeg+YOLO+DeepFace+Whisper+spaCy)
            └── matching.py              ← SBERT + FAISS job matching engine
```

---

## ⚙️ STEP 1: Prerequisites

Install system dependencies (once, outside venv):

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y ffmpeg postgresql postgresql-contrib python3.12 python3.12-venv

# macOS (Homebrew)
brew install ffmpeg postgresql@16 python@3.12

# Windows
# 1. Install ffmpeg from https://ffmpeg.org/download.html → add to PATH
# 2. Install PostgreSQL from https://www.postgresql.org/download/windows/
# 3. Python 3.12 from https://python.org
```

Verify ffmpeg:
```bash
ffmpeg -version       # Expected: ffmpeg version 6.x or higher
ffprobe -version
```

---

## 🐘 STEP 2: PostgreSQL Setup

```bash
# Start PostgreSQL
sudo systemctl start postgresql   # Linux
brew services start postgresql@16 # macOS

# Create database and user
sudo -u postgres psql << 'SQL'
CREATE USER verifyhire_user WITH PASSWORD 'verifyhire_pass';
CREATE DATABASE verifyhire_db OWNER verifyhire_user;
GRANT ALL PRIVILEGES ON DATABASE verifyhire_db TO verifyhire_user;
SQL

# Verify connection
psql -U verifyhire_user -h localhost -d verifyhire_db -c "SELECT version();"
```

---

## 🐍 STEP 3: Python Virtual Environment

```bash
cd verifyhire/backend

# Create venv
python3.12 -m venv venv

# Activate
source venv/bin/activate         # Linux/macOS
# OR
venv\Scripts\activate            # Windows PowerShell

# Upgrade pip
pip install --upgrade pip

# Install all dependencies (~10 minutes for AI models)
pip install -r requirements.txt
```

### Install spaCy language model:
```bash
python -m spacy download en_core_web_sm
```

### Expected output after install:
```
Successfully installed fastapi-0.115.5 uvicorn-0.32.1 sqlalchemy-2.0.36
  ultralytics-8.3.50 openai-whisper-20240930 spacy-3.8.3
  sentence-transformers-3.3.1 faiss-cpu-1.9.0 deepface-0.0.93 ...
```

---

## 🚀 STEP 4: Run the Backend

```bash
cd verifyhire/backend
source venv/bin/activate

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Expected startup output:
```
INFO | Starting VerifyHire...
INFO | Directory ready: uploads/videos
INFO | Directory ready: uploads/audio
INFO | Directory ready: uploads/faces
INFO | Database tables created/verified
INFO | Application startup complete.
INFO | Uvicorn running on http://0.0.0.0:8000
```

**Open Swagger UI:** http://localhost:8000/docs

---

## 🧪 STEP 5: Test the Full Flow

### Option A — Automated Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx aiosqlite

# Run all tests
pytest test_auth.py -v

# Expected: 10 tests passing
```

### Option B — Manual curl tests

**1. Register worker:**
```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"ravi@test.com","password":"testpass123","role":"worker"}' | jq .
```

**2. Login and save token:**
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ravi@test.com","password":"testpass123"}' | jq -r .access_token)
echo "Token: $TOKEN"
```

**3. Update worker profile:**
```bash
curl -s -X PATCH http://localhost:8000/worker/profile \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Ravi Kumar","bio":"Experienced electrician with 5 years wiring experience","location":"Hyderabad"}' | jq .
```

**4. Add skills:**
```bash
curl -s -X POST http://localhost:8000/worker/skills \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"skill_name":"electrician","years_experience":5}' | jq .
```

**5. Register employer and create job:**
```bash
EMP_TOKEN=$(curl -s -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"employer@buildco.com","password":"testpass123","role":"employer"}' | jq -r .access_token)

curl -s -X POST http://localhost:8000/employer/jobs \
  -H "Authorization: Bearer $EMP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Senior Electrician",
    "description":"Looking for experienced electrician for wiring and installation projects",
    "required_skills":["electrician","wiring","electrical","installation"],
    "location":"Hyderabad",
    "employment_type":"full_time",
    "salary_min":25000,
    "salary_max":40000
  }' | jq .
```

**6. Upload video:**
```bash
# Create a test video first (requires ffmpeg)
ffmpeg -f lavfi -i color=c=blue:s=640x480:d=5 \
       -f lavfi -i sine=frequency=440:duration=5 \
       -c:v libx264 -c:a aac test_video.mp4

# Upload it
curl -s -X POST http://localhost:8000/worker/videos/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test_video.mp4" | jq .
```

**7. Get AI matches:**
```bash
curl -s http://localhost:8000/worker/matches \
  -H "Authorization: Bearer $TOKEN" | jq .
```

### Expected matches response:
```json
{
  "worker_id": "...",
  "total_jobs_evaluated": 1,
  "matches": [
    {
      "job": {"title": "Senior Electrician", ...},
      "final_score": 0.73,
      "semantic_score": 0.81,
      "skill_score": 0.50,
      "matched_skills": ["electrician"]
    }
  ]
}
```

---

## 🤖 STEP 6: AI Models (Auto-Downloaded)

These download automatically on first use:

| Model | Size | When |
|-------|------|------|
| YOLOv8n-face | ~6MB | First video upload |
| Whisper base | ~140MB | First video upload |
| SBERT all-MiniLM-L6-v2 | ~80MB | First /matches call |
| DeepFace ArcFace | ~250MB | First face verify |
| spaCy en_core_web_sm | ~12MB | `python -m spacy download en_core_web_sm` |

---

## ⚠️ Common Errors & Fixes

### Error: `ffmpeg not found`
```bash
# Linux
sudo apt install ffmpeg

# Windows: Download from ffmpeg.org, add bin/ folder to System PATH
# Then restart terminal
```

### Error: `could not connect to server` (PostgreSQL)
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Error: `bcrypt has no attribute '__about__'`
```bash
pip install bcrypt==4.0.1 passlib==1.7.4
```

### Error: `No module named 'en_core_web_sm'`
```bash
python -m spacy download en_core_web_sm
```

### Error: YOLOv8 model not found
```bash
# Download manually
python -c "from ultralytics import YOLO; YOLO('yolov8n-face.pt')"
```

### Error: JWT 'str' not UUID
Already handled in `deps.py` with explicit `uuid.UUID(user_id_str)` conversion.

---

## 🌐 API Summary

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | /health | ❌ | Health check |
| POST | /auth/register | ❌ | Register user |
| POST | /auth/login | ❌ | Login → tokens |
| POST | /auth/refresh | ❌ | Refresh access token |
| GET | /auth/me | ✅ | Current user |
| GET | /worker/profile | ✅ Worker | Get profile |
| PATCH | /worker/profile | ✅ Worker | Update profile |
| GET | /worker/skills | ✅ Worker | List skills |
| POST | /worker/skills | ✅ Worker | Add skill |
| DELETE | /worker/skills/{id} | ✅ Worker | Delete skill |
| GET | /worker/videos | ✅ Worker | List videos |
| POST | /worker/videos/upload | ✅ Worker | Upload + AI pipeline |
| GET | /worker/matches | ✅ Worker | Ranked job matches |
| GET | /employer/profile | ✅ Employer | Get profile |
| PATCH | /employer/profile | ✅ Employer | Update profile |
| POST | /employer/jobs | ✅ Employer | Create job |
| GET | /employer/jobs | ✅ Employer | List my jobs |
| DELETE | /employer/jobs/{id} | ✅ Employer | Delete job |
| GET | /employer/public/jobs | ❌ | All active jobs |

---

## 🏗️ Frontend (Next.js) — After Backend Complete

```bash
cd verifyhire
npx create-next-app@latest frontend --typescript --tailwind --app
cd frontend
npm run dev
# → http://localhost:3000
```

See documentation section 5.2 for completed frontend pages list.
