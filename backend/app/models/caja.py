from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CajaAlmacenamiento(Base):
    __tablename__ = "cajas_almacenamiento"

    id: Mapped[int] = mapped_column(primary_key=True)
    etiqueta: Mapped[str] = mapped_column(String(100), unique=True)
    descripcion: Mapped[str | None] = mapped_column(String(500))
