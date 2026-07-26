import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.db import get_db
from app.core.storage import output_file_path, save_input_file
from app.models.formatting_profile import FormattingProfile
from app.models.job import Job, JobStatus
from app.models.user import User
from app.models.validation_report import ValidationReport
from app.schemas.job import JobOut
from app.schemas.validation_report import ValidationReportOut
from app.services.profiles import resolve_default_profile
from app.worker import process_job as process_job_task

router = APIRouter(prefix="/jobs", tags=["jobs"])

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
ALLOWED_CONTENT_TYPES = {DOCX_CONTENT_TYPE}


def _job_out(job: Job) -> JobOut:
    return JobOut(
        id=str(job.id),
        status=job.status,
        profile_id=str(job.profile_id),
        input_file=job.input_file,
        output_file=job.output_file,
        error_message=job.error_message,
        created_at=job.created_at,
    )


async def _resolve_profile(
    profile_id: uuid.UUID | None, user: User, db: AsyncSession
) -> FormattingProfile:
    if profile_id is not None:
        profile = await db.get(FormattingProfile, profile_id)
        # system profiles (owner_id is None) are usable by anyone; a
        # personal profile is only usable by its own owner
        if profile is None or (profile.owner_id is not None and profile.owner_id != user.id):
            raise HTTPException(status.HTTP_404_NOT_FOUND, "Formatting profile not found")
        return profile

    profile = await resolve_default_profile(user, db)
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

    profile = await _resolve_profile(profile_id, user, db)

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

    process_job_task.delay(str(job.id))

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


@router.get("/{job_id}/download")
async def download_job_output(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    job = await db.get(Job, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")

    if job.status != JobStatus.DONE or job.output_file is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Job output is not ready yet")

    path = output_file_path(job.id)
    if not path.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Output file not found")

    download_name = f"{Path(job.input_file).stem}_formatted.docx"

    return FileResponse(path, media_type=DOCX_CONTENT_TYPE, filename=download_name)


@router.get("/{job_id}/report", response_model=ValidationReportOut)
async def get_job_report(
    job_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ValidationReportOut:
    job = await db.get(Job, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Job not found")

    if job.status != JobStatus.DONE:
        raise HTTPException(status.HTTP_409_CONFLICT, "Job output is not ready yet")

    report = await db.scalar(
        select(ValidationReport).where(ValidationReport.job_id == job.id)
    )
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")

    return ValidationReportOut(
        id=str(report.id),
        job_id=str(report.job_id),
        issues_found=report.issues_found,
        issues_fixed=report.issues_fixed,
        created_at=report.created_at,
    )
