from datetime import datetime

from pydantic import BaseModel

from app.models.job import JobStatus


class JobOut(BaseModel):
    id: str
    status: JobStatus
    profile_id: str
    input_file: str
    output_file: str | None
    created_at: datetime
