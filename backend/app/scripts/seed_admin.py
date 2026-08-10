"""Crea (o actualiza la contrasena de) un usuario admin. Uso:

    python -m app.scripts.seed_admin <email> <password> "<Nombre Completo>"

No hay registro propio en la app -- las cuentas se crean asi, a mano,
por el rol admin (o por este script para la primera cuenta).
"""
import sys

from sqlalchemy import select

from app.db import SessionLocal
from app.models.usuario import RolUsuario, Usuario
from app.security import hash_password


def main() -> None:
    if len(sys.argv) < 4:
        print(__doc__)
        raise SystemExit(1)

    email, password, nombre = sys.argv[1], sys.argv[2], sys.argv[3]

    db = SessionLocal()
    try:
        usuario = db.scalar(select(Usuario).where(Usuario.email == email))
        if usuario is None:
            usuario = Usuario(email=email, nombre=nombre, rol=RolUsuario.admin, password_hash=hash_password(password))
            db.add(usuario)
            print(f"Usuario admin creado: {email}")
        else:
            usuario.password_hash = hash_password(password)
            usuario.rol = RolUsuario.admin
            usuario.activo = True
            print(f"Usuario existente actualizado a admin: {email}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
