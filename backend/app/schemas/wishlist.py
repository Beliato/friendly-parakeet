from pydantic import BaseModel, Field

from app.schemas.item import FotoItemOut


class ConfigOut(BaseModel):
    nombre_app: str


class ConfigUpdate(BaseModel):
    nombre_app: str = Field(min_length=1, max_length=100)


class WishlistLinkOut(BaseModel):
    share_token: str


class ItemPublicoOut(BaseModel):
    """Vista de invitado: sin estado, sin origen, sin nombres — solo lo
    necesario para elegir qué regalar."""

    id: int
    nombre: str
    descripcion: str | None = None
    amazon_link: str | None = None
    fotos: list[FotoItemOut] = []

    class Config:
        from_attributes = True


class WishlistPublicaOut(BaseModel):
    nombre_app: str
    items: list[ItemPublicoOut]


class ReservarRequest(BaseModel):
    nombre: str = Field(min_length=1, max_length=255)


class ReservarResponse(BaseModel):
    token_deshacer: str


class ReservasCountOut(BaseModel):
    pendientes: int
