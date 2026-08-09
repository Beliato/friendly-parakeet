from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.core import storage_r2
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import Admin
from app.models.item import EstadoItem, Item, OrigenAdquisicion
from app.models.reserva import Reserva
from app.schemas.item import ItemAdquirir, ItemCreate, ItemOut, ItemUpdate

router = APIRouter(prefix="/items", tags=["items"])


def _get_item_or_404(item_id: int, db: Session) -> Item:
    item = (
        db.query(Item)
        .options(selectinload(Item.fotos), selectinload(Item.caja))
        .filter(Item.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return item


def _reserva_activa(item_id: int, db: Session) -> Reserva | None:
    return (
        db.query(Reserva)
        .filter(Reserva.item_id == item_id, Reserva.released_at.is_(None))
        .first()
    )


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def crear_item(
    body: ItemCreate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    item = Item(
        nombre=body.nombre,
        descripcion=body.descripcion,
        amazon_link=body.amazon_link,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[ItemOut])
def listar_items(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    return (
        db.query(Item)
        .options(selectinload(Item.fotos), selectinload(Item.caja))
        .order_by(Item.created_at.desc())
        .all()
    )


@router.patch("/{item_id}", response_model=ItemOut)
def editar_item(
    item_id: int,
    body: ItemUpdate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    item = _get_item_or_404(item_id, db)
    cambios = body.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(item, campo, valor)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/{item_id}/adquirir", response_model=ItemOut)
def adquirir_item(
    item_id: int,
    body: ItemAdquirir,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    item = _get_item_or_404(item_id, db)

    if item.estado == EstadoItem.ADQUIRIDO:
        raise HTTPException(status_code=409, detail="El item ya está adquirido")

    if item.estado == EstadoItem.RESERVADO:
        if body.origen == OrigenAdquisicion.NOSOTROS:
            raise HTTPException(
                status_code=409,
                detail=(
                    "El item está reservado. Libera la reserva primero "
                    "para adquirirlo por cuenta propia."
                ),
            )
        # Regalo recibido: revelar el nombre desde la reserva, ignorando
        # cualquier gifter_name del body.
        reserva = _reserva_activa(item_id, db)
        if not reserva:
            raise HTTPException(
                status_code=409,
                detail="Estado inconsistente: item reservado sin reserva activa",
            )
        item.gifter_name = reserva.nombre_reservante
        reserva.revelado = True
        reserva.released_at = datetime.now(timezone.utc)
    else:
        # NECESITADO: carga manual, sin sorpresa que preservar.
        item.gifter_name = (
            body.gifter_name if body.origen == OrigenAdquisicion.REGALO else None
        )

    item.estado = EstadoItem.ADQUIRIDO
    item.origen_adquisicion = body.origen
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    item = _get_item_or_404(item_id, db)
    if item.estado == EstadoItem.RESERVADO:
        raise HTTPException(
            status_code=409,
            detail=(
                "El item está reservado. Libera la reserva primero "
                "para poder eliminarlo."
            ),
        )
    # Las fotos en DB caen por cascade; los objetos en R2 se borran aquí.
    if storage_r2.esta_configurado():
        for foto in item.fotos:
            key = storage_r2.key_desde_url(foto.url)
            if key:
                storage_r2.borrar_objeto(key)
    db.delete(item)
    db.commit()
