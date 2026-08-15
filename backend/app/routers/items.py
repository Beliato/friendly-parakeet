from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.core import storage_r2
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import Admin
from app.models.categoria import Categoria
from app.models.item import EstadoItem, Item, OrigenAdquisicion
from app.models.reserva import Reserva
from app.schemas.item import (
    ItemAdquirir,
    ItemBusquedaOut,
    ItemCreate,
    ItemOut,
    ItemUpdate,
    ReservaAdminOut,
    ReservaReveladaOut,
)
from app.services.items import (
    contar_reservas_activas,
    recalcular_estado,
    reservas_activas,
)

router = APIRouter(prefix="/items", tags=["items"])

_ACENTOS_DESDE = "áéíóúüñÁÉÍÓÚÜÑ"
_ACENTOS_HASTA = "aeiounnAEIOUNN"


def _cargado(query):
    return query.options(
        selectinload(Item.fotos),
        selectinload(Item.caja),
        selectinload(Item.categoria),
    )


def _get_item_or_404(item_id: int, db: Session) -> Item:
    item = _cargado(db.query(Item)).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return item


def _validar_categoria(db: Session, categoria_id: int | None) -> None:
    if categoria_id is None:
        return
    if not db.query(Categoria).filter(Categoria.id == categoria_id).first():
        raise HTTPException(status_code=404, detail="Categoría no encontrada")


@router.post("", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def crear_item(
    body: ItemCreate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    _validar_categoria(db, body.categoria_id)
    item = Item(**body.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[ItemOut])
def listar_items(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    return _cargado(db.query(Item)).order_by(Item.created_at.desc()).all()


@router.get("/buscar", response_model=list[ItemBusquedaOut])
def buscar_items(
    q: str = Query(min_length=1, max_length=100),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Busca por nombre y descripción, ignorando mayúsculas y acentos."""
    normalizado = q.strip().translate(str.maketrans(_ACENTOS_DESDE, _ACENTOS_HASTA))
    patron = f"%{normalizado.lower()}%"

    def sin_acentos(col):
        return func.translate(func.lower(col), _ACENTOS_DESDE, _ACENTOS_HASTA)

    return (
        db.query(Item)
        .options(selectinload(Item.caja))
        .filter(
            sin_acentos(Item.nombre).like(patron)
            | sin_acentos(func.coalesce(Item.descripcion, "")).like(patron)
        )
        .order_by(Item.nombre)
        .limit(50)
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

    if "categoria_id" in cambios:
        _validar_categoria(db, cambios["categoria_id"])

    if cambios.get("cantidad") is not None:
        comprometidas = item.cantidad_recibida + contar_reservas_activas(db, item.id)
        if cambios["cantidad"] < comprometidas:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Ya hay {comprometidas} unidades recibidas o reservadas: "
                    "no se puede bajar la cantidad por debajo de ese número."
                ),
            )

    for campo, valor in cambios.items():
        setattr(item, campo, valor)
    recalcular_estado(db, item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}/reservas", response_model=list[ReservaAdminOut])
def listar_reservas(
    item_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Reservas activas del item. Nunca incluye nombre ni mensaje: el admin
    solo ve cuántas hay y hace cuánto, para decidir si liberar alguna."""
    _get_item_or_404(item_id, db)
    ahora = datetime.now(UTC)
    return [
        ReservaAdminOut(
            id=r.id,
            unidad=r.unidad,
            dias_desde_reserva=(ahora - r.created_at).days,
        )
        for r in reservas_activas(db, item_id)
    ]


@router.post(
    "/{item_id}/reservas/{reserva_id}/recibir", response_model=ReservaReveladaOut
)
def recibir_unidad(
    item_id: int,
    reserva_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Marca recibida esa unidad y revela quién la regaló. Las otras
    reservas del mismo item siguen ocultas."""
    item = _get_item_or_404(item_id, db)
    reserva = (
        db.query(Reserva)
        .filter(
            Reserva.id == reserva_id,
            Reserva.item_id == item_id,
            Reserva.released_at.is_(None),
        )
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva activa no encontrada")

    reserva.revelado = True
    reserva.released_at = datetime.now(UTC)
    item.cantidad_recibida += 1
    item.origen_adquisicion = OrigenAdquisicion.REGALO
    # gifter_name acumula los nombres ya revelados del item.
    item.gifter_name = (
        f"{item.gifter_name}, {reserva.nombre_reservante}"
        if item.gifter_name
        else reserva.nombre_reservante
    )
    recalcular_estado(db, item)
    db.commit()
    db.refresh(item)
    return ReservaReveladaOut(
        nombre=reserva.nombre_reservante, mensaje=reserva.mensaje, item=item
    )


@router.post("/{item_id}/reservas/{reserva_id}/liberar", response_model=ItemOut)
def liberar_unidad(
    item_id: int,
    reserva_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Descarta la reserva sin revelar nada: la unidad vuelve a estar
    disponible y el nombre nunca sale de la tabla reservas."""
    item = _get_item_or_404(item_id, db)
    reserva = (
        db.query(Reserva)
        .filter(
            Reserva.id == reserva_id,
            Reserva.item_id == item_id,
            Reserva.released_at.is_(None),
        )
        .first()
    )
    if not reserva:
        raise HTTPException(status_code=404, detail="Reserva activa no encontrada")

    reserva.released_at = datetime.now(UTC)
    recalcular_estado(db, item)
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
    """Recibe todas las unidades que falten como compra propia o regalo
    cargado a mano. Si hay reservas activas hay que resolverlas primero."""
    item = _get_item_or_404(item_id, db)

    if item.estado == EstadoItem.ADQUIRIDO:
        raise HTTPException(status_code=409, detail="El item ya está adquirido")

    if contar_reservas_activas(db, item.id) > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "El item tiene unidades reservadas. Recibí o liberá esas "
                "reservas antes de marcarlo por tu cuenta."
            ),
        )

    item.cantidad_recibida = item.cantidad
    item.origen_adquisicion = body.origen
    item.gifter_name = (
        body.gifter_name if body.origen == OrigenAdquisicion.REGALO else None
    )
    recalcular_estado(db, item)
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
    if contar_reservas_activas(db, item.id) > 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "El item tiene unidades reservadas. Liberá esas reservas "
                "primero para poder eliminarlo."
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
