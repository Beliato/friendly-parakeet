import pytest
from sqlalchemy.exc import IntegrityError

from app.models.item import EstadoItem
from app.models.reserva import Reserva

TOKEN = "11111111-1111-1111-1111-111111111111"


def test_reservar_item(client, config, item):
    r = client.post(
        f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Primo Juan"}
    )
    assert r.status_code == 201
    assert len(r.json()["token_deshacer"]) == 36


def test_reservar_quita_de_la_lista_publica(client, config, item):
    client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Ana"})
    w = client.get(f"/w/{TOKEN}").json()
    assert all(x["id"] != item.id for x in w["items"])


def test_doble_reserva_da_409(client, config, item):
    client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Ana"})
    r = client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Beto"})
    assert r.status_code == 409


def test_indice_parcial_bloquea_doble_reserva_activa(db, item):
    # Directo contra la DB, saltándose la validación de estado del endpoint:
    # el índice único parcial es la última línea de defensa.
    db.add(Reserva(item_id=item.id, nombre_reservante="A", token_deshacer="t1"))
    db.commit()
    db.add(Reserva(item_id=item.id, nombre_reservante="B", token_deshacer="t2"))
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_reserva_liberada_permite_nueva_reserva(client, config, item):
    r1 = client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Ana"})
    client.post(f"/w/reservas/{r1.json()['token_deshacer']}/deshacer")
    r2 = client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Beto"})
    assert r2.status_code == 201


def test_reservar_item_inexistente(client, config):
    r = client.post(f"/w/{TOKEN}/items/999/reservar", json={"nombre": "Ana"})
    assert r.status_code == 404


def test_reservar_con_share_token_invalido(client, config, item):
    r = client.post(f"/w/token-falso/items/{item.id}/reservar", json={"nombre": "Ana"})
    assert r.status_code == 404


def test_deshacer_reserva(client, config, item, db):
    r = client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Ana"})
    undo = r.json()["token_deshacer"]
    assert client.post(f"/w/reservas/{undo}/deshacer").status_code == 200
    db.refresh(item)
    assert item.estado == EstadoItem.NECESITADO
    w = client.get(f"/w/{TOKEN}").json()
    assert any(x["id"] == item.id for x in w["items"])


def test_deshacer_token_gastado_da_404(client, config, item):
    r = client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Ana"})
    undo = r.json()["token_deshacer"]
    client.post(f"/w/reservas/{undo}/deshacer")
    assert client.post(f"/w/reservas/{undo}/deshacer").status_code == 404


def test_deshacer_token_invalido_da_404(client, config):
    assert client.post("/w/reservas/token-falso/deshacer").status_code == 404


def test_liberar_reserva_admin_no_expone_nombre(
    client, auth_headers, item_reservado, db
):
    item, reserva = item_reservado
    r = client.post(f"/items/{item.id}/liberar-reserva", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["estado"] == "NECESITADO"
    assert "Abuela Marta" not in r.text
    db.refresh(reserva)
    assert reserva.released_at is not None
    assert reserva.revelado is False


def test_liberar_sin_reserva_activa_da_409(client, auth_headers, item):
    r = client.post(f"/items/{item.id}/liberar-reserva", headers=auth_headers)
    assert r.status_code == 409


def test_liberar_requiere_auth(client, item_reservado):
    item, _ = item_reservado
    assert client.post(f"/items/{item.id}/liberar-reserva").status_code == 403


def test_contador_pendientes(client, auth_headers, config, item, db):
    from app.models.item import Item

    otro = Item(nombre="Silla")
    db.add(otro)
    db.commit()
    client.post(f"/w/{TOKEN}/items/{item.id}/reservar", json={"nombre": "Ana"})
    client.post(f"/w/{TOKEN}/items/{otro.id}/reservar", json={"nombre": "Beto"})
    r = client.get("/reservas/pendientes/count", headers=auth_headers)
    assert r.json() == {"pendientes": 2}
    assert "Ana" not in r.text and "Beto" not in r.text


def test_contador_requiere_auth(client):
    assert client.get("/reservas/pendientes/count").status_code == 403
