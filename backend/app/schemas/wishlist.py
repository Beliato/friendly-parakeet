from pydantic import BaseModel, Field

from app.models.item import Prioridad, RangoPrecio
from app.schemas.item import FotoItemOut


class ConfigOut(BaseModel):
    nombre_app: str


class ConfigUpdate(BaseModel):
    nombre_app: str = Field(min_length=1, max_length=100)


class WishlistLinkOut(BaseModel):
    share_token: str


class ItemPublicoOut(BaseModel):
    """Vista de invitado: sin estado interno, sin origen, sin nombres —
    solo lo necesario para elegir qué regalar."""

    id: int
    nombre: str
    descripcion: str | None = None
    amazon_link: str | None = None
    cantidad: int
    disponibles: int
    prioridad: Prioridad
    rango_precio: RangoPrecio | None = None
    categoria: str | None = None
    fotos: list[FotoItemOut] = []


class WishlistPublicaOut(BaseModel):
    nombre_app: str
    items: list[ItemPublicoOut]


class ReservarRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    mensaje: str | None = Field(default=None, max_length=500)


class ReservarResponse(BaseModel):
    token_deshacer: str
    unidad: int


class ReservasCountOut(BaseModel):
    pendientes: int
