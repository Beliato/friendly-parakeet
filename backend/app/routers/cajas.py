from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import Admin
from app.models.caja import CajaAlmacenamiento
from app.models.item import EstadoItem, Item
from app.schemas.caja import CajaAsignar, CajaCreate
from app.schemas.item import CajaOut, ItemOut

router = APIRouter(prefix="/cajas", tags=["cajas"])


@router.post("", response_model=CajaOut, status_code=status.HTTP_201_CREATED)
def crear_caja(
    body: CajaCreate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    existe = (
        db.query(CajaAlmacenamiento)
        .filter(CajaAlmacenamiento.etiqueta == body.etiqueta.strip())
        .first()
    )
    if existe:
        raise HTTPException(
            status_code=409, detail="Ya existe una caja con esa etiqueta"
        )
    caja = CajaAlmacenamiento(
        etiqueta=body.etiqueta.strip(), descripcion=body.descripcion
    )
    db.add(caja)
    db.commit()
    db.refresh(caja)
    return caja


@router.get("", response_model=list[CajaOut])
def listar_cajas(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    return db.query(CajaAlmacenamiento).order_by(CajaAlmacenamiento.etiqueta).all()


items_router = APIRouter(prefix="/items", tags=["cajas"])


@items_router.patch("/{item_id}/caja", response_model=ItemOut)
def asignar_caja(
    item_id: int,
    body: CajaAsignar,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    if item.estado != EstadoItem.ADQUIRIDO:
        raise HTTPException(
            status_code=409,
            detail="Solo un item adquirido puede asignarse a una caja",
        )
    if body.caja_id is not None:
        caja = (
            db.query(CajaAlmacenamiento)
            .filter(CajaAlmacenamiento.id == body.caja_id)
            .first()
        )
        if not caja:
            raise HTTPException(status_code=404, detail="Caja no encontrada")
    item.caja_id = body.caja_id
    db.commit()
    db.refresh(item)
    return item
