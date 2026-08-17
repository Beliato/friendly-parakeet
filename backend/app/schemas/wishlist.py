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


class RegaloPublicoOut(BaseModel):
    """Una entrada del muro de agradecimiento.

    Solo lleva lo que se agradece en público: qué fue y de parte de quién.
    Las notas privadas del regalador no salen.
    """

    id: int
    item: str
    persona: str
    foto: str | None = None


class WishlistPublicaOut(BaseModel):
    nombre_app: str
    items: list[ItemPublicoOut]
    recibidos: list[RegaloPublicoOut] = []


class ReservarRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    mensaje: str | None = Field(default=None, max_length=500)


class ReservarResponse(BaseModel):
    token_deshacer: str
    unidad: int


class ReservasCountOut(BaseModel):
    pendientes: int


class ReservaPendienteOut(BaseModel):
    """Una reserva en camino, vista por el admin.

    Lleva el nombre del objeto para poder identificarlo cuando llega, pero
    nunca el de quien reservó: eso es la sorpresa.
    """

    id: int
    item_id: int
    item_nombre: str
    unidad: int
    total_unidades: int
    dias_desde_reserva: int
