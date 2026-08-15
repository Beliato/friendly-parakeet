import pytest

from app.models.categoria import Categoria
from app.models.item import Item

TOKEN = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def categoria(db) -> Categoria:
    c = Categoria(nombre="Ropa")
    db.add(c)
    db.commit()
    return c


# --- Categorías ---


def test_crear_categoria(client, auth_headers):
    r = client.post("/categorias", json={"nombre": "Higiene"}, headers=auth_headers)
    assert r.status_code == 201
    assert r.json()["nombre"] == "Higiene"


def test_categoria_duplicada_da_409(client, auth_headers, categoria):
    r = client.post("/categorias", json={"nombre": "Ropa"}, headers=auth_headers)
    assert r.status_code == 409


def test_listar_categorias(client, auth_headers, categoria):
    r = client.get("/categorias", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_categorias_requieren_auth(client, categoria):
    assert client.get("/categorias").status_code == 403
    assert client.post("/categorias", json={"nombre": "X"}).status_code == 403


def test_asignar_categoria_al_crear(client, auth_headers, categoria):
    r = client.post(
        "/items",
        json={"nombre": "Body", "categoria_id": categoria.id},
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["categoria"]["nombre"] == "Ropa"


def test_categoria_inexistente_da_404(client, auth_headers):
    r = client.post(
        "/items", json={"nombre": "Body", "categoria_id": 999}, headers=auth_headers
    )
    assert r.status_code == 404


def test_wishlist_expone_nombre_de_categoria(client, config, auth_headers, categoria):
    client.post(
        "/items",
        json={"nombre": "Body", "categoria_id": categoria.id},
        headers=auth_headers,
    )
    w = client.get(f"/w/{TOKEN}").json()
    assert w["items"][0]["categoria"] == "Ropa"


# --- Prioridad y precio ---


def test_prioridad_por_defecto_normal(client, auth_headers):
    r = client.post("/items", json={"nombre": "Cuna"}, headers=auth_headers)
    assert r.json()["prioridad"] == "NORMAL"


def test_crear_con_prioridad_y_precio(client, auth_headers):
    r = client.post(
        "/items",
        json={"nombre": "Cuna", "prioridad": "URGENTE", "rango_precio": "ALTO"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    assert r.json()["prioridad"] == "URGENTE"
    assert r.json()["rango_precio"] == "ALTO"


def test_prioridad_invalida_da_422(client, auth_headers):
    r = client.post(
        "/items", json={"nombre": "X", "prioridad": "SUPER"}, headers=auth_headers
    )
    assert r.status_code == 422


def test_wishlist_ordena_urgentes_primero(client, auth_headers, config, db):
    db.add(Item(nombre="Puede esperar", prioridad="PUEDE_ESPERAR"))
    db.add(Item(nombre="Normal"))
    db.add(Item(nombre="Urgente", prioridad="URGENTE"))
    db.commit()
    w = client.get(f"/w/{TOKEN}").json()
    nombres = [i["nombre"] for i in w["items"]]
    assert nombres.index("Urgente") < nombres.index("Normal")
    assert nombres.index("Normal") < nombres.index("Puede esperar")


def test_wishlist_expone_prioridad_y_precio(client, auth_headers, config):
    client.post(
        "/items",
        json={"nombre": "Cuna", "prioridad": "URGENTE", "rango_precio": "MEDIO"},
        headers=auth_headers,
    )
    publicado = client.get(f"/w/{TOKEN}").json()["items"][0]
    assert publicado["prioridad"] == "URGENTE"
    assert publicado["rango_precio"] == "MEDIO"


# --- Buscador ---


@pytest.fixture
def items_para_buscar(db, caja):
    db.add(Item(nombre="Termómetro digital", caja_id=caja.id, descripcion="Con funda"))
    db.add(Item(nombre="Chupetes", descripcion="Pack de tres"))
    db.commit()


def test_buscar_por_nombre(client, auth_headers, items_para_buscar):
    r = client.get("/items/buscar?q=termometro", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["nombre"] == "Termómetro digital"


def test_buscar_ignora_acentos_y_mayusculas(client, auth_headers, items_para_buscar):
    for q in ("TERMÓMETRO", "termometro", "TeRmOmEtRo"):
        r = client.get(f"/items/buscar?q={q}", headers=auth_headers)
        assert len(r.json()) == 1, q


def test_buscar_devuelve_la_caja(client, auth_headers, items_para_buscar):
    r = client.get("/items/buscar?q=termo", headers=auth_headers)
    assert r.json()[0]["caja"]["etiqueta"] == "Caja A"


def test_buscar_por_descripcion(client, auth_headers, items_para_buscar):
    r = client.get("/items/buscar?q=funda", headers=auth_headers)
    assert len(r.json()) == 1


def test_buscar_sin_resultados(client, auth_headers, items_para_buscar):
    assert client.get("/items/buscar?q=zzzz", headers=auth_headers).json() == []


def test_buscar_requiere_auth(client, items_para_buscar):
    assert client.get("/items/buscar?q=termo").status_code == 403


def test_buscar_query_vacia_da_422(client, auth_headers):
    assert client.get("/items/buscar?q=", headers=auth_headers).status_code == 422
