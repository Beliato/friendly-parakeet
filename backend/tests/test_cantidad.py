import pytest
from sqlalchemy.exc import IntegrityError

from app.models.item import EstadoItem, Item
from app.models.reserva import Reserva

TOKEN = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def item_multiple(db) -> Item:
    i = Item(nombre="Bodies 0-3m", cantidad=3)
    db.add(i)
    db.commit()
    return i


def test_crear_item_con_cantidad(client, auth_headers):
    r = client.post(
        "/items", json={"nombre": "Pañales", "cantidad": 4}, headers=auth_headers
    )
    assert r.status_code == 201
    assert r.json()["cantidad"] == 4
    assert r.json()["cantidad_recibida"] == 0


def test_cantidad_por_defecto_es_uno(client, auth_headers):
    r = client.post("/items", json={"nombre": "Cuna"}, headers=auth_headers)
    assert r.json()["cantidad"] == 1


def test_cantidad_cero_es_invalida(client, auth_headers):
    r = client.post("/items", json={"nombre": "X", "cantidad": 0}, headers=auth_headers)
    assert r.status_code == 422


def test_wishlist_muestra_disponibles(client, config, item_multiple):
    w = client.get(f"/w/{TOKEN}").json()
    publicado = [i for i in w["items"] if i["id"] == item_multiple.id][0]
    assert publicado["cantidad"] == 3
    assert publicado["disponibles"] == 3


def test_item_sigue_visible_con_reservas_parciales(client, config, item_multiple, db):
    client.post(f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": "Ana"})
    w = client.get(f"/w/{TOKEN}").json()
    publicado = [i for i in w["items"] if i["id"] == item_multiple.id][0]
    assert publicado["disponibles"] == 2
    db.refresh(item_multiple)
    assert item_multiple.estado == EstadoItem.NECESITADO


def test_item_desaparece_al_agotarse(client, config, item_multiple, db):
    for nombre in ("Ana", "Beto", "Caro"):
        r = client.post(
            f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": nombre}
        )
        assert r.status_code == 201
    w = client.get(f"/w/{TOKEN}").json()
    assert all(i["id"] != item_multiple.id for i in w["items"])
    db.refresh(item_multiple)
    assert item_multiple.estado == EstadoItem.RESERVADO


def test_no_se_puede_reservar_mas_que_la_cantidad(client, config, item_multiple):
    for nombre in ("Ana", "Beto", "Caro"):
        client.post(
            f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": nombre}
        )
    r = client.post(
        f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": "Dani"}
    )
    assert r.status_code == 409


def test_unidades_asignadas_son_distintas(client, config, item_multiple):
    unidades = {
        client.post(
            f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": n}
        ).json()["unidad"]
        for n in ("Ana", "Beto", "Caro")
    }
    assert unidades == {1, 2, 3}


def test_indice_impide_dos_reservas_de_la_misma_unidad(db, item_multiple):
    # Última línea de defensa a nivel de base, salteando el endpoint.
    db.add(
        Reserva(
            item_id=item_multiple.id,
            unidad=1,
            nombre_reservante="A",
            token_deshacer="t1",
        )
    )
    db.commit()
    db.add(
        Reserva(
            item_id=item_multiple.id,
            unidad=1,
            nombre_reservante="B",
            token_deshacer="t2",
        )
    )
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_recibir_una_unidad_no_completa_el_item(
    client, auth_headers, config, item_multiple, db
):
    client.post(f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": "Ana"})
    reservas = client.get(
        f"/items/{item_multiple.id}/reservas", headers=auth_headers
    ).json()
    r = client.post(
        f"/items/{item_multiple.id}/reservas/{reservas[0]['id']}/recibir",
        headers=auth_headers,
    )
    assert r.status_code == 200
    assert r.json()["item"]["cantidad_recibida"] == 1
    assert r.json()["item"]["estado"] == "NECESITADO"
    # Vuelve a estar disponible para los demás.
    w = client.get(f"/w/{TOKEN}").json()
    publicado = [i for i in w["items"] if i["id"] == item_multiple.id][0]
    assert publicado["disponibles"] == 2


def test_recibir_todas_las_unidades_completa_el_item(
    client, auth_headers, config, item_multiple
):
    for nombre in ("Ana", "Beto", "Caro"):
        client.post(
            f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": nombre}
        )
    reservas = client.get(
        f"/items/{item_multiple.id}/reservas", headers=auth_headers
    ).json()
    for reserva in reservas:
        r = client.post(
            f"/items/{item_multiple.id}/reservas/{reserva['id']}/recibir",
            headers=auth_headers,
        )
    assert r.json()["item"]["estado"] == "ADQUIRIDO"
    assert r.json()["item"]["cantidad_recibida"] == 3


def test_recibir_una_unidad_no_revela_las_otras(
    client, auth_headers, config, item_multiple
):
    for nombre in ("Ana", "Beto"):
        client.post(
            f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": nombre}
        )
    reservas = client.get(
        f"/items/{item_multiple.id}/reservas", headers=auth_headers
    ).json()
    r = client.post(
        f"/items/{item_multiple.id}/reservas/{reservas[0]['id']}/recibir",
        headers=auth_headers,
    )
    assert r.json()["nombre"] == "Ana"
    # La segunda reserva sigue oculta en el listado admin.
    listado = client.get("/items", headers=auth_headers)
    assert "Beto" not in listado.text


def test_bajar_cantidad_por_debajo_de_lo_comprometido_da_409(
    client, auth_headers, config, item_multiple
):
    for nombre in ("Ana", "Beto"):
        client.post(
            f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": nombre}
        )
    r = client.patch(
        f"/items/{item_multiple.id}", json={"cantidad": 1}, headers=auth_headers
    )
    assert r.status_code == 409


def test_subir_cantidad_reabre_disponibilidad(
    client, auth_headers, config, item_multiple
):
    for nombre in ("Ana", "Beto", "Caro"):
        client.post(
            f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": nombre}
        )
    r = client.patch(
        f"/items/{item_multiple.id}", json={"cantidad": 5}, headers=auth_headers
    )
    assert r.status_code == 200
    assert r.json()["estado"] == "NECESITADO"
    w = client.get(f"/w/{TOKEN}").json()
    publicado = [i for i in w["items"] if i["id"] == item_multiple.id][0]
    assert publicado["disponibles"] == 2


def test_mensaje_del_regalador_se_revela_con_el_nombre(
    client, auth_headers, config, item_multiple
):
    client.post(
        f"/w/{TOKEN}/items/{item_multiple.id}/reservar",
        json={"nombre": "Ana", "mensaje": "Con todo el cariño"},
    )
    reservas = client.get(
        f"/items/{item_multiple.id}/reservas", headers=auth_headers
    ).json()
    # Antes de recibir, el mensaje tampoco se ve.
    assert (
        "cariño"
        not in client.get(
            f"/items/{item_multiple.id}/reservas", headers=auth_headers
        ).text
    )
    r = client.post(
        f"/items/{item_multiple.id}/reservas/{reservas[0]['id']}/recibir",
        headers=auth_headers,
    )
    assert r.json()["mensaje"] == "Con todo el cariño"


def test_deshacer_libera_solo_esa_unidad(client, config, item_multiple):
    r1 = client.post(
        f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": "Ana"}
    )
    client.post(
        f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": "Beto"}
    )
    client.post(f"/w/reservas/{r1.json()['token_deshacer']}/deshacer")
    w = client.get(f"/w/{TOKEN}").json()
    publicado = [i for i in w["items"] if i["id"] == item_multiple.id][0]
    assert publicado["disponibles"] == 2


def test_eliminar_item_con_reservas_da_409(client, auth_headers, config, item_multiple):
    client.post(f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": "Ana"})
    r = client.delete(f"/items/{item_multiple.id}", headers=auth_headers)
    assert r.status_code == 409
