"""Fixtures compartidas — patrón savepoint rollback (heredado de FinTrack).

- engine (scope=session): crea el esquema una vez por sesión de pytest.
- db (scope=function): Session sobre SAVEPOINT; rollback al final de cada test.
- client (scope=function): TestClient con get_db sobreescrito.
El rate limiter se desactiva globalmente; el test que lo cubre lo re-activa.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, get_db
from app.core.ratelimit import limiter
from app.core.security import create_access_token, hash_password
from app.models.admin import Admin
from app.models.caja import CajaAlmacenamiento
from app.models.item import EstadoItem, Item
from app.models.reserva import Reserva
from app.models.wishlist_config import WishlistConfig
from main import app

TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://julia:julia123@localhost:5433/julia_test"
)


@pytest.fixture(scope="session")
def engine():
    _engine = create_engine(TEST_DB_URL, echo=False)
    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)
    _engine.dispose()


@pytest.fixture(scope="function")
def db(engine):
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(connection, join_transaction_mode="create_savepoint")

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        yield db

    limiter.enabled = False
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()
    limiter.enabled = True


@pytest.fixture
def admin(db) -> Admin:
    a = Admin(email="admin@test.com", password_hash=hash_password("clave-test-123"))
    db.add(a)
    db.commit()
    return a


@pytest.fixture
def auth_headers(admin) -> dict:
    token = create_access_token({"sub": str(admin.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def config(db) -> WishlistConfig:
    c = WishlistConfig(share_token="11111111-1111-1111-1111-111111111111")
    db.add(c)
    db.commit()
    return c


@pytest.fixture
def item(db) -> Item:
    i = Item(nombre="Cuna colecho")
    db.add(i)
    db.commit()
    return i


@pytest.fixture
def item_reservado(db, item) -> tuple[Item, Reserva]:
    reserva = Reserva(
        item_id=item.id,
        nombre_reservante="Abuela Marta",
        token_deshacer="22222222-2222-2222-2222-222222222222",
    )
    item.estado = EstadoItem.RESERVADO
    db.add(reserva)
    db.commit()
    return item, reserva


@pytest.fixture
def caja(db) -> CajaAlmacenamiento:
    c = CajaAlmacenamiento(etiqueta="Caja A", descripcion="Closet")
    db.add(c)
    db.commit()
    return c
