import uuid
import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import aiofiles

from app.core.database import get_db
from app.core.deps import require_worker
from app.core.config import settings
from app.models.models import User, WorkerProfile, Video, WorkerSkill, VideoStatus
from app.schemas.schemas import VideoResponse
from app.services import ai_pipeline

router = APIRouter(prefix="/worker/videos", tags=["Videos"])

ALLOWED_MIME_TYPES = {
    "video/mp4", "video/webm", "video/quicktime",
    "video/x-msvideo", "video/mpeg", "video/x-matroska",
}


async def _run_pipeline_and_update(video_id: uuid.UUID, db_url: str):
    """
    Background task: run AI pipeline, then update DB with results.
    Uses a fresh DB session (not the request session).
    """
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Video).where(Video.id == video_id))
            video = result.scalar_one_or_none()
            if not video:
                return

            # Mark as processing
            video.status = VideoStatus.processing
            await db.commit()

            # Get worker profile for reference face
            worker_result = await db.execute(
                select(WorkerProfile).where(WorkerProfile.id == video.worker_id)
            )
            worker = worker_result.scalar_one_or_none()
            reference_face = worker.face_image_path if worker else None

            # Build file paths
            audio_path = str(settings.audio_dir / f"{video_id}.wav")
            face_path = str(settings.faces_dir / f"{video_id}.jpg")

            # Run pipeline (CPU-bound — run in threadpool)
            loop = asyncio.get_event_loop()
            pipeline_result = await loop.run_in_executor(
                None,
                lambda: ai_pipeline.process_video_pipeline(
                    video_id=str(video_id),
                    worker_id=str(video.worker_id),
                    video_path=video.file_path,
                    audio_output_path=audio_path,
                    face_output_path=face_path,
                    reference_face_path=reference_face,
                )
            )

            # Update video record
            video.processing_metadata = pipeline_result
            video.processed_at = datetime.utcnow()

            if pipeline_result["processing_status"] == "completed":
                video.status = VideoStatus.completed
                video.transcript = pipeline_result["transcription"].get("full_text")
                video.detected_language = pipeline_result["transcription"].get("language")
                video.face_detected = pipeline_result["face_detection"].get("face_detected")
                video.face_confidence = pipeline_result["face_detection"].get("confidence")
                video.face_verified = pipeline_result["face_verification"].get("is_verified")
                video.face_similarity_score = pipeline_result["face_verification"].get("similarity_score")
                video.face_image_path = pipeline_result["face_detection"].get("face_image_path")
                video.audio_path = pipeline_result["audio_processing"].get("audio_path")
                video.audio_duration = pipeline_result["audio_processing"].get("duration_seconds")

                # Update worker profile: reference face and verification status
                if worker:
                    if not worker.face_image_path:
                        worker.face_image_path = face_path
                    worker.face_verified = bool(video.face_verified)

                    # Auto-sync AI-extracted skills to worker profile
                    detected_skills = pipeline_result["skill_extraction"].get("detected_skills", [])
                    confidence_scores = pipeline_result["skill_extraction"].get("confidence_scores", [])
                    for i, skill_name in enumerate(detected_skills):
                        # Check if skill already exists
                        existing = await db.execute(
                            select(WorkerSkill).where(
                                WorkerSkill.worker_id == worker.id,
                                WorkerSkill.skill_name == skill_name,
                            )
                        )
                        if not existing.scalar_one_or_none():
                            db.add(WorkerSkill(
                                worker_id=worker.id,
                                skill_name=skill_name,
                                is_ai_extracted=True,
                                confidence_score=confidence_scores[i] if i < len(confidence_scores) else 0.8,
                            ))

                    # Update worker metadata from transcript
                    worker_meta = pipeline_result.get("worker_metadata", {})
                    if worker_meta.get("experience_years") and not worker.years_experience:
                        worker.years_experience = worker_meta["experience_years"]
                    if worker_meta.get("location_detected") and not worker.location:
                        worker.location = worker_meta["location_detected"]
                    if worker_meta.get("name_detected") and not worker.full_name:
                        worker.full_name = worker_meta["name_detected"]

            else:
                video.status = VideoStatus.failed

            await db.commit()

        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Pipeline background task error: {e}", exc_info=True)
            async with AsyncSessionLocal() as err_db:
                err_result = await err_db.execute(select(Video).where(Video.id == video_id))
                err_video = err_result.scalar_one_or_none()
                if err_video:
                    err_video.status = VideoStatus.failed
                    await err_db.commit()


@router.post("/upload", response_model=VideoResponse, status_code=202)
async def upload_video(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(require_worker),
    db: AsyncSession = Depends(get_db),
):
    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported video format: {file.content_type}. Allowed: mp4, webm, mov, avi"
        )

    # Read file and check size
    contents = await file.read()
    if len(contents) > settings.max_video_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_VIDEO_SIZE_MB}MB"
        )

    # Get worker profile
    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == current_user.id)
    )
    worker = result.scalar_one_or_none()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker profile not found")

    # Save video file
    video_id = uuid.uuid4()
    ext = Path(file.filename or "video.mp4").suffix or ".mp4"
    filename = f"{video_id}{ext}"
    video_path = settings.videos_dir / filename

    settings.videos_dir.mkdir(parents=True, exist_ok=True)
    settings.audio_dir.mkdir(parents=True, exist_ok=True)
    settings.faces_dir.mkdir(parents=True, exist_ok=True)

    async with aiofiles.open(video_path, "wb") as f:
        await f.write(contents)

    # Create DB record
    video = Video(
        id=video_id,
        worker_id=worker.id,
        file_path=str(video_path),
        file_name=file.filename or filename,
        file_size_bytes=len(contents),
        mime_type=file.content_type,
        status=VideoStatus.pending,
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    # Trigger AI pipeline in background
    background_tasks.add_task(
        _run_pipeline_and_update,
        video_id=video_id,
        db_url=settings.DATABASE_URL,
    )

    return video
