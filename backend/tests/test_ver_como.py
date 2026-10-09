"""Un admin ve la app como otro usuario, solo para mirar (`D-120`).

Se prueba con la cadena real --cookie, sesión y guardas--, porque eso es justo lo
que la vista cambia: `resolver_usuario` devuelve al usuario visto.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.auth import COOKIE_NAME, SOLO_LECTURA
from app.models.usuario import RolUsuario, Sesion, Usuario, VistaComo


@pytest.fixture
def cliente_real(db):
    from fastapi.testclient import TestClient

    from app.config import settings
    from app.db import get_db
    from app.main import app

    settings.tareas_de_fondo = False
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


def _usuario(db, id_, nombre, rol, activo=True, forzar=False):
    u = Usuario(
        id=id_, email=f"{nombre.lower()}@viveprop.com", nombre=nombre, password_hash="x",
        rol=rol, activo=activo, debe_cambiar_password=forzar,
    )
    db.add(u)
    db.commit()
    return u


def _entrar(db, cliente, usuario_id) -> str:
    sid = uuid.uuid4()
    ahora = datetime.now(timezone.utc)
    db.add(Sesion(id=sid, usuario_id=usuario_id, creado_en=ahora, expira_en=ahora + timedelta(hours=12)))
    db.commit()
    cliente.cookies.set(COOKIE_NAME, str(sid))
    return str(sid)


@pytest.fixture
def gente(db):
    return {
        "admin": _usuario(db, 1, "Felipe", RolUsuario.admin),
        "otro_admin": _usuario(db, 2, "Isidora", RolUsuario.admin),
        "gerencia": _usuario(db, 3, "Gonzalo", RolUsuario.gerencia),
        "operaciones": _usuario(db, 4, "Gianfranco", RolUsuario.operaciones),
        "inactivo": _usuario(db, 5, "Mario", RolUsuario.gerencia, activo=False),
    }


def test_el_admin_ve_como_gerencia_y_vuelve(db, cliente_real, gente):
    _entrar(db, cliente_real, 1)

    r = cliente_real.post("/api/admin/usuarios/3/ver-como")
    assert r.status_code == 200, r.text

    yo = cliente_real.get("/api/auth/me").json()
    assert (yo["id"], yo["rol"]) == (3, "gerencia")
    assert yo["vista_de_admin"] == {"id": 1, "nombre": "Felipe"}

    # Con los permisos del visto: gerencia no entra a la administración.
    assert cliente_real.get("/api/admin/usuarios").status_code == 403

    r = cliente_real.post("/api/auth/dejar-de-ver-como")
    assert r.status_code == 200
    assert r.json()["id"] == 1
    yo = cliente_real.get("/api/auth/me").json()
    assert (yo["id"], yo["vista_de_admin"]) == (1, None)

    (registro,) = db.scalars(select(VistaComo)).all()
    assert (registro.admin_id, registro.usuario_id) == (1, 3)
    assert registro.fin is not None


def test_en_la_vista_solo_se_mira(db, cliente_real, gente):
    _entrar(db, cliente_real, 1)
    cliente_real.post("/api/admin/usuarios/4/ver-como")

    # Operaciones puede registrar cambios, pero desde la vista no: quedarían a su
    # nombre. Se rechaza cualquier método que no sea de lectura.
    r = cliente_real.post("/api/canjes", json={})
    assert r.status_code == 403
    assert r.json()["detail"] == SOLO_LECTURA
    assert cliente_real.post("/api/auth/cambiar-clave", json={}).status_code == 403
    # Y no se encadenan vistas.
    assert cliente_real.post("/api/admin/usuarios/3/ver-como").status_code == 403
    # Mirar sí.
    assert cliente_real.get("/api/canjes/reportes/resumen").status_code == 200


@pytest.mark.parametrize(
    "objetivo, codigo",
    [(1, 400), (2, 400), (5, 400), (999, 404)],
    ids=["a si mismo", "otro admin", "desactivado", "no existe"],
)
def test_a_quien_no_se_puede_ver(db, cliente_real, gente, objetivo, codigo):
    _entrar(db, cliente_real, 1)
    assert cliente_real.post(f"/api/admin/usuarios/{objetivo}/ver-como").status_code == codigo
    assert db.scalars(select(VistaComo)).all() == []


def test_solo_un_admin_puede_ver_como_otro(db, cliente_real, gente):
    _entrar(db, cliente_real, 4)
    assert cliente_real.post("/api/admin/usuarios/3/ver-como").status_code == 403


def test_salir_cierra_el_registro(db, cliente_real, gente):
    _entrar(db, cliente_real, 1)
    cliente_real.post("/api/admin/usuarios/3/ver-como")
    cliente_real.post("/api/auth/logout")

    (registro,) = db.scalars(select(VistaComo)).all()
    assert registro.fin is not None


def test_la_clave_temporal_del_visto_no_bloquea_la_vista(db, cliente_real, gente):
    _usuario(db, 6, "Nuevo", RolUsuario.gerencia, forzar=True)
    _entrar(db, cliente_real, 1)
    cliente_real.post("/api/admin/usuarios/6/ver-como")

    assert cliente_real.get("/api/auth/me").json()["debe_cambiar_password"] is False
    assert cliente_real.get("/api/canjes/reportes/resumen").status_code == 200


def test_si_el_visto_se_desactiva_la_vista_termina_sola(db, cliente_real, gente):
    _entrar(db, cliente_real, 1)
    cliente_real.post("/api/admin/usuarios/3/ver-como")
    gente["gerencia"].activo = False
    db.commit()

    yo = cliente_real.get("/api/auth/me").json()
    assert (yo["id"], yo["vista_de_admin"]) == (1, None)
    assert db.scalars(select(VistaComo)).one().fin is not None


def test_el_registro_se_lista_del_mas_reciente(db, cliente_real, gente):
    _entrar(db, cliente_real, 1)
    cliente_real.post("/api/admin/usuarios/3/ver-como")
    cliente_real.post("/api/auth/dejar-de-ver-como")
    cliente_real.post("/api/admin/usuarios/4/ver-como")
    cliente_real.post("/api/auth/dejar-de-ver-como")

    filas = cliente_real.get("/api/admin/usuarios/vistas-como").json()
    assert [(f["admin"], f["usuario"]) for f in filas] == [
        ("Felipe", "Gianfranco"),
        ("Felipe", "Gonzalo"),
    ]
