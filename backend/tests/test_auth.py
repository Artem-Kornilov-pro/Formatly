from httpx import AsyncClient

EMAIL = "student@example.com"
PASSWORD = "correct-horse-battery-staple"


async def _register(client: AsyncClient, email: str = EMAIL, password: str = PASSWORD):
    return await client.post("/auth/register", json={"email": email, "password": password})


async def _login(client: AsyncClient, email: str = EMAIL, password: str = PASSWORD):
    return await client.post("/auth/login", json={"email": email, "password": password})


async def test_register_creates_user(client: AsyncClient):
    response = await _register(client)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == EMAIL
    assert "id" in body
    assert "password" not in body


async def test_register_rejects_duplicate_email(client: AsyncClient):
    await _register(client)

    response = await _register(client)

    assert response.status_code == 409


async def test_register_rejects_short_password(client: AsyncClient):
    response = await _register(client, password="short")

    assert response.status_code == 422


async def test_login_returns_token_pair(client: AsyncClient):
    await _register(client)

    response = await _login(client)

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["access_token"] != body["refresh_token"]
    assert body["token_type"] == "bearer"


async def test_login_rejects_wrong_password(client: AsyncClient):
    await _register(client)

    response = await _login(client, password="not the right password")

    assert response.status_code == 401


async def test_login_rejects_unknown_email(client: AsyncClient):
    response = await _login(client, email="ghost@example.com")

    assert response.status_code == 401


async def test_me_returns_current_user_with_valid_access_token(client: AsyncClient):
    await _register(client)
    tokens = (await _login(client)).json()

    response = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )

    assert response.status_code == 200
    assert response.json()["email"] == EMAIL


async def test_me_rejects_missing_token(client: AsyncClient):
    response = await client.get("/auth/me")

    assert response.status_code in (401, 403)


async def test_me_rejects_garbage_token(client: AsyncClient):
    response = await client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert response.status_code == 401


async def test_refresh_rotates_tokens(client: AsyncClient):
    await _register(client)
    first = (await _login(client)).json()

    response = await client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})

    assert response.status_code == 200
    rotated = response.json()
    assert rotated["access_token"] != first["access_token"]
    assert rotated["refresh_token"] != first["refresh_token"]

    # the new access token works
    me = await client.get(
        "/auth/me", headers={"Authorization": f"Bearer {rotated['access_token']}"}
    )
    assert me.status_code == 200

    # the old refresh token was consumed and can't be reused
    reuse = await client.post("/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert reuse.status_code == 401


async def test_refresh_rejects_unknown_token(client: AsyncClient):
    response = await client.post("/auth/refresh", json={"refresh_token": "not-a-real-token"})

    assert response.status_code == 401


async def test_logout_invalidates_refresh_token(client: AsyncClient):
    await _register(client)
    tokens = (await _login(client)).json()

    logout = await client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert logout.status_code == 204

    refresh = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh.status_code == 401
