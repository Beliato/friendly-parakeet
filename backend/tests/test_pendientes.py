"""El listado de lo que está en camino: hay que poder identificar el
objeto sin que se filtre quién lo reservó."""

TOKEN = "11111111-1111-1111-1111-111111111111"


def test_lista_vacia_al_principio(client, auth_headers):
    assert client.get("/reservas/pendientes", headers=auth_headers).json() == []


def test_incluye_el_nombre_del_objeto(client, auth_headers, config, item):
    client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Prima"})
    r = client.get("/reservas/pendientes", headers=auth_headers)
    assert r.status_code == 200
    pendiente = r.json()[0]
    assert pendiente["item_nombre"] == item.nombre
    assert pendiente["item_id"] == item.id
    assert pendiente["total_unidades"] == 1


def test_nunca_expone_el_nombre_de_quien_reservo(client, auth_headers, config, item):
    client.post(
        f"/w/{TOKEN}/items/{item.id}/reservar",
        json={"nombre": "Prima Sofía", "mensaje": "un secreto"},
    )
    r = client.get("/reservas/pendientes", headers=auth_headers)
    assert "Sofía" not in r.text
    assert "secreto" not in r.text


def test_junta_reservas_de_varios_items(client, auth_headers, config, item, db):
    from app.models.item import Item

    otro = Item(nombre="Coche paseador")
    db.add(otro)
    db.commit()
    client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Ana"})
    client.post(f"/w/{TOKEN}/items/{otro.id}/reservar", json={"nombre": "Beto"})

    nombres = [
        p["item_nombre"]
        for p in client.get("/reservas/pendientes", headers=auth_headers).json()
    ]
    assert sorted(nombres) == sorted([item.nombre, "Coche paseador"])


def test_una_reserva_recibida_sale_de_la_lista(client, auth_headers, config, item):
    client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Ana"})
    pendientes = client.get("/reservas/pendientes", headers=auth_headers).json()
    client.post(
        f"/items/{item.id}/reservas/{pendientes[0]['id']}/recibir",
        headers=auth_headers,
    )
    assert client.get("/reservas/pendientes", headers=auth_headers).json() == []


def test_una_reserva_liberada_sale_de_la_lista(client, auth_headers, config, item):
    client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Ana"})
    pendientes = client.get("/reservas/pendientes", headers=auth_headers).json()
    client.post(
        f"/items/{item.id}/reservas/{pendientes[0]['id']}/liberar",
        headers=auth_headers,
    )
    assert client.get("/reservas/pendientes", headers=auth_headers).json() == []


def test_requiere_auth(client):
    assert client.get("/reservas/pendientes").status_code == 403
