import pytest

from app.core import storage_r2
from app.models.item import FotoItem


@pytest.fixture
def r2_configurado(monkeypatch):
    monkeypatch.setattr(storage_r2, "esta_configurado", lambda: True)
    monkeypatch.setattr(
        storage_r2, "presign_put", lambda key, ct: f"https://r2.fake/put/{key}"
    )
    monkeypatch.setattr(storage_r2, "objeto_existe", lambda key: True)
    monkeypatch.setattr(storage_r2, "borrar_objeto", lambda key: None)
    monkeypatch.setattr(
        storage_r2, "url_publica", lambda key: f"https://cdn.fake/{key}"
    )


def test_presign_sin_r2_503(client, auth_headers, item):
    r = client.post(
        f"/items/{item.id}/fotos/presign",
        json={"content_type": "image/png", "size_bytes": 1000},
        headers=auth_headers,
    )
    assert r.status_code == 503


def test_presign_ok(client, auth_headers, item, r2_configurado):
    r = client.post(
        f"/items/{item.id}/fotos/presign",
        json={"content_type": "image/png", "size_bytes": 1000},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["key"].startswith(f"items/{item.id}/")
    assert body["upload_url"].startswith("https://r2.fake/put/")


def test_presign_tipo_no_permitido(client, auth_headers, item, r2_configurado):
    r = client.post(
        f"/items/{item.id}/fotos/presign",
        json={"content_type": "application/pdf", "size_bytes": 1000},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_presign_muy_grande(client, auth_headers, item, r2_configurado):
    r = client.post(
        f"/items/{item.id}/fotos/presign",
        json={"content_type": "image/png", "size_bytes": 6 * 1024 * 1024},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_confirmar_foto_ok(client, auth_headers, item, r2_configurado):
    key = storage_r2.generar_key(item.id, "image/png")
    r = client.post(
        f"/items/{item.id}/fotos",
        json={"key": key, "orden": 0},
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["url"] == f"https://cdn.fake/{key}"


def test_confirmar_key_de_otro_item_422(client, auth_headers, item, r2_configurado):
    key = storage_r2.generar_key(item.id + 100, "image/png")
    r = client.post(
        f"/items/{item.id}/fotos",
        json={"key": key, "orden": 0},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_confirmar_objeto_inexistente_422(
    client, auth_headers, item, r2_configurado, monkeypatch
):
    monkeypatch.setattr(storage_r2, "objeto_existe", lambda key: False)
    key = storage_r2.generar_key(item.id, "image/png")
    r = client.post(
        f"/items/{item.id}/fotos",
        json={"key": key, "orden": 0},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_eliminar_foto(client, auth_headers, item, r2_configurado, db):
    foto = FotoItem(item_id=item.id, url="https://cdn.fake/items/1/x.jpg", orden=0)
    db.add(foto)
    db.commit()
    r = client.delete(f"/items/{item.id}/fotos/{foto.id}", headers=auth_headers)
    assert r.status_code == 204
    assert db.query(FotoItem).count() == 0


def test_eliminar_foto_inexistente_404(client, auth_headers, item):
    r = client.delete(f"/items/{item.id}/fotos/999", headers=auth_headers)
    assert r.status_code == 404


def test_fotos_requieren_auth(client, item):
    r = client.post(
        f"/items/{item.id}/fotos/presign",
        json={"content_type": "image/png", "size_bytes": 100},
    )
    assert r.status_code == 403


def test_key_pertenece_a_item():
    key_ok = "items/5/9c5b94b1-35ad-49bb-b118-8e8fc24abf80.jpg"
    assert storage_r2.key_pertenece_a_item(key_ok, 5)
    assert not storage_r2.key_pertenece_a_item(key_ok, 6)
    assert not storage_r2.key_pertenece_a_item("otra/cosa.exe", 5)
    assert not storage_r2.key_pertenece_a_item("items/5/../../evil.jpg", 5)


def test_key_desde_url(monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "R2_PUBLIC_URL", "https://cdn.fake")
    assert storage_r2.key_desde_url("https://cdn.fake/items/1/a.jpg") == "items/1/a.jpg"
    assert storage_r2.key_desde_url("https://otro.host/items/1/a.jpg") is None
