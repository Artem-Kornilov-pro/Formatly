from datetime import datetime

from pydantic import BaseModel


class ValidationReportOut(BaseModel):
    id: str
    job_id: str
    issues_found: list[str]
    issues_fixed: list[str]
    created_at: datetime
