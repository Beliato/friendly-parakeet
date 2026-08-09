from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core import storage_r2
from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import Admin
from app.models.item import FotoItem, Item
from app.schemas.foto import FotoConfirmar, PresignRequest, PresignResponse
from app.schemas.item import FotoItemOut

router = APIRouter(prefix="/items", tags=["fotos"])


def _get_item_or_404(item_id: int, db: Session) -> Item:
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    return item


def _check_r2():
    if not storage_r2.esta_configurado():
        raise HTTPException(
            status_code=503,
            detail="Storage de fotos no configurado (variables R2_* faltantes)",
        )


@router.post("/{item_id}/fotos/presign", response_model=PresignResponse)
def presign_foto(
    item_id: int,
    body: PresignRequest,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    _check_r2()
    _get_item_or_404(item_id, db)
    if body.content_type not in storage_r2.CONTENT_TYPES_PERMITIDOS:
        raise HTTPException(
            status_code=422,
            detail="Tipo de archivo no permitido (solo jpeg, png, webp)",
        )
    if body.size_bytes > storage_r2.MAX_BYTES:
        raise HTTPException(
            status_code=422,
            detail="La foto supera el tamaño máximo de 5 MB",
        )
    key = storage_r2.generar_key(item_id, body.content_type)
    url = storage_r2.presign_put(key, body.content_type)
    return PresignResponse(upload_url=url, key=key)


@router.post(
    "/{item_id}/fotos",
    response_model=FotoItemOut,
    status_code=status.HTTP_201_CREATED,
)
def confirmar_foto(
    item_id: int,
    body: FotoConfirmar,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    _check_r2()
    _get_item_or_404(item_id, db)
    if not storage_r2.key_pertenece_a_item(body.key, item_id):
        raise HTTPException(
            status_code=422,
            detail="La key no corresponde a un presign emitido para este item",
        )
    if not storage_r2.objeto_existe(body.key):
        raise HTTPException(
            status_code=422,
            detail="El archivo no existe en el storage (¿falló la subida?)",
        )
    foto = FotoItem(
        item_id=item_id, url=storage_r2.url_publica(body.key), orden=body.orden
    )
    db.add(foto)
    db.commit()
    db.refresh(foto)
    return foto


@router.delete("/{item_id}/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_foto(
    item_id: int,
    foto_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    foto = (
        db.query(FotoItem)
        .filter(FotoItem.id == foto_id, FotoItem.item_id == item_id)
        .first()
    )
    if not foto:
        raise HTTPException(status_code=404, detail="Foto no encontrada")
    if storage_r2.esta_configurado():
        key = storage_r2.key_desde_url(foto.url)
        if key:
            storage_r2.borrar_objeto(key)
    db.delete(foto)
    db.commit()
