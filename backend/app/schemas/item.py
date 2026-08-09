from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.models.item import EstadoItem, OrigenAdquisicion


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


class ItemCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)
    descripcion: str | None = Field(default=None, max_length=1000)
    amazon_link: str | None = Field(default=None, max_length=2000)

    @field_validator("amazon_link")
    @classmethod
    def validar_link(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            HttpUrl(v)
            return v.strip()
        return None


class ItemUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=1, max_length=255)
    descripcion: str | None = Field(default=None, max_length=1000)
    amazon_link: str | None = Field(default=None, max_length=2000)

    @field_validator("amazon_link")
    @classmethod
    def validar_link(cls, v: str | None) -> str | None:
        if v is not None and v.strip():
            HttpUrl(v)
            return v.strip()
        return None


class ItemAdquirir(BaseModel):
    origen: OrigenAdquisicion
    gifter_name: str | None = Field(default=None, max_length=255)


class ItemOut(BaseModel):
    """Salida admin. gifter_name solo viaja cuando el item ya está ADQUIRIDO:
    mientras está RESERVADO el nombre vive en la tabla reservas y este schema
    nunca lo toca — garantía estructural de la sorpresa."""

    id: int
    nombre: str
    descripcion: str | None = None
    amazon_link: str | None = None
    estado: EstadoItem
    origen_adquisicion: OrigenAdquisicion | None = None
    gifter_name: str | None = None
    caja: CajaOut | None = None
    fotos: list[FotoItemOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
