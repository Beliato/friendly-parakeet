"""Crea (o actualiza) la cuenta admin única desde variables de entorno.

Uso:
    ADMIN_EMAIL=pareja@example.com ADMIN_PASSWORD=... python seed_admin.py

Idempotente: si el email ya existe, actualiza la contraseña.
"""

import os
import sys

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.admin import Admin


def main() -> int:
    email = os.environ.get("ADMIN_EMAIL", "").strip().lower()
    password = os.environ.get("ADMIN_PASSWORD", "")
    if not email or not password:
        print("ERROR: define ADMIN_EMAIL y ADMIN_PASSWORD en el entorno.")
        return 1
    if len(password) < 8:
        print("ERROR: ADMIN_PASSWORD debe tener al menos 8 caracteres.")
        return 1

    db = SessionLocal()
    try:
        admin = db.query(Admin).filter(Admin.email == email).first()
        if admin:
            admin.password_hash = hash_password(password)
            accion = "actualizada"
        else:
            admin = Admin(email=email, password_hash=hash_password(password))
            db.add(admin)
            accion = "creada"
        db.commit()
        print(f"Cuenta admin {accion}: {email}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
