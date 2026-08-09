def test_login_ok(client, admin):
    r = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "clave-test-123"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_password_incorrecta(client, admin):
    r = client.post(
        "/auth/login",
        json={"email": "admin@test.com", "password": "incorrecta"},
    )
    assert r.status_code == 401


def test_login_email_inexistente(client, admin):
    r = client.post(
        "/auth/login",
        json={"email": "nadie@test.com", "password": "clave-test-123"},
    )
    assert r.status_code == 401


def test_login_email_case_insensitive(client, admin):
    r = client.post(
        "/auth/login",
        json={"email": "ADMIN@test.com", "password": "clave-test-123"},
    )
    assert r.status_code == 200


def test_me_ok(client, admin, auth_headers):
    r = client.get("/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["email"] == "admin@test.com"


def test_me_token_invalido(client):
    r = client.get("/auth/me", headers={"Authorization": "Bearer basura"})
    assert r.status_code == 401


def test_me_sin_token(client):
    assert client.get("/auth/me").status_code == 403


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
