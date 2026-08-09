import enum
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EstadoItem(str, enum.Enum):
    NECESITADO = "NECESITADO"
    RESERVADO = "RESERVADO"
    ADQUIRIDO = "ADQUIRIDO"


class OrigenAdquisicion(str, enum.Enum):
    NOSOTROS = "NOSOTROS"
    REGALO = "REGALO"


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255))
    descripcion: Mapped[str | None] = mapped_column(String(1000))
    amazon_link: Mapped[str | None] = mapped_column(String(2000))
    estado: Mapped[EstadoItem] = mapped_column(
        Enum(EstadoItem), default=EstadoItem.NECESITADO, index=True
    )
    origen_adquisicion: Mapped[OrigenAdquisicion | None] = mapped_column(
        Enum(OrigenAdquisicion)
    )
    # Solo se popula al marcar adquirido. Mientras el item está RESERVADO, el
    # nombre vive únicamente en Reserva.nombre_reservante (sorpresa real).
    gifter_name: Mapped[str | None] = mapped_column(String(255))
    caja_id: Mapped[int | None] = mapped_column(
        ForeignKey("cajas_almacenamiento.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    caja = relationship("CajaAlmacenamiento")
    fotos = relationship(
        "FotoItem",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="FotoItem.orden",
    )


class FotoItem(Base):
    __tablename__ = "fotos_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(String(2000))
    orden: Mapped[int] = mapped_column(Integer, default=0)

    item = relationship("Item", back_populates="fotos")
