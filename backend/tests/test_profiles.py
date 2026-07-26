from httpx import AsyncClient


async def _authed_headers(client: AsyncClient, email: str) -> dict[str, str]:
    password = "correct-horse-battery-staple"
    await client.post("/auth/register", json={"email": email, "password": password})
    login = await client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


async def test_get_my_profile_requires_auth(client: AsyncClient):
    response = await client.get("/profiles/me")

    assert response.status_code in (401, 403)


async def test_get_my_profile_returns_system_defaults_when_nothing_saved(
    client: AsyncClient, system_profile_id: str
):
    headers = await _authed_headers(client, "student@example.com")

    response = await client.get("/profiles/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["font_family"] == "Times New Roman"
    assert body["paragraph_indent_mm"] == 12.5


async def test_put_my_profile_creates_and_returns_custom_settings(
    client: AsyncClient, system_profile_id: str
):
    headers = await _authed_headers(client, "student@example.com")
    payload = {"font_family": "Arial", "center_headings": False, "paragraph_indent_mm": 10}

    response = await client.put("/profiles/me", json=payload, headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["font_family"] == "Arial"
    assert body["center_headings"] is False
    assert body["paragraph_indent_mm"] == 10
    # untouched fields still default
    assert body["font_size_pt"] == 14


async def test_put_my_profile_persists_across_requests(
    client: AsyncClient, system_profile_id: str
):
    headers = await _authed_headers(client, "student@example.com")
    await client.put("/profiles/me", json={"font_family": "Georgia"}, headers=headers)

    response = await client.get("/profiles/me", headers=headers)

    assert response.status_code == 200
    assert response.json()["font_family"] == "Georgia"


async def test_put_my_profile_updates_in_place_rather_than_duplicating(
    client: AsyncClient, system_profile_id: str
):
    headers = await _authed_headers(client, "student@example.com")
    await client.put("/profiles/me", json={"font_family": "Georgia"}, headers=headers)
    await client.put("/profiles/me", json={"font_family": "Verdana"}, headers=headers)

    response = await client.get("/profiles/me", headers=headers)

    assert response.json()["font_family"] == "Verdana"


async def test_settings_are_isolated_per_user(client: AsyncClient, system_profile_id: str):
    headers_a = await _authed_headers(client, "alice@example.com")
    headers_b = await _authed_headers(client, "bob@example.com")

    await client.put("/profiles/me", json={"font_family": "Comic Sans MS"}, headers=headers_a)

    response_b = await client.get("/profiles/me", headers=headers_b)

    assert response_b.json()["font_family"] == "Times New Roman"


async def test_put_my_profile_rejects_invalid_values(client: AsyncClient, system_profile_id: str):
    headers = await _authed_headers(client, "student@example.com")

    response = await client.put(
        "/profiles/me", json={"paragraph_alignment": "diagonal"}, headers=headers
    )

    assert response.status_code == 422
