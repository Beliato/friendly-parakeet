from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.models.item import (
    EstadoItem,
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

    @field_validator("amazon_link")
    @classmethod
    def validar_link(cls, v: str | None) -> str | None:
        return _validar_link(v)


class ItemAdquirir(BaseModel):
    origen: OrigenAdquisicion
    gifter_name: str | None = Field(default=None, max_length=255)


class ItemOut(BaseModel):
    """Salida admin. gifter_name solo lleva los nombres ya revelados: las
    reservas activas viven en la tabla reservas y este schema nunca las
    toca — garantía estructural de la sorpresa."""

    id: int
    nombre: str
    descripcion: str | None = None
    amazon_link: str | None = None
    cantidad: int
    cantidad_recibida: int
    prioridad: Prioridad
    rango_precio: RangoPrecio | None = None
    categoria: CategoriaOut | None = None
    estado: EstadoItem
    origen_adquisicion: OrigenAdquisicion | None = None
    gifter_name: str | None = None
    caja: CajaOut | None = None
    fotos: list[FotoItemOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ItemBusquedaOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    estado: EstadoItem
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
