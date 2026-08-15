"""Reglas compartidas de items y sus unidades."""

from sqlalchemy.orm import Session

from app.models.item import EstadoItem, Item
from app.models.reserva import Reserva


def reservas_activas(db: Session, item_id: int) -> list[Reserva]:
    return (
        db.query(Reserva)
        .filter(Reserva.item_id == item_id, Reserva.released_at.is_(None))
        .order_by(Reserva.created_at)
        .all()
    )


def contar_reservas_activas(db: Session, item_id: int) -> int:
    return (
        db.query(Reserva)
        .filter(Reserva.item_id == item_id, Reserva.released_at.is_(None))
        .count()
    )


def unidades_disponibles(db: Session, item: Item) -> int:
    """Cuántas unidades quedan sin recibir ni reservar."""
    comprometidas = item.cantidad_recibida + contar_reservas_activas(db, item.id)
    return max(item.cantidad - comprometidas, 0)


def primera_unidad_libre(db: Session, item_id: int) -> int:
    """Menor número de unidad no tomado por una reserva activa.

    Los números de unidades ya recibidas se reciclan: la capacidad total la
    controla unidades_disponibles(), no este número.
    """
    tomadas = {r.unidad for r in reservas_activas(db, item_id)}
    unidad = 1
    while unidad in tomadas:
        unidad += 1
    return unidad


def recalcular_estado(db: Session, item: Item) -> None:
    """Deriva el estado del item de sus cantidades y reservas activas."""
    if item.cantidad_recibida >= item.cantidad:
        item.estado = EstadoItem.ADQUIRIDO
    elif unidades_disponibles(db, item) == 0:
        item.estado = EstadoItem.RESERVADO
    else:
        item.estado = EstadoItem.NECESITADO
