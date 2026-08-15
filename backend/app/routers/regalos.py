from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import Admin
from app.models.categoria import Categoria
from app.models.item import Item
from app.models.regalo import OrigenRegalo, Regalo
from app.schemas.regalo import (
    RegaloCreate,
    RegaloOut,
    RegalosDePersonaOut,
    RegaloUpdate,
)
from app.services.items import recalcular_item

router = APIRouter(prefix="/regalos", tags=["regalos"])


def _cargado(query):
    return query.options(
        selectinload(Regalo.fotos),
        selectinload(Regalo.item).selectinload(Item.fotos),
    )


def _get_regalo_or_404(regalo_id: int, db: Session) -> Regalo:
    regalo = _cargado(db.query(Regalo)).filter(Regalo.id == regalo_id).first()
    if not regalo:
        raise HTTPException(status_code=404, detail="Regalo no encontrado")
    return regalo


@router.post("", response_model=RegaloOut, status_code=status.HTTP_201_CREATED)
def registrar_regalo(
    body: RegaloCreate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Registra 'recibimos X de parte de Y' en un solo paso.

    Si el objeto no existe todavía se crea acá mismo: la mayoría de los
    regalos llegan sin haber pasado por la wishlist.
    """
    if body.item_nuevo is not None:
        if body.item_nuevo.categoria_id is not None:
            existe = (
                db.query(Categoria)
                .filter(Categoria.id == body.item_nuevo.categoria_id)
                .first()
            )
            if not existe:
                raise HTTPException(status_code=404, detail="Categoría no encontrada")
        item = Item(**body.item_nuevo.model_dump(), cantidad=body.cantidad)
        db.add(item)
        db.flush()
    else:
        item = db.query(Item).filter(Item.id == body.item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item no encontrado")

    regalo = Regalo(
        item_id=item.id,
        persona=body.persona.strip(),
        origen=body.origen,
        cantidad=body.cantidad,
        fecha=body.fecha or datetime.now(UTC).date(),
        nota=(body.nota or "").strip() or None,
    )
    db.add(regalo)
    recalcular_item(db, item)
    db.commit()
    return _get_regalo_or_404(regalo.id, db)


@router.get("", response_model=list[RegaloOut])
def listar_regalos(
    persona: str | None = None,
    agradecido: bool | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    query = _cargado(db.query(Regalo))
    if persona:
        query = query.filter(Regalo.persona == persona)
    if agradecido is not None:
        query = query.filter(Regalo.agradecido.is_(agradecido))
    if desde:
        query = query.filter(Regalo.fecha >= desde)
    if hasta:
        query = query.filter(Regalo.fecha <= hasta)
    return query.order_by(Regalo.fecha.desc(), Regalo.id.desc()).all()


@router.get("/personas", response_model=list[str])
def listar_personas(
    q: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Nombres ya usados, para el autocompletado.

    Es lo que mantiene consistente el texto libre: si Ana ya existe, se
    elige de la lista en vez de volver a escribirla distinto.
    """
    query = db.query(Regalo.persona).filter(Regalo.persona != "").distinct()
    if q:
        query = query.filter(Regalo.persona.ilike(f"%{q.strip()}%"))
    return sorted(p[0] for p in query.all())


@router.get("/por-persona", response_model=list[RegalosDePersonaOut])
def regalos_por_persona(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    """Lo que regaló cada persona, para agradecer sin olvidarse de nadie."""
    regalos = (
        _cargado(db.query(Regalo))
        .filter(Regalo.persona != "")
        .order_by(Regalo.persona, Regalo.fecha)
        .all()
    )
    agrupados: dict[str, list[Regalo]] = {}
    for regalo in regalos:
        agrupados.setdefault(regalo.persona, []).append(regalo)

    return [
        RegalosDePersonaOut(
            persona=persona,
            total_regalos=len(items),
            pendientes_de_agradecer=sum(1 for r in items if not r.agradecido),
            regalos=[RegaloOut.model_validate(r) for r in items],
        )
        for persona, items in agrupados.items()
    ]


@router.patch("/{regalo_id}", response_model=RegaloOut)
def editar_regalo(
    regalo_id: int,
    body: RegaloUpdate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    regalo = _get_regalo_or_404(regalo_id, db)
    cambios = body.model_dump(exclude_unset=True)
    if "persona" in cambios and cambios["persona"] is not None:
        cambios["persona"] = cambios["persona"].strip()
        if not cambios["persona"] and regalo.origen == OrigenRegalo.REGALO:
            raise HTTPException(
                status_code=422,
                detail="Un regalo necesita el nombre de quien lo regaló",
            )
    for campo, valor in cambios.items():
        setattr(regalo, campo, valor)
    recalcular_item(db, regalo.item)
    db.commit()
    return _get_regalo_or_404(regalo_id, db)


@router.delete("/{regalo_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_regalo(
    regalo_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    regalo = _get_regalo_or_404(regalo_id, db)
    item = regalo.item
    db.delete(regalo)
    recalcular_item(db, item)
    db.commit()
