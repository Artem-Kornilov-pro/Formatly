import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings


def input_file_path(job_id: uuid.UUID) -> Path:
    return Path(get_settings().uploads_dir) / f"{job_id}.docx"


def output_file_path(job_id: uuid.UUID) -> Path:
    return Path(get_settings().uploads_dir) / f"{job_id}_output.docx"


async def save_input_file(job_id: uuid.UUID, upload: UploadFile) -> None:
    path = input_file_path(job_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(await upload.read())
