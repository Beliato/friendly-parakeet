import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


def _nuevo_token() -> str:
    return str(uuid.uuid4())


class Reserva(Base):
    __tablename__ = "reservas"
    # Solo una reserva activa (no liberada) por item — evita que dos invitados
    # reserven el mismo item en simultáneo.
    __table_args__ = (
        Index(
            "uq_reservas_item_activa",
            "item_id",
            unique=True,
            postgresql_where="released_at IS NULL",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("items.id", ondelete="CASCADE"), index=True
    )
    nombre_reservante: Mapped[str] = mapped_column(String(255))
    token_deshacer: Mapped[str] = mapped_column(
        String(36), unique=True, default=_nuevo_token
    )
    revelado: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    released_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    item = relationship("Item")
