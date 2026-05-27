import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import require_worker
from app.models.models import User, WorkerProfile, WorkerSkill
from app.schemas.schemas import (
    WorkerProfileUpdate, WorkerProfileResponse,
    SkillCreate, SkillResponse, VideoResponse
)

router = APIRouter(prefix="/worker", tags=["Worker"])


async def _get_worker_profile(user: User, db: AsyncSession) -> WorkerProfile:
    result = await db.execute(
        select(WorkerProfile)
        .where(WorkerProfile.user_id == user.id)
        .options(selectinload(WorkerProfile.skills))
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Worker profile not found")
    return profile


@router.get("/profile", response_model=WorkerProfileResponse)
async def get_profile(
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    return await _get_worker_profile(current_user, db)


@router.patch("/profile", response_model=WorkerProfileResponse)
async def update_profile(
    body: WorkerProfileUpdate,
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_worker_profile(current_user, db)
    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/skills", response_model=list[SkillResponse])
async def get_skills(
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_worker_profile(current_user, db)
    return profile.skills


@router.post("/skills", response_model=SkillResponse, status_code=201)
async def add_skill(
    body: SkillCreate,
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_worker_profile(current_user, db)
    skill = WorkerSkill(
        worker_id=profile.id,
        skill_name=body.skill_name,
        skill_category=body.skill_category,
        years_experience=body.years_experience,
        is_ai_extracted=False,
    )
    db.add(skill)
    await db.commit()
    await db.refresh(skill)
    return skill


@router.delete("/skills/{skill_id}", status_code=204)
async def delete_skill(
    skill_id: uuid.UUID,
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_worker_profile(current_user, db)
    result = await db.execute(
        select(WorkerSkill).where(
            WorkerSkill.id == skill_id,
            WorkerSkill.worker_id == profile.id,
        )
    )
    skill = result.scalar_one_or_none()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    await db.delete(skill)
    await db.commit()


@router.get("/videos", response_model=list[VideoResponse])
async def get_videos(
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    from app.models.models import Video
    profile = await _get_worker_profile(current_user, db)
    result = await db.execute(
        select(Video).where(Video.worker_id == profile.id).order_by(Video.created_at.desc())
    )
    return result.scalars().all()
