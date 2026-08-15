"""Reglas compartidas de items y sus unidades."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.item import EstadoItem, Item, OrigenAdquisicion
from app.models.regalo import OrigenRegalo, Regalo
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


def recalcular_recibidas(db: Session, item: Item) -> None:
    """cantidad_recibida se deriva de los regalos registrados.

    Antes era un contador que se incrementaba a mano en varios lugares;
    ahora los regalos son la única fuente de verdad. También actualiza
    origen_adquisicion, que pasa a ser un resumen de esos regalos.
    """
    total = (
        db.query(func.coalesce(func.sum(Regalo.cantidad), 0))
        .filter(Regalo.item_id == item.id)
        .scalar()
    )
    item.cantidad_recibida = min(int(total), item.cantidad)

    if item.cantidad_recibida == 0:
        item.origen_adquisicion = None
    else:
        hubo_regalo = (
            db.query(Regalo)
            .filter(Regalo.item_id == item.id, Regalo.origen == OrigenRegalo.REGALO)
            .first()
            is not None
        )
        item.origen_adquisicion = (
            OrigenAdquisicion.REGALO if hubo_regalo else OrigenAdquisicion.NOSOTROS
        )


def recalcular_estado(db: Session, item: Item) -> None:
    """Deriva el estado del item de sus cantidades y reservas activas."""
    if item.cantidad_recibida >= item.cantidad:
        item.estado = EstadoItem.ADQUIRIDO
    elif unidades_disponibles(db, item) == 0:
        item.estado = EstadoItem.RESERVADO
    else:
        item.estado = EstadoItem.NECESITADO


def recalcular_item(db: Session, item: Item) -> None:
    """Recalcula cantidades y estado. Llamar tras tocar regalos o reservas."""
    db.flush()
    recalcular_recibidas(db, item)
    recalcular_estado(db, item)
