from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.models.item import (
    EstadoItem,
    Etapa,
    OrigenAdquisicion,
    Prioridad,
    RangoPrecio,
)


class FotoItemOut(BaseModel):
    id: int
    url: str
    orden: int

    class Config:
        from_attributes = True


class CajaOut(BaseModel):
    id: int
    etiqueta: str
    descripcion: str | None = None

    class Config:
        from_attributes = True


class CategoriaOut(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True


def _validar_link(v: str | None) -> str | None:
    if v is not None and v.strip():
        HttpUrl(v)
        return v.strip()
    return None


class ItemCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    descripcion: str | None = Field(default=None, max_length=1000)
    amazon_link: str | None = Field(default=None, max_length=2000)
    cantidad: int = Field(default=1, ge=1, le=99)
    prioridad: Prioridad = Prioridad.NORMAL
    rango_precio: RangoPrecio | None = None
    categoria_id: int | None = None
    etapa: Etapa = Etapa.CUALQUIERA

    @field_validator("amazon_link")
    @classmethod
    def validar_link(cls, v: str | None) -> str | None:
        return _validar_link(v)


class ItemUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    descripcion: str | None = Field(default=None, max_length=1000)
    amazon_link: str | None = Field(default=None, max_length=2000)
    cantidad: int | None = Field(default=None, ge=1, le=99)
    prioridad: Prioridad | None = None
    rango_precio: RangoPrecio | None = None
    categoria_id: int | None = None
    etapa: Etapa | None = None

    @field_validator("amazon_link")
    @classmethod
    def validar_link(cls, v: str | None) -> str | None:
        return _validar_link(v)


class ItemAdquirir(BaseModel):
    origen: OrigenAdquisicion
    gifter_name: str | None = Field(default=None, max_length=255)


class ItemOut(BaseModel):
    """Salida admin. `personas` lista solo a quienes ya fueron revelados
    (vienen de los regalos registrados); las reservas activas viven en la
    tabla reservas y este schema nunca las toca — garantía estructural de
    la sorpresa."""

    id: int
    nombre: str
    descripcion: str | None = None
    amazon_link: str | None = None
    cantidad: int
    cantidad_recibida: int
    # Cuántas unidades hay reservadas ahora. Es solo un número: los nombres
    # siguen fuera de este schema.
    reservas_activas: int = 0
    prioridad: Prioridad
    rango_precio: RangoPrecio | None = None
    categoria: CategoriaOut | None = None
    etapa: Etapa
    estado: EstadoItem
    origen_adquisicion: OrigenAdquisicion | None = None
    personas: list[str] = []
    caja: CajaOut | None = None
    fotos: list[FotoItemOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemBusquedaOut(BaseModel):
    """Lo que hace falta para responder "¿dónde está y de quién vino?"."""

    id: int
    nombre: str
    descripcion: str | None = None
    estado: EstadoItem
    etapa: Etapa
    personas: list[str] = []
    caja: CajaOut | None = None

    class Config:
        from_attributes = True


class ReservaAdminOut(BaseModel):
    """Vista admin de una reserva activa: sin nombre ni mensaje."""

    id: int
    unidad: int
    dias_desde_reserva: int


class ReservaReveladaOut(BaseModel):
    """Se devuelve solo al marcar la unidad como recibida."""

    nombre: str
    mensaje: str | None = None
    item: ItemOut
