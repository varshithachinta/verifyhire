import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, field_validator
from app.models.models import UserRole, VideoStatus, EmploymentType


# ── Auth Schemas ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.worker

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Worker Schemas ────────────────────────────────────────────────────────────

class WorkerProfileUpdate(BaseModel):
    full_name: str | None = None
    bio: str | None = None
    location: str | None = None
    phone: str | None = None
    years_experience: int | None = None


class WorkerProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    full_name: str | None
    bio: str | None
    location: str | None
    phone: str | None
    years_experience: int | None
    face_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SkillCreate(BaseModel):
    skill_name: str
    skill_category: str | None = None
    years_experience: int | None = None


class SkillResponse(BaseModel):
    id: uuid.UUID
    skill_name: str
    skill_category: str | None
    years_experience: int | None
    is_ai_extracted: bool
    confidence_score: float | None

    model_config = {"from_attributes": True}


# ── Employer Schemas ──────────────────────────────────────────────────────────

class EmployerProfileUpdate(BaseModel):
    company_name: str | None = None
    industry: str | None = None
    location: str | None = None
    description: str | None = None
    website: str | None = None


class EmployerProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    company_name: str | None
    industry: str | None
    location: str | None
    description: str | None
    website: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Job Schemas ───────────────────────────────────────────────────────────────

class JobCreate(BaseModel):
    title: str
    description: str
    required_skills: list[str] = []
    location: str | None = None
    employment_type: EmploymentType = EmploymentType.full_time
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "INR"


class JobResponse(BaseModel):
    id: uuid.UUID
    employer_id: uuid.UUID
    title: str
    description: str
    required_skills: list[str]
    location: str | None
    employment_type: EmploymentType
    salary_min: float | None
    salary_max: float | None
    salary_currency: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Video Schemas ─────────────────────────────────────────────────────────────

class VideoResponse(BaseModel):
    id: uuid.UUID
    worker_id: uuid.UUID
    file_name: str | None
    status: VideoStatus
    transcript: str | None
    detected_language: str | None
    face_detected: bool | None
    face_verified: bool | None
    face_confidence: float | None
    face_similarity_score: float | None
    audio_duration: float | None
    processing_metadata: dict | None
    created_at: datetime
    processed_at: datetime | None

    model_config = {"from_attributes": True}


# ── Matching Schemas ──────────────────────────────────────────────────────────

class JobMatchResult(BaseModel):
    job: JobResponse
    final_score: float
    semantic_score: float
    skill_score: float
    matched_skills: list[str]


class MatchResponse(BaseModel):
    worker_id: uuid.UUID
    total_jobs_evaluated: int
    matches: list[JobMatchResult]
