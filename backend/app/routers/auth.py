from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_admin
from app.core.security import create_access_token, verify_password
from app.models.admin import Admin
from app.schemas.auth import AdminOut, LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == body.email.lower()).first()
    if not admin or not verify_password(body.password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )
    token = create_access_token({"sub": str(admin.id)})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=AdminOut)
def me(current_admin: Admin = Depends(get_current_admin)):
    return current_admin
