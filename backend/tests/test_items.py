from app.models.item import EstadoItem


def test_crear_item_minimo(client, auth_headers):
    r = client.post("/items", json={"nombre": "Pañalera"}, headers=auth_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["nombre"] == "Pañalera"
    assert body["estado"] == "NECESITADO"
    assert body["gifter_name"] is None
    assert body["fotos"] == []


def test_crear_item_con_link(client, auth_headers):
    r = client.post(
        "/items",
        json={"nombre": "Cuna", "amazon_link": "https://amazon.com/dp/B0X"},
        headers=auth_headers,
    )
    assert r.status_code == 201


def test_crear_item_link_invalido(client, auth_headers):
    r = client.post(
        "/items",
        json={"nombre": "Cuna", "amazon_link": "no-es-url"},
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_crear_item_sin_nombre(client, auth_headers):
    assert client.post("/items", json={}, headers=auth_headers).status_code == 422


def test_items_requieren_auth(client, item):
    assert client.get("/items").status_code == 403
    assert client.post("/items", json={"nombre": "x"}).status_code == 403
    assert client.patch(f"/items/{item.id}", json={}).status_code == 403
    assert client.delete(f"/items/{item.id}").status_code == 403


def test_listar_items(client, auth_headers, item):
    r = client.get("/items", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_editar_item(client, auth_headers, item):
    r = client.patch(
        f"/items/{item.id}",
        json={"descripcion": "Madera clara"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["descripcion"] == "Madera clara"


def test_editar_item_inexistente(client, auth_headers):
    r = client.patch("/items/999", json={"nombre": "x"}, headers=auth_headers)
    assert r.status_code == 404


def test_adquirir_nosotros(client, auth_headers, item):
    r = client.patch(
        f"/items/{item.id}/adquirir",
        json={"origen": "NOSOTROS"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["estado"] == "ADQUIRIDO"
    assert body["origen_adquisicion"] == "NOSOTROS"
    assert body["gifter_name"] is None


def test_adquirir_regalo_manual(client, auth_headers, item):
    r = client.patch(
        f"/items/{item.id}/adquirir",
        json={"origen": "REGALO", "gifter_name": "Tía Rosa"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["gifter_name"] == "Tía Rosa"


def test_readquirir_da_409(client, auth_headers, item):
    client.patch(
        f"/items/{item.id}/adquirir",
        json={"origen": "NOSOTROS"},
        headers=auth_headers,
    )
    r = client.patch(
        f"/items/{item.id}/adquirir",
        json={"origen": "NOSOTROS"},
        headers=auth_headers,
    )
    assert r.status_code == 409


def test_adquirir_nosotros_sobre_reservado_da_409(
    client, auth_headers, item_reservado
):
    item, _ = item_reservado
    r = client.patch(
        f"/items/{item.id}/adquirir",
        json={"origen": "NOSOTROS"},
        headers=auth_headers,
    )
    assert r.status_code == 409


def test_adquirir_regalo_sobre_reservado_revela_nombre_real(
    client, auth_headers, item_reservado, db
):
    item, reserva = item_reservado
    r = client.patch(
        f"/items/{item.id}/adquirir",
        json={"origen": "REGALO", "gifter_name": "Impostor"},
        headers=auth_headers,
    )
    assert r.status_code == 200
    # El nombre viene de la reserva, no del body.
    assert r.json()["gifter_name"] == "Abuela Marta"
    db.refresh(reserva)
    assert reserva.revelado is True
    assert reserva.released_at is not None


def test_gifter_name_oculto_mientras_reservado(
    client, auth_headers, item_reservado
):
    item, _ = item_reservado
    r = client.get("/items", headers=auth_headers)
    listado = [x for x in r.json() if x["id"] == item.id][0]
    assert listado["estado"] == "RESERVADO"
    assert listado["gifter_name"] is None
    # El nombre no aparece en ningún byte de la respuesta admin.
    assert "Abuela Marta" not in r.text


def test_eliminar_item(client, auth_headers, item):
    assert (
        client.delete(f"/items/{item.id}", headers=auth_headers).status_code == 204
    )
    assert client.get("/items", headers=auth_headers).json() == []


def test_eliminar_item_reservado_da_409(client, auth_headers, item_reservado):
    item, _ = item_reservado
    r = client.delete(f"/items/{item.id}", headers=auth_headers)
    assert r.status_code == 409


def test_eliminar_item_borra_fotos_en_db(client, auth_headers, item, db):
    from app.models.item import FotoItem

    db.add(FotoItem(item_id=item.id, url="https://cdn.test/items/x.jpg", orden=0))
    db.commit()
    client.delete(f"/items/{item.id}", headers=auth_headers)
    assert db.query(FotoItem).filter(FotoItem.item_id == item.id).count() == 0
