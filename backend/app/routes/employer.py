import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import require_employer, get_current_user
from app.models.models import User, EmployerProfile, JobPosting
from app.schemas.schemas import (
    EmployerProfileUpdate, EmployerProfileResponse,
    JobCreate, JobResponse
)

router = APIRouter(prefix="/employer", tags=["Employer"])


async def _get_employer_profile(user: User, db: AsyncSession) -> EmployerProfile:
    result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Employer profile not found")
    return profile


@router.get("/profile", response_model=EmployerProfileResponse)
async def get_profile(
    current_user: User = Depends(require_employer),
    db: AsyncSession = Depends(get_db),
):
    return await _get_employer_profile(current_user, db)


@router.patch("/profile", response_model=EmployerProfileResponse)
async def update_profile(
    body: EmployerProfileUpdate,
    current_user: User = Depends(require_employer),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_employer_profile(current_user, db)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.post("/jobs", response_model=JobResponse, status_code=201)
async def create_job(
    body: JobCreate,
    current_user: User = Depends(require_employer),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_employer_profile(current_user, db)
    job = JobPosting(
        employer_id=profile.id,
        **body.model_dump()
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


@router.get("/jobs", response_model=list[JobResponse])
async def get_my_jobs(
    current_user: User = Depends(require_employer),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_employer_profile(current_user, db)
    result = await db.execute(
        select(JobPosting)
        .where(JobPosting.employer_id == profile.id)
        .order_by(JobPosting.created_at.desc())
    )
    return result.scalars().all()


# ⚠️ MUST be before /jobs/{job_id} so FastAPI doesn't swallow "candidates" as a UUID
@router.get("/jobs/{job_id}/candidates")
async def get_job_candidates(
    job_id: uuid.UUID,
    current_user: User = Depends(require_employer),
    db: AsyncSession = Depends(get_db),
):
    import asyncio
    from app.models.models import WorkerProfile, Video, VideoStatus
    from app.services.matching import compute_matches

    profile = await _get_employer_profile(current_user, db)
    result = await db.execute(
        select(JobPosting).where(
            JobPosting.id == job_id,
            JobPosting.employer_id == profile.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    job_dict = {
        "id": str(job.id),
        "title": job.title,
        "description": job.description,
        "required_skills": job.required_skills or [],
        "location": job.location or "",
        "employment_type": job.employment_type.value if job.employment_type else "",
        "salary_min": job.salary_min,
        "salary_max": job.salary_max,
        "salary_currency": job.salary_currency,
        "is_active": job.is_active,
        "created_at": str(job.created_at),
        "employer_id": str(job.employer_id),
    }

    workers_result = await db.execute(
        select(WorkerProfile).options(selectinload(WorkerProfile.skills))
    )
    workers = workers_result.scalars().all()

    candidates = []
    for worker in workers:
        skill_names = [s.skill_name for s in worker.skills]

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

        worker_text = " ".join(
            filter(None, [worker.bio or "", " ".join(skill_names), transcript])
        ).strip()

        if not worker_text:
            continue

        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None,
            lambda wt=worker_text, sn=skill_names: compute_matches(wt, sn, [job_dict], 1),
        )

        if raw:
            m = raw[0]
            candidates.append({
                "worker_id": str(worker.user_id),
                "full_name": worker.full_name,
                "location": worker.location,
                "years_experience": worker.years_experience,
                "face_verified": worker.face_verified,
                "skills": skill_names,
                "final_score": m["final_score"],
                "semantic_score": m["semantic_score"],
                "skill_score": m["skill_score"],
                "matched_skills": m["matched_skills"],
            })

    candidates.sort(key=lambda x: x["final_score"], reverse=True)
    return {
        "job_id": str(job_id),
        "total_candidates": len(candidates),
        "candidates": candidates[:20],
    }


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_employer),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(JobPosting).where(JobPosting.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.delete("/jobs/{job_id}", status_code=204)
async def delete_job(
    job_id: uuid.UUID,
    current_user: User = Depends(require_employer),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_employer_profile(current_user, db)
    result = await db.execute(
        select(JobPosting).where(
            JobPosting.id == job_id,
            JobPosting.employer_id == profile.id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.delete(job)
    await db.commit()


# Public: all active jobs
@router.get("/public/jobs", response_model=list[JobResponse], tags=["Public"])
async def list_all_jobs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(JobPosting)
        .where(JobPosting.is_active == True)
        .order_by(JobPosting.created_at.desc())
    )
    return result.scalars().all()

