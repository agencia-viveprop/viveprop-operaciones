"""Tabla de intentos de login, para el limite de fuerza bruta

Revision ID: e3b8c15d7a42
Revises: d1f4a72b6e59
Create Date: 2026-08-22

`/auth/login` aceptaba intentos infinitos. Medido: cada intento cuesta **70 ms de
CPU** verificando el hash Argon2id, así que la falta de límite era dos problemas
en uno -- fuerza bruta contra una contraseña que hasta hoy podía ser `"1"`, y un
vector de saturación, porque unos cientos de peticiones por segundo dejan el
proceso moliendo hashes y la app deja de responder.

**En la base y no en memoria.** Un contador en memoria se reinicia con cada
deploy y no sirve si algún día hay más de una instancia. La tabla es una fila por
clave y se limpia sola: el éxito borra la fila.

**La clave es genérica a propósito.** Se limita por email --protege la cuenta-- y
por IP --protege el servidor--, y las dos cosas viven en la misma tabla con un
prefijo (`email:...`, `ip:...`) en vez de en dos tablas o dos columnas. Es el
mismo mecanismo contando dos cosas distintas.
"""
from alembic import op
import sqlalchemy as sa

revision = "e3b8c15d7a42"
down_revision = "d1f4a72b6e59"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "intentos_login",
        # 'email:felipe@viveprop.com' o 'ip:1.2.3.4'.
        sa.Column("clave", sa.String(320), primary_key=True),
        sa.Column("fallidos", sa.Integer(), nullable=False, server_default="0"),
        # Nulo mientras no se haya alcanzado el umbral.
        sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    # Para la limpieza periódica de filas viejas. El nombre es el que genera
    # `index=True` en el modelo: si difiere, `alembic check` reporta desalineamiento.
    op.create_index("ix_intentos_login_actualizado_en", "intentos_login", ["actualizado_en"])


def downgrade() -> None:
    op.drop_index("ix_intentos_login_actualizado_en", table_name="intentos_login")
    op.drop_table("intentos_login")
