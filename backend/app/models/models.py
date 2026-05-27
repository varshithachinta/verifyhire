import uuid
from datetime import datetime
from sqlalchemy import (
    String, Boolean, Integer, Float, Text, DateTime,
    ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base
import enum


# ── Enums ─────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    worker = "worker"
    employer = "employer"
    admin = "admin"


class VideoStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class EmploymentType(str, enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"
    daily_wage = "daily_wage"


# ── Users ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"), nullable=False, default=UserRole.worker
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    worker_profile: Mapped["WorkerProfile"] = relationship(
        "WorkerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    employer_profile: Mapped["EmployerProfile"] = relationship(
        "EmployerProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role})>"


# ── Worker Profile ────────────────────────────────────────────────────────────

class WorkerProfile(Base):
    __tablename__ = "worker_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    full_name: Mapped[str | None] = mapped_column(String(200))
    bio: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(200))
    phone: Mapped[str | None] = mapped_column(String(20))
    years_experience: Mapped[int | None] = mapped_column(Integer)
    face_image_path: Mapped[str | None] = mapped_column(String(500))
    face_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="worker_profile")
    skills: Mapped[list["WorkerSkill"]] = relationship(
        "WorkerSkill", back_populates="worker", cascade="all, delete-orphan"
    )
    videos: Mapped[list["Video"]] = relationship(
        "Video", back_populates="worker", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<WorkerProfile {self.full_name}>"


# ── Worker Skills ─────────────────────────────────────────────────────────────

class WorkerSkill(Base):
    __tablename__ = "worker_skills"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worker_profiles.id", ondelete="CASCADE"), nullable=False
    )
    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    skill_category: Mapped[str | None] = mapped_column(String(100))
    years_experience: Mapped[int | None] = mapped_column(Integer)
    is_ai_extracted: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    worker: Mapped["WorkerProfile"] = relationship("WorkerProfile", back_populates="skills")

    def __repr__(self) -> str:
        return f"<WorkerSkill {self.skill_name}>"


# ── Employer Profile ──────────────────────────────────────────────────────────

class EmployerProfile(Base):
    __tablename__ = "employer_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    company_name: Mapped[str | None] = mapped_column(String(200))
    industry: Mapped[str | None] = mapped_column(String(100))
    location: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    website: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="employer_profile")
    job_postings: Mapped[list["JobPosting"]] = relationship(
        "JobPosting", back_populates="employer", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<EmployerProfile {self.company_name}>"


# ── Job Postings ──────────────────────────────────────────────────────────────

class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employer_profiles.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[list] = mapped_column(JSON, default=list)
    location: Mapped[str | None] = mapped_column(String(200))
    employment_type: Mapped[EmploymentType] = mapped_column(
        SAEnum(EmploymentType, name="employment_type"), default=EmploymentType.full_time
    )
    salary_min: Mapped[float | None] = mapped_column(Float)
    salary_max: Mapped[float | None] = mapped_column(Float)
    salary_currency: Mapped[str] = mapped_column(String(10), default="INR")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    employer: Mapped["EmployerProfile"] = relationship("EmployerProfile", back_populates="job_postings")

    def __repr__(self) -> str:
        return f"<JobPosting {self.title}>"


# ── Videos ───────────────────────────────────────────────────────────────────

class Video(Base):
    __tablename__ = "videos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    worker_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("worker_profiles.id", ondelete="CASCADE"), nullable=False
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(200))
    file_size_bytes: Mapped[int | None] = mapped_column(Integer)
    mime_type: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[VideoStatus] = mapped_column(
        SAEnum(VideoStatus, name="video_status"), default=VideoStatus.pending
    )

    # AI Processing results
    transcript: Mapped[str | None] = mapped_column(Text)
    detected_language: Mapped[str | None] = mapped_column(String(10))
    face_detected: Mapped[bool | None] = mapped_column(Boolean)
    face_confidence: Mapped[float | None] = mapped_column(Float)
    face_verified: Mapped[bool | None] = mapped_column(Boolean)
    face_similarity_score: Mapped[float | None] = mapped_column(Float)
    face_image_path: Mapped[str | None] = mapped_column(String(500))
    audio_path: Mapped[str | None] = mapped_column(String(500))
    audio_duration: Mapped[float | None] = mapped_column(Float)

    # Structured metadata (full pipeline JSON output)
    processing_metadata: Mapped[dict | None] = mapped_column(JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Relationships
    worker: Mapped["WorkerProfile"] = relationship("WorkerProfile", back_populates="videos")

    def __repr__(self) -> str:
        return f"<Video {self.id} [{self.status}]>"
