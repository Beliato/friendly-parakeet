from datetime import date

from pydantic import BaseModel, Field, model_validator

from app.models.item import Etapa, Prioridad, RangoPrecio
from app.models.regalo import OrigenRegalo
from app.schemas.item import FotoItemOut


class ItemNuevo(BaseModel):
    """Datos mínimos para crear el objeto en el mismo paso que el regalo."""

    nombre: str = Field(min_length=1, max_length=255)
    descripcion: str | None = Field(default=None, max_length=1000)
    categoria_id: int | None = None
    etapa: Etapa = Etapa.CUALQUIERA
    prioridad: Prioridad = Prioridad.NORMAL
    rango_precio: RangoPrecio | None = None


class RegaloCreate(BaseModel):
    # Uno de los dos: el objeto ya existe, o se crea al vuelo.
    item_id: int | None = None
    item_nuevo: ItemNuevo | None = None
    persona: str = Field(default="", max_length=255)
    origen: OrigenRegalo = OrigenRegalo.REGALO
    cantidad: int = Field(default=1, ge=1, le=99)
    fecha: date | None = None
    nota: str | None = Field(default=None, max_length=1000)

    @model_validator(mode="after")
    def validar(self) -> "RegaloCreate":
        if (self.item_id is None) == (self.item_nuevo is None):
            raise ValueError("Indicá item_id o item_nuevo, pero no ambos")
        if self.origen == OrigenRegalo.REGALO and not self.persona.strip():
            raise ValueError("Un regalo necesita el nombre de quien lo regaló")
        return self


class RegaloUpdate(BaseModel):
    persona: str | None = Field(default=None, max_length=255)
    cantidad: int | None = Field(default=None, ge=1, le=99)
    fecha: date | None = None
    nota: str | None = Field(default=None, max_length=1000)
    agradecido: bool | None = None


class ItemDeRegaloOut(BaseModel):
    """Datos del objeto que acompañan al regalo, sin recursión."""

    id: int
    nombre: str
    etapa: Etapa
    fotos: list[FotoItemOut] = []

    class Config:
        from_attributes = True


class FotoRegaloOut(BaseModel):
    id: int
    url: str
    orden: int

    class Config:
        from_attributes = True


class RegaloOut(BaseModel):
    id: int
    item: ItemDeRegaloOut
    persona: str
    origen: OrigenRegalo
    cantidad: int
    fecha: date
    nota: str | None = None
    agradecido: bool
    fotos: list[FotoRegaloOut] = []

    class Config:
        from_attributes = True


class RegalosDePersonaOut(BaseModel):
    persona: str
    total_regalos: int
    pendientes_de_agradecer: int
    regalos: list[RegaloOut]
