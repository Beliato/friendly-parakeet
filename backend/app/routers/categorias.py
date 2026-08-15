from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.models.admin import Admin
from app.models.categoria import Categoria
from app.schemas.item import CategoriaOut

router = APIRouter(prefix="/categorias", tags=["categorias"])


class CategoriaCreate(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)


@router.post("", response_model=CategoriaOut, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    body: CategoriaCreate,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    nombre = body.nombre.strip()
    if db.query(Categoria).filter(Categoria.nombre == nombre).first():
        raise HTTPException(status_code=409, detail="Ya existe esa categoría")
    categoria = Categoria(nombre=nombre)
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


@router.get("", response_model=list[CategoriaOut])
def listar_categorias(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
):
    return db.query(Categoria).order_by(Categoria.nombre).all()
