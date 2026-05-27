from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.deps import require_admin
from app.models.models import User, WorkerProfile, EmployerProfile, JobPosting, Video, VideoStatus, UserRole

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total_users = (await db.execute(select(func.count(User.id)))).scalar()
    total_workers = (await db.execute(select(func.count(User.id)).where(User.role == UserRole.worker))).scalar()
    total_employers = (await db.execute(select(func.count(User.id)).where(User.role == UserRole.employer))).scalar()
    total_jobs = (await db.execute(select(func.count(JobPosting.id)))).scalar()
    active_jobs = (await db.execute(select(func.count(JobPosting.id)).where(JobPosting.is_active == True))).scalar()
    total_videos = (await db.execute(select(func.count(Video.id)))).scalar()
    completed_videos = (await db.execute(select(func.count(Video.id)).where(Video.status == VideoStatus.completed))).scalar()
    failed_videos = (await db.execute(select(func.count(Video.id)).where(Video.status == VideoStatus.failed))).scalar()

    return {
        "total_users": total_users,
        "total_workers": total_workers,
        "total_employers": total_employers,
        "total_jobs": total_jobs,
        "active_jobs": active_jobs,
        "total_videos": total_videos,
        "completed_videos": completed_videos,
        "failed_videos": failed_videos,
    }


@router.get("/users")
async def list_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.get("/jobs")
async def list_all_jobs(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(JobPosting).order_by(JobPosting.created_at.desc()))
    jobs = result.scalars().all()
    return [
        {
            "id": str(j.id),
            "title": j.title,
            "location": j.location,
            "is_active": j.is_active,
            "created_at": j.created_at,
            "employer_id": str(j.employer_id),
        }
        for j in jobs
    ]


@router.get("/videos")
async def list_all_videos(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Video).order_by(Video.created_at.desc()).limit(50))
    videos = result.scalars().all()
    return [
        {
            "id": str(v.id),
            "worker_id": str(v.worker_id),
            "file_name": v.file_name,
            "status": v.status,
            "face_detected": v.face_detected,
            "face_verified": v.face_verified,
            "created_at": v.created_at,
        }
        for v in videos
    ]


@router.patch("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    import uuid
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await db.commit()
    return {"message": f"User {user_id} deactivated"}