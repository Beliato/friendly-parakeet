import pytest

from app.models.item import Item


@pytest.fixture
def items_por_etapa(db, caja):
    db.add(Item(nombre="Body recién nacido", etapa="RECIEN_NACIDO", caja_id=caja.id))
    db.add(Item(nombre="Zapatitos 3-6", etapa="M3_6"))
    db.add(Item(nombre="Termómetro", descripcion="Digital", caja_id=caja.id))
    db.commit()


def test_etapa_por_defecto_es_cualquiera(client, auth_headers):
    r = client.post("/items", json={"nombre": "Cuna"}, headers=auth_headers)
    assert r.json()["etapa"] == "CUALQUIERA"


def test_crear_con_etapa(client, auth_headers):
    r = client.post(
        "/items", json={"nombre": "Body", "etapa": "M0_3"}, headers=auth_headers
    )
    assert r.status_code == 201
    assert r.json()["etapa"] == "M0_3"


def test_etapa_invalida_da_422(client, auth_headers):
    r = client.post(
        "/items", json={"nombre": "X", "etapa": "ADOLESCENTE"}, headers=auth_headers
    )
    assert r.status_code == 422


def test_editar_etapa(client, auth_headers, item):
    r = client.patch(f"/items/{item.id}", json={"etapa": "A1_2"}, headers=auth_headers)
    assert r.json()["etapa"] == "A1_2"


def test_filtrar_catalogo_por_etapa(client, auth_headers, items_por_etapa):
    r = client.get("/items?etapa=RECIEN_NACIDO", headers=auth_headers)
    assert [i["nombre"] for i in r.json()] == ["Body recién nacido"]


def test_filtrar_catalogo_por_estado(client, auth_headers, items_por_etapa):
    r = client.get("/items?estado=NECESITADO", headers=auth_headers)
    assert len(r.json()) == 3
    assert client.get("/items?estado=ADQUIRIDO", headers=auth_headers).json() == []


# --- Búsqueda ampliada ---


def test_busqueda_devuelve_caja_y_etapa(client, auth_headers, items_por_etapa):
    r = client.get("/items/buscar?q=termometro", headers=auth_headers)
    resultado = r.json()[0]
    assert resultado["caja"]["etiqueta"] == "Caja A"
    assert resultado["etapa"] == "CUALQUIERA"


def test_busqueda_devuelve_quien_lo_regalo(client, auth_headers, items_por_etapa, db):
    item = db.query(Item).filter(Item.nombre == "Termómetro").one()
    client.post(
        "/regalos",
        json={"item_id": item.id, "persona": "Abuela Carmen"},
        headers=auth_headers,
    )
    r = client.get("/items/buscar?q=termo", headers=auth_headers)
    assert r.json()[0]["personas"] == ["Abuela Carmen"]


def test_busqueda_filtra_por_etapa(client, auth_headers, items_por_etapa):
    con_filtro = client.get("/items/buscar?q=o&etapa=M3_6", headers=auth_headers).json()
    assert [i["nombre"] for i in con_filtro] == ["Zapatitos 3-6"]


def test_personas_no_repite_nombres(client, auth_headers, item, db):
    for _ in range(2):
        client.post(
            "/regalos",
            json={"item_id": item.id, "persona": "Ana"},
            headers=auth_headers,
        )
    r = client.get("/items", headers=auth_headers)
    assert r.json()[0]["personas"] == ["Ana"]


def test_compra_propia_no_aporta_persona(client, auth_headers, item):
    client.post(
        "/regalos",
        json={"item_id": item.id, "origen": "NOSOTROS"},
        headers=auth_headers,
    )
    r = client.get("/items", headers=auth_headers)
    assert r.json()[0]["personas"] == []
    assert r.json()[0]["origen_adquisicion"] == "NOSOTROS"
