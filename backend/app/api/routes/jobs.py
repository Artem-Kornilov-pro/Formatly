import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.storage import save_input_file
from app.models.formatting_profile import FormattingProfile
from app.models.job import Job, JobStatus
from app.models.user import User
from app.schemas.job import JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])

ALLOWED_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _job_out(job: Job) -> JobOut:
    return JobOut(
        id=str(job.id),
        status=job.status,
        profile_id=str(job.profile_id),
        input_file=job.input_file,
        output_file=job.output_file,
        created_at=job.created_at,
    )


async def _resolve_profile(
    profile_id: uuid.UUID | None, db: AsyncSession
) -> FormattingProfile:
    if profile_id is not None:
        profile = await db.get(FormattingProfile, profile_id)
        if profile is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Formatting profile not found")
        return profile

    profile = await db.scalar(
        select(FormattingProfile)
        .where(FormattingProfile.owner_id.is_(None))
        .order_by(FormattingProfile.created_at)
        .limit(1)
    )
    if profile is None:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR, "No default formatting profile configured"
        )
    return profile


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
async def create_job(
    file: UploadFile = File(...),
    profile_id: uuid.UUID | None = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobOut:
    if not file.filename or not file.filename.lower().endswith(".docx"):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Only .docx files are supported")
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Only .docx files are supported")

    profile = await _resolve_profile(profile_id, db)

    job_id = uuid.uuid4()
    await save_input_file(job_id, file)

    job = Job(
        id=job_id,
        user_id=user.id,
        profile_id=profile.id,
        status=JobStatus.PENDING,
        input_file=file.filename,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    return _job_out(job)


@router.get("", response_model=list[JobOut])
async def list_jobs(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[JobOut]:
    jobs = await db.scalars(
        select(Job).where(Job.user_id == user.id).order_by(Job.created_at.desc())
    )
    return [_job_out(job) for job in jobs]


@router.get("/{job_id}", response_model=JobOut)
async def get_job(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobOut:
    job = await db.get(Job, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")

    return _job_out(job)
