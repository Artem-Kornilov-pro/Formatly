import io
import uuid

from docx import Document
from httpx import AsyncClient
from sqlalchemy import select

from app.core.storage import output_file_path
from app.models.formatting_profile import FormattingProfile
from app.models.job import Job, JobStatus
from app.models.validation_report import ValidationReport
from tests.conftest import test_session_maker as make_test_session

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _make_docx_bytes() -> bytes:
    document = Document()
    document.add_paragraph("Hello, Formatly!")
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


async def _authed_headers(client: AsyncClient, email: str) -> dict[str, str]:
    password = "correct-horse-battery-staple"
    await client.post("/auth/register", json={"email": email, "password": password})
    login = await client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _upload_files(filename: str = "thesis.docx", content_type: str = DOCX_CONTENT_TYPE):
    return {"file": (filename, _make_docx_bytes(), content_type)}


async def test_create_job_requires_auth(client: AsyncClient):
    response = await client.post("/jobs", files=_upload_files())

    assert response.status_code in (401, 403)


async def test_create_job_uploads_docx_with_default_profile(
    client: AsyncClient, system_profile_id: str
):
    headers = await _authed_headers(client, "student@example.com")

    response = await client.post("/jobs", files=_upload_files(), headers=headers)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["input_file"] == "thesis.docx"
    assert body["output_file"] is None
    assert body["profile_id"] == system_profile_id


async def test_create_job_rejects_non_docx_file(client: AsyncClient, system_profile_id: str):
    headers = await _authed_headers(client, "student@example.com")

    response = await client.post(
        "/jobs",
        files=_upload_files(filename="thesis.txt", content_type="text/plain"),
        headers=headers,
    )

    assert response.status_code == 422


async def test_create_job_rejects_unknown_profile(client: AsyncClient, system_profile_id: str):
    headers = await _authed_headers(client, "student@example.com")

    response = await client.post(
        "/jobs",
        files=_upload_files(),
        data={"profile_id": str(uuid.uuid4())},
        headers=headers,
    )

    assert response.status_code == 404


async def test_create_job_rejects_another_users_private_profile(
    client: AsyncClient, system_profile_id: str
):
    headers_a = await _authed_headers(client, "alice@example.com")
    headers_b = await _authed_headers(client, "bob@example.com")

    await client.put("/profiles/me", json={"font_family": "Georgia"}, headers=headers_a)
    alice_id = (await client.get("/auth/me", headers=headers_a)).json()["id"]

    async with make_test_session() as session:
        alice_profile = await session.scalar(
            select(FormattingProfile).where(FormattingProfile.owner_id == uuid.UUID(alice_id))
        )
    assert alice_profile is not None

    response = await client.post(
        "/jobs",
        files=_upload_files(),
        data={"profile_id": str(alice_profile.id)},
        headers=headers_b,
    )

    assert response.status_code == 404


async def test_create_job_uses_the_users_own_saved_profile_by_default(
    client: AsyncClient, system_profile_id: str
):
    headers = await _authed_headers(client, "student@example.com")
    await client.put("/profiles/me", json={"font_family": "Georgia"}, headers=headers)

    response = await client.post("/jobs", files=_upload_files(), headers=headers)

    assert response.status_code == 201
    assert response.json()["profile_id"] != system_profile_id


async def test_list_jobs_returns_only_current_users_jobs(
    client: AsyncClient, system_profile_id: str
):
    headers_a = await _authed_headers(client, "alice@example.com")
    headers_b = await _authed_headers(client, "bob@example.com")

    await client.post("/jobs", files=_upload_files("alice.docx"), headers=headers_a)
    await client.post("/jobs", files=_upload_files("bob.docx"), headers=headers_b)

    response = await client.get("/jobs", headers=headers_a)

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["input_file"] == "alice.docx"


async def test_get_job_by_id(client: AsyncClient, system_profile_id: str):
    headers = await _authed_headers(client, "student@example.com")
    created = (await client.post("/jobs", files=_upload_files(), headers=headers)).json()

    response = await client.get(f"/jobs/{created['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


async def test_get_job_404_for_other_users_job(client: AsyncClient, system_profile_id: str):
    headers_a = await _authed_headers(client, "alice@example.com")
    headers_b = await _authed_headers(client, "bob@example.com")
    created = (await client.post("/jobs", files=_upload_files(), headers=headers_a)).json()

    response = await client.get(f"/jobs/{created['id']}", headers=headers_b)

    assert response.status_code == 404


async def test_get_job_404_for_unknown_id(client: AsyncClient, system_profile_id: str):
    headers = await _authed_headers(client, "student@example.com")

    response = await client.get(f"/jobs/{uuid.uuid4()}", headers=headers)

    assert response.status_code == 404


async def _mark_job_done(
    job_id: str,
    content: bytes = b"formatted docx bytes",
    issues_found: list[str] | None = None,
    issues_fixed: list[str] | None = None,
) -> None:
    job_uuid = uuid.UUID(job_id)
    async with make_test_session() as session:
        job = await session.get(Job, job_uuid)
        job.status = JobStatus.DONE
        job.output_file = output_file_path(job_uuid).name
        session.add(
            ValidationReport(
                job_id=job_uuid,
                issues_found=issues_found if issues_found is not None else [],
                issues_fixed=issues_fixed if issues_fixed is not None else ["applied formatting"],
            )
        )
        await session.commit()

    path = output_file_path(job_uuid)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


async def test_download_requires_auth(client: AsyncClient, system_profile_id: str):
    headers = await _authed_headers(client, "student@example.com")
    created = (await client.post("/jobs", files=_upload_files(), headers=headers)).json()

    response = await client.get(f"/jobs/{created['id']}/download")

    assert response.status_code in (401, 403)


async def test_download_404_for_unknown_job(client: AsyncClient, system_profile_id: str):
    headers = await _authed_headers(client, "student@example.com")

    response = await client.get(f"/jobs/{uuid.uuid4()}/download", headers=headers)

    assert response.status_code == 404


async def test_download_404_for_other_users_job(client: AsyncClient, system_profile_id: str):
    headers_a = await _authed_headers(client, "alice@example.com")
    headers_b = await _authed_headers(client, "bob@example.com")
    created = (await client.post("/jobs", files=_upload_files(), headers=headers_a)).json()
    await _mark_job_done(created["id"], content=b"formatted docx bytes")

    response = await client.get(f"/jobs/{created['id']}/download", headers=headers_b)

    assert response.status_code == 404


async def test_download_409_when_job_not_done(client: AsyncClient, system_profile_id: str):
    headers = await _authed_headers(client, "student@example.com")
    created = (await client.post("/jobs", files=_upload_files(), headers=headers)).json()
    assert created["status"] == "pending"

    response = await client.get(f"/jobs/{created['id']}/download", headers=headers)

    assert response.status_code == 409


async def test_download_returns_output_file_when_done(
    client: AsyncClient, system_profile_id: str
):
    headers = await _authed_headers(client, "student@example.com")
    created = (
        await client.post("/jobs", files=_upload_files("thesis.docx"), headers=headers)
    ).json()
    await _mark_job_done(created["id"], content=b"formatted docx bytes")

    response = await client.get(f"/jobs/{created['id']}/download", headers=headers)

    assert response.status_code == 200
    assert response.content == b"formatted docx bytes"
    assert response.headers["content-type"] == DOCX_CONTENT_TYPE
    assert 'filename="thesis_formatted.docx"' in response.headers["content-disposition"]


async def test_get_report_requires_auth(client: AsyncClient, system_profile_id: str):
    headers = await _authed_headers(client, "student@example.com")
    created = (await client.post("/jobs", files=_upload_files(), headers=headers)).json()

    response = await client.get(f"/jobs/{created['id']}/report")

    assert response.status_code in (401, 403)


async def test_get_report_404_for_unknown_job(client: AsyncClient, system_profile_id: str):
    headers = await _authed_headers(client, "student@example.com")

    response = await client.get(f"/jobs/{uuid.uuid4()}/report", headers=headers)

    assert response.status_code == 404


async def test_get_report_404_for_other_users_job(client: AsyncClient, system_profile_id: str):
    headers_a = await _authed_headers(client, "alice@example.com")
    headers_b = await _authed_headers(client, "bob@example.com")
    created = (await client.post("/jobs", files=_upload_files(), headers=headers_a)).json()
    await _mark_job_done(created["id"])

    response = await client.get(f"/jobs/{created['id']}/report", headers=headers_b)

    assert response.status_code == 404


async def test_get_report_409_when_job_not_done(client: AsyncClient, system_profile_id: str):
    headers = await _authed_headers(client, "student@example.com")
    created = (await client.post("/jobs", files=_upload_files(), headers=headers)).json()
    assert created["status"] == "pending"

    response = await client.get(f"/jobs/{created['id']}/report", headers=headers)

    assert response.status_code == 409


async def test_get_report_returns_issues_when_done(client: AsyncClient, system_profile_id: str):
    headers = await _authed_headers(client, "student@example.com")
    created = (await client.post("/jobs", files=_upload_files(), headers=headers)).json()
    await _mark_job_done(
        created["id"],
        issues_found=["left margin is 25mm, expected 30mm"],
        issues_fixed=["set page margins to 20/20/30/15mm (top/bottom/left/right)"],
    )

    response = await client.get(f"/jobs/{created['id']}/report", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["job_id"] == created["id"]
    assert body["issues_found"] == ["left margin is 25mm, expected 30mm"]
    assert body["issues_fixed"] == ["set page margins to 20/20/30/15mm (top/bottom/left/right)"]
