from pydantic import BaseModel, Field


class CajaCreate(BaseModel):
    etiqueta: str = Field(min_length=1, max_length=100)
    descripcion: str | None = Field(default=None, max_length=500)


class CajaAsignar(BaseModel):
    caja_id: int | None = None
