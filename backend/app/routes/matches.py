import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import require_worker
from app.models.models import User, WorkerProfile, WorkerSkill, JobPosting, Video, VideoStatus
from app.schemas.schemas import MatchResponse, JobMatchResult, JobResponse
from app.services.matching import compute_matches

router = APIRouter(prefix="/worker", tags=["Matching"])


@router.get("/matches", response_model=MatchResponse)
async def get_job_matches(
    top_k: int = 20,
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    # Get worker profile with skills
    profile_result = await db.execute(
        select(WorkerProfile)
        .where(WorkerProfile.user_id == current_user.id)
        .options(selectinload(WorkerProfile.skills))
    )
    worker = profile_result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    # Get latest completed video transcript
    video_result = await db.execute(
        select(Video)
        .where(
            Video.worker_id == worker.id,
            Video.status == VideoStatus.completed,
        )
        .order_by(Video.created_at.desc())
        .limit(1)
    )
    latest_video = video_result.scalar_one_or_none()
    transcript = (latest_video.transcript or "") if latest_video else ""

    # Build worker text for SBERT
    skill_names = [s.skill_name for s in worker.skills]
    worker_text_parts = [
        worker.bio or "",
        " ".join(skill_names),
        transcript,
    ]
    worker_text = " ".join(p for p in worker_text_parts if p).strip()

    if not worker_text:
        raise HTTPException(
            status_code=400,
            detail="Your profile has no content for matching. Add skills or upload a video."
        )

    # Get all active jobs
    jobs_result = await db.execute(
        select(JobPosting).where(JobPosting.is_active == True)
    )
    job_rows = jobs_result.scalars().all()

    if not job_rows:
        return MatchResponse(
            worker_id=worker.user_id,
            total_jobs_evaluated=0,
            matches=[],
        )

    # Convert to dicts for matching engine
    job_dicts = [
        {
            "id": str(job.id),
            "title": job.title,
            "description": job.description,
            "required_skills": job.required_skills or [],
            "location": job.location,
            "employment_type": job.employment_type,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "salary_currency": job.salary_currency,
            "is_active": job.is_active,
            "created_at": job.created_at,
            "employer_id": str(job.employer_id),
        }
        for job in job_rows
    ]

    # Run matching (threadpool — CPU-bound model inference)
    import asyncio
    loop = asyncio.get_event_loop()
    raw_matches = await loop.run_in_executor(
        None,
        lambda: compute_matches(worker_text, skill_names, job_dicts, top_k)
    )

    # Build response
    matches = []
    for m in raw_matches:
        job_dict = m["job"]
        job_response = JobResponse(
            id=uuid.UUID(job_dict["id"]),
            employer_id=uuid.UUID(job_dict["employer_id"]),
            title=job_dict["title"],
            description=job_dict["description"],
            required_skills=job_dict["required_skills"],
            location=job_dict.get("location"),
            employment_type=job_dict["employment_type"],
            salary_min=job_dict.get("salary_min"),
            salary_max=job_dict.get("salary_max"),
            salary_currency=job_dict["salary_currency"],
            is_active=job_dict["is_active"],
            created_at=job_dict["created_at"],
        )
        matches.append(JobMatchResult(
            job=job_response,
            final_score=m["final_score"],
            semantic_score=m["semantic_score"],
            skill_score=m["skill_score"],
            matched_skills=m["matched_skills"],
        ))

    return MatchResponse(
        worker_id=worker.user_id,
        total_jobs_evaluated=len(job_rows),
        matches=matches,
    )
