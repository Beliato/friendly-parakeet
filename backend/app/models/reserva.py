import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _nuevo_token() -> str:
    return str(uuid.uuid4())


class Reserva(Base):
    __tablename__ = "reservas"
    # Una reserva activa por unidad del item: dos invitados pueden tomar
    # unidades distintas, pero nunca la misma. La capacidad total la
    # controla el lock de fila al reservar (ver routers/wishlist.py).
    __table_args__ = (
        Index(
            "uq_reservas_item_unidad",
            "item_id",
            "unidad",
            unique=True,
            postgresql_where="released_at IS NULL",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), index=True
    )
    unidad: Mapped[int] = mapped_column(Integer, default=1)
    nombre_reservante: Mapped[str] = mapped_column(String(255))
    mensaje: Mapped[str | None] = mapped_column(Text)
    token_deshacer: Mapped[str] = mapped_column(
        String(36), unique=True, default=_nuevo_token
    )
    revelado: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    item = relationship("Item")
