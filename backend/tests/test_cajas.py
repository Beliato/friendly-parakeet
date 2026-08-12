def test_crear_caja(client, auth_headers):
    r = client.post(
        "/cajas",
        json={"etiqueta": "Caja B", "descripcion": "Bajo la cama"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["etiqueta"] == "Caja B"


def test_caja_duplicada_409(client, auth_headers, caja):
    r = client.post("/cajas", json={"etiqueta": "Caja A"}, headers=auth_headers)
    assert r.status_code == 409


def test_listar_cajas(client, auth_headers, caja):
    r = client.get("/cajas", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_cajas_requieren_auth(client, caja, item):
    assert client.get("/cajas").status_code == 403
    assert client.post("/cajas", json={"etiqueta": "X"}).status_code == 403
    assert (
        client.patch(f"/items/{item.id}/caja", json={"caja_id": 1}).status_code == 403
    )


def test_asignar_caja_solo_a_adquirido(client, auth_headers, caja, item):
    r = client.patch(
        f"/items/{item.id}/caja", json={"caja_id": caja.id}, headers=auth_headers
    )
    assert r.status_code == 409


def test_asignar_y_quitar_caja(client, auth_headers, caja, item):
    client.patch(
        f"/items/{item.id}/adquirir",
        json={"origen": "NOSOTROS"},
        headers=auth_headers,
    )
    r = client.patch(
        f"/items/{item.id}/caja", json={"caja_id": caja.id}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["caja"]["etiqueta"] == "Caja A"

    r = client.patch(
        f"/items/{item.id}/caja", json={"caja_id": None}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["caja"] is None


def test_asignar_caja_inexistente_404(client, auth_headers, item):
    client.patch(
        f"/items/{item.id}/adquirir",
        json={"origen": "NOSOTROS"},
        headers=auth_headers,
    )
    r = client.patch(
        f"/items/{item.id}/caja", json={"caja_id": 999}, headers=auth_headers
    )
    assert r.status_code == 404


def test_asignar_caja_item_inexistente_404(client, auth_headers, caja):
    r = client.patch("/items/999/caja", json={"caja_id": caja.id}, headers=auth_headers)
    assert r.status_code == 404
