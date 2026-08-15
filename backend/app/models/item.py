import enum
from datetime import UTC, datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class EstadoItem(str, enum.Enum):
    NECESITADO = "NECESITADO"
    RESERVADO = "RESERVADO"
    ADQUIRIDO = "ADQUIRIDO"


class OrigenAdquisicion(str, enum.Enum):
    NOSOTROS = "NOSOTROS"
    REGALO = "REGALO"


class Prioridad(str, enum.Enum):
    URGENTE = "URGENTE"
    NORMAL = "NORMAL"
    PUEDE_ESPERAR = "PUEDE_ESPERAR"


class RangoPrecio(str, enum.Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        CheckConstraint("cantidad >= 1", name="ck_items_cantidad_positiva"),
        CheckConstraint(
            "cantidad_recibida >= 0 AND cantidad_recibida <= cantidad",
            name="ck_items_recibida_valida",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255))
    descripcion: Mapped[str | None] = mapped_column(String(1000))
    amazon_link: Mapped[str | None] = mapped_column(String(2000))
    cantidad: Mapped[int] = mapped_column(Integer, default=1)
    cantidad_recibida: Mapped[int] = mapped_column(Integer, default=0)
    prioridad: Mapped[Prioridad] = mapped_column(
        Enum(Prioridad), default=Prioridad.NORMAL
    )
    rango_precio: Mapped[RangoPrecio | None] = mapped_column(Enum(RangoPrecio))
    categoria_id: Mapped[int | None] = mapped_column(
        ForeignKey("categorias.id", ondelete="SET NULL")
    )
    # Derivado de cantidad/cantidad_recibida/reservas activas — ver
    # recalcular_estado(). Se persiste para poder filtrar e indexar.
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
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    caja = relationship("CajaAlmacenamiento")
    categoria = relationship("Categoria")
    fotos = relationship(
        "FotoItem",
        back_populates="item",
        cascade="all, delete-orphan",
        order_by="FotoItem.orden",
    )
    reservas = relationship(
        "Reserva", back_populates="item", cascade="all, delete-orphan"
    )

    @property
    def reservas_activas(self) -> int:
        """Cuántas unidades están reservadas. Solo el número: los nombres
        viven en Reserva y no salen de ahí hasta recibir cada unidad."""
        return sum(1 for r in self.reservas if r.released_at is None)


class FotoItem(Base):
    __tablename__ = "fotos_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(String(2000))
    orden: Mapped[int] = mapped_column(Integer, default=0)

    item = relationship("Item", back_populates="fotos")
