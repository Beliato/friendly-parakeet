import pytest

from app.models.item import Item
from app.models.regalo import Regalo

TOKEN = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def item_multiple(db) -> Item:
    i = Item(nombre="Bodies 0-3m", cantidad=3)
    db.add(i)
    db.commit()
    return i


# --- Registrar ---


def test_registrar_sobre_item_existente(client, auth_headers, item):
    r = client.post(
        "/regalos",
        json={"item_id": item.id, "persona": "Tía Rosa"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    body = r.json()
    assert body["persona"] == "Tía Rosa"
    assert body["item"]["nombre"] == item.nombre
    assert body["agradecido"] is False


def test_registrar_crea_el_item_al_vuelo(client, auth_headers, db):
    r = client.post(
        "/regalos",
        json={
            "item_nuevo": {"nombre": "Manta de apego", "etapa": "RECIEN_NACIDO"},
            "persona": "Vecina Marta",
        },
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["item"]["nombre"] == "Manta de apego"
    assert r.json()["item"]["etapa"] == "RECIEN_NACIDO"
    # El objeto quedó en el catálogo y ya figura como recibido.
    creado = db.query(Item).filter(Item.nombre == "Manta de apego").first()
    assert creado is not None
    assert creado.cantidad_recibida == 1
    assert creado.estado.value == "ADQUIRIDO"


def test_registrar_sin_item_ni_item_nuevo_da_422(client, auth_headers):
    r = client.post("/regalos", json={"persona": "Ana"}, headers=auth_headers)
    assert r.status_code == 422


def test_registrar_con_los_dos_da_422(client, auth_headers, item):
    r = client.post(
        "/regalos",
        json={
            "item_id": item.id,
            "item_nuevo": {"nombre": "Otro"},
            "persona": "Ana",
        },
        headers=auth_headers,
    )
    assert r.status_code == 422


def test_regalo_sin_persona_da_422(client, auth_headers, item):
    r = client.post("/regalos", json={"item_id": item.id}, headers=auth_headers)
    assert r.status_code == 422


def test_compra_propia_no_necesita_persona(client, auth_headers, item):
    r = client.post(
        "/regalos",
        json={"item_id": item.id, "origen": "NOSOTROS"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["persona"] == ""


def test_registrar_varias_unidades(client, auth_headers, item_multiple, db):
    r = client.post(
        "/regalos",
        json={"item_id": item_multiple.id, "persona": "Ana", "cantidad": 2},
        headers=auth_headers,
    )
    assert r.status_code == 201
    db.refresh(item_multiple)
    assert item_multiple.cantidad_recibida == 2
    assert item_multiple.estado.value == "NECESITADO"


def test_item_inexistente_da_404(client, auth_headers):
    r = client.post(
        "/regalos", json={"item_id": 999, "persona": "Ana"}, headers=auth_headers
    )
    assert r.status_code == 404


def test_regalos_requieren_auth(client, item):
    assert client.get("/regalos").status_code == 403
    assert client.post("/regalos", json={"item_id": item.id}).status_code == 403


# --- cantidad_recibida derivada ---


def test_cantidad_recibida_suma_los_regalos(client, auth_headers, item_multiple, db):
    for persona in ("Ana", "Beto"):
        client.post(
            "/regalos",
            json={"item_id": item_multiple.id, "persona": persona},
            headers=auth_headers,
        )
    db.refresh(item_multiple)
    assert item_multiple.cantidad_recibida == 2


def test_borrar_regalo_devuelve_el_item_al_estado_anterior(
    client, auth_headers, item, db
):
    r = client.post(
        "/regalos", json={"item_id": item.id, "persona": "Ana"}, headers=auth_headers
    )
    db.refresh(item)
    assert item.estado.value == "ADQUIRIDO"

    assert (
        client.delete(f"/regalos/{r.json()['id']}", headers=auth_headers).status_code
        == 204
    )
    db.refresh(item)
    assert item.cantidad_recibida == 0
    assert item.estado.value == "NECESITADO"


def test_editar_cantidad_recalcula(client, auth_headers, item_multiple, db):
    r = client.post(
        "/regalos",
        json={"item_id": item_multiple.id, "persona": "Ana"},
        headers=auth_headers,
    )
    client.patch(
        f"/regalos/{r.json()['id']}", json={"cantidad": 3}, headers=auth_headers
    )
    db.refresh(item_multiple)
    assert item_multiple.cantidad_recibida == 3
    assert item_multiple.estado.value == "ADQUIRIDO"


# --- Personas y agradecimientos ---


def test_autocompletado_de_personas(client, auth_headers, item, item_multiple):
    client.post(
        "/regalos", json={"item_id": item.id, "persona": "Ana"}, headers=auth_headers
    )
    client.post(
        "/regalos",
        json={"item_id": item_multiple.id, "persona": "Beto"},
        headers=auth_headers,
    )
    # Las compras propias no aportan nombre.
    client.post(
        "/regalos",
        json={"item_id": item_multiple.id, "origen": "NOSOTROS"},
        headers=auth_headers,
    )
    r = client.get("/regalos/personas", headers=auth_headers)
    assert r.json() == ["Ana", "Beto"]


def test_autocompletado_filtra_por_texto(client, auth_headers, item):
    client.post(
        "/regalos",
        json={"item_id": item.id, "persona": "Abuela Marta"},
        headers=auth_headers,
    )
    assert client.get("/regalos/personas?q=abue", headers=auth_headers).json() == [
        "Abuela Marta"
    ]
    assert client.get("/regalos/personas?q=zzz", headers=auth_headers).json() == []


def test_agrupado_por_persona(client, auth_headers, item, item_multiple):
    client.post(
        "/regalos", json={"item_id": item.id, "persona": "Ana"}, headers=auth_headers
    )
    r2 = client.post(
        "/regalos",
        json={"item_id": item_multiple.id, "persona": "Ana"},
        headers=auth_headers,
    )
    client.patch(
        f"/regalos/{r2.json()['id']}", json={"agradecido": True}, headers=auth_headers
    )

    grupos = client.get("/regalos/por-persona", headers=auth_headers).json()
    assert len(grupos) == 1
    assert grupos[0]["persona"] == "Ana"
    assert grupos[0]["total_regalos"] == 2
    assert grupos[0]["pendientes_de_agradecer"] == 1


def test_marcar_agradecido(client, auth_headers, item):
    r = client.post(
        "/regalos", json={"item_id": item.id, "persona": "Ana"}, headers=auth_headers
    )
    edit = client.patch(
        f"/regalos/{r.json()['id']}", json={"agradecido": True}, headers=auth_headers
    )
    assert edit.json()["agradecido"] is True


def test_filtrar_pendientes_de_agradecer(client, auth_headers, item, item_multiple):
    r1 = client.post(
        "/regalos", json={"item_id": item.id, "persona": "Ana"}, headers=auth_headers
    )
    client.post(
        "/regalos",
        json={"item_id": item_multiple.id, "persona": "Beto"},
        headers=auth_headers,
    )
    client.patch(
        f"/regalos/{r1.json()['id']}", json={"agradecido": True}, headers=auth_headers
    )
    pendientes = client.get("/regalos?agradecido=false", headers=auth_headers).json()
    assert [g["persona"] for g in pendientes] == ["Beto"]


def test_filtrar_por_persona(client, auth_headers, item, item_multiple):
    client.post(
        "/regalos", json={"item_id": item.id, "persona": "Ana"}, headers=auth_headers
    )
    client.post(
        "/regalos",
        json={"item_id": item_multiple.id, "persona": "Beto"},
        headers=auth_headers,
    )
    r = client.get("/regalos?persona=Ana", headers=auth_headers)
    assert len(r.json()) == 1


def test_quitar_el_nombre_de_un_regalo_da_422(client, auth_headers, item):
    r = client.post(
        "/regalos", json={"item_id": item.id, "persona": "Ana"}, headers=auth_headers
    )
    edit = client.patch(
        f"/regalos/{r.json()['id']}", json={"persona": "  "}, headers=auth_headers
    )
    assert edit.status_code == 422


# --- Integración con la wishlist ---


def test_recibir_una_reserva_crea_el_regalo(
    client, auth_headers, config, item_multiple, db
):
    client.post(
        f"/w/{TOKEN}/items/{item_multiple.id}/reservar",
        json={"nombre": "Prima Sofía", "mensaje": "Con cariño"},
    )
    reservas = client.get(
        f"/items/{item_multiple.id}/reservas", headers=auth_headers
    ).json()
    client.post(
        f"/items/{item_multiple.id}/reservas/{reservas[0]['id']}/recibir",
        headers=auth_headers,
    )

    regalo = db.query(Regalo).filter(Regalo.item_id == item_multiple.id).one()
    assert regalo.persona == "Prima Sofía"
    assert regalo.nota == "Con cariño"
    assert regalo.reserva_id == reservas[0]["id"]


def test_la_reserva_pendiente_no_aparece_como_regalo(
    client, auth_headers, config, item_multiple, db
):
    client.post(
        f"/w/{TOKEN}/items/{item_multiple.id}/reservar", json={"nombre": "Prima Sofía"}
    )
    # Antes de recibirla no hay regalo, y el nombre no se filtra por ningún lado.
    assert db.query(Regalo).count() == 0
    assert "Sofía" not in client.get("/regalos", headers=auth_headers).text
    assert "Sofía" not in client.get("/regalos/personas", headers=auth_headers).text


def test_adquirir_crea_el_regalo(client, auth_headers, item_multiple, db):
    client.patch(
        f"/items/{item_multiple.id}/adquirir",
        json={"origen": "REGALO", "gifter_name": "Tía Rosa"},
        headers=auth_headers,
    )
    regalo = db.query(Regalo).filter(Regalo.item_id == item_multiple.id).one()
    assert regalo.persona == "Tía Rosa"
    # Cubre todas las unidades que faltaban.
    assert regalo.cantidad == 3
