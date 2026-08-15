from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.core.ratelimit import limiter
from app.models.admin import Admin
from app.models.item import EstadoItem, Item
from app.models.reserva import Reserva
from app.models.wishlist_config import WishlistConfig
from app.schemas.item import ItemOut
from app.schemas.wishlist import (
    ConfigOut,
    ConfigUpdate,
    ItemPublicoOut,
    ReservarRequest,
    ReservarResponse,
    ReservasCountOut,
    WishlistLinkOut,
    WishlistPublicaOut,
)

router = APIRouter(tags=["wishlist"])


def _get_config(db: Session) -> WishlistConfig:
    config = db.query(WishlistConfig).first()
    if not config:
        # La migración seed la crea; esto es solo red de seguridad.
        config = WishlistConfig()
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


# --- Config (nombre de la app) ---


@router.get("/config", response_model=ConfigOut)
@limiter.limit("30/minute")
def obtener_config(request: Request, db: Session = Depends(get_db)):
    return ConfigOut(nombre_app=_get_config(db).nombre_app)


@router.patch("/config", response_model=ConfigOut)
def actualizar_config(
    body: ConfigUpdate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    config = _get_config(db)
    config.nombre_app = body.nombre_app.strip()
    db.commit()
    return ConfigOut(nombre_app=config.nombre_app)


# --- Link compartible (admin) ---


@router.get("/wishlist/link", response_model=WishlistLinkOut)
def obtener_link(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    return WishlistLinkOut(share_token=_get_config(db).share_token)


# --- Contador de actividad (admin, sin nombres) ---


@router.get("/reservas/pendientes/count", response_model=ReservasCountOut)
def contar_reservas_pendientes(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    pendientes = db.query(Reserva).filter(Reserva.released_at.is_(None)).count()
    return ReservasCountOut(pendientes=pendientes)


# --- Liberar reserva (admin, sin revelar nombre) ---


@router.post("/items/{item_id}/liberar-reserva", response_model=ItemOut)
def liberar_reserva(
    item_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    item = (
        db.query(Item)
        .options(selectinload(Item.fotos), selectinload(Item.caja))
        .filter(Item.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    reserva = (
        db.query(Reserva)
        .filter(Reserva.item_id == item_id, Reserva.released_at.is_(None))
        .first()
    )
    if item.estado != EstadoItem.RESERVADO or not reserva:
        raise HTTPException(
            status_code=409, detail="El item no tiene una reserva activa"
        )
    # La reserva se descarta sin marcarse como revelada: el nombre del
    # reservante nunca sale de la tabla reservas.
    reserva.released_at = datetime.now(UTC)
    item.estado = EstadoItem.NECESITADO
    db.commit()
    db.refresh(item)
    return item


# --- Wishlist pública ---


def _get_config_por_token(share_token: str, db: Session) -> WishlistConfig:
    config = (
        db.query(WishlistConfig)
        .filter(WishlistConfig.share_token == share_token)
        .first()
    )
    if not config:
        raise HTTPException(status_code=404, detail="Wishlist no encontrada")
    return config


@router.get("/w/{share_token}", response_model=WishlistPublicaOut)
@limiter.limit("30/minute")
def ver_wishlist(request: Request, share_token: str, db: Session = Depends(get_db)):
    config = _get_config_por_token(share_token, db)
    items = (
        db.query(Item)
        .options(selectinload(Item.fotos))
        .filter(Item.estado == EstadoItem.NECESITADO)
        .order_by(Item.created_at.desc())
        .all()
    )
    return WishlistPublicaOut(
        nombre_app=config.nombre_app,
        items=[ItemPublicoOut.model_validate(i) for i in items],
    )


@router.post(
    "/w/{share_token}/items/{item_id}/reservar",
    response_model=ReservarResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
def reservar_item(
    request: Request,
    share_token: str,
    item_id: int,
    body: ReservarRequest,
    db: Session = Depends(get_db),
):
    _get_config_por_token(share_token, db)
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    if item.estado != EstadoItem.NECESITADO:
        raise HTTPException(status_code=409, detail="El item ya no está disponible")
    reserva = Reserva(item_id=item_id, nombre_reservante=body.nombre.strip())
    item.estado = EstadoItem.RESERVADO
    db.add(reserva)
    try:
        db.commit()
    except IntegrityError as e:
        # Índice único parcial: otro invitado reservó en simultáneo.
        db.rollback()
        raise HTTPException(
            status_code=409, detail="El item ya no está disponible"
        ) from e
    return ReservarResponse(token_deshacer=reserva.token_deshacer)


@router.post("/w/reservas/{token_deshacer}/deshacer", response_model=ConfigOut)
@limiter.limit("10/minute")
def deshacer_reserva(
    request: Request, token_deshacer: str, db: Session = Depends(get_db)
):
    reserva = (
        db.query(Reserva)
        .filter(
            Reserva.token_deshacer == token_deshacer,
            Reserva.released_at.is_(None),
        )
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    item = db.query(Item).filter(Item.id == reserva.item_id).first()
    reserva.released_at = datetime.now(UTC)
    if item and item.estado == EstadoItem.RESERVADO:
        item.estado = EstadoItem.NECESITADO
    db.commit()
    return ConfigOut(nombre_app=_get_config(db).nombre_app)
