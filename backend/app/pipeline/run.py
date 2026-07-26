import uuid
from collections.abc import Callable

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import async_session_maker
from app.core.storage import input_file_path, output_file_path
from app.models.formatting_profile import FormattingProfile
from app.models.job import Job, JobStatus
from app.models.validation_report import ValidationReport
from app.pipeline.formatter import apply_formatting
from app.pipeline.llm import ParagraphClassifier, build_classifier
from app.pipeline.parser import parse_docx
from app.pipeline.validator import validate_document


async def process_job(
    job_id: uuid.UUID,
    classifier: ParagraphClassifier | None = None,
    session_maker: Callable[[], AsyncSession] | async_sessionmaker | None = None,
) -> None:
    session_maker = session_maker or async_session_maker

    async with session_maker() as session:
        job = await session.get(Job, job_id)
        if job is None:
            return

        job.status = JobStatus.PROCESSING
        await session.commit()

        try:
            profile = await session.get(FormattingProfile, job.profile_id)
            paragraphs = parse_docx(input_file_path(job.id))

            active_classifier = classifier or build_classifier()
            classified = active_classifier.classify(paragraphs)

            output_path = output_file_path(job.id)
            changes = apply_formatting(
                input_file_path(job.id), output_path, classified, profile.rules
            )
            issues_found = validate_document(output_path, classified, profile.rules)

            # reprocessing an already-done job would otherwise hit the
            # unique constraint on validation_reports.job_id
            await session.execute(delete(ValidationReport).where(ValidationReport.job_id == job.id))
            session.add(
                ValidationReport(job_id=job.id, issues_found=issues_found, issues_fixed=changes)
            )
            job.status = JobStatus.DONE
            job.output_file = output_path.name
            job.error_message = None
            await session.commit()
        except Exception as exc:  # noqa: BLE001 - any failure here must land the job as FAILED
            job.status = JobStatus.FAILED
            job.error_message = str(exc)[:1000]
            await session.commit()
