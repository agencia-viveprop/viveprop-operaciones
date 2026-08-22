"""Tests del reset de contraseña con cambio forzado (sprint 22).

La propiedad central: **la guarda está en la API, no en la pantalla.** Si el
cambio forzado solo lo aplicara el front, la clave temporal serviría para usar
toda la API con cualquier cliente y el sprint entero sería decorativo. Casi todos
los tests de acá existen para fijar eso.

La segunda: **un reset cierra las sesiones abiertas.** Sin eso, una pestaña ya
logueada seguiría con todos los permisos hasta doce horas, y el cambio forzado no
se aplicaría nunca.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.auth import CLAVE_VENCIDA, COOKIE_NAME
from app.models.usuario import RolUsuario, Sesion, Usuario
from app.routers.usuarios import ALFABETO_TEMPORAL, LARGO_TEMPORAL
from app.security import hash_password, verify_password


@pytest.fixture
def cliente_real(db):
    """`TestClient` **sin** sobreescribir la autenticación.

    El fixture `cliente` reemplaza `get_current_user`, que es justo la pieza que
    acá hay que probar. Este usa la cadena real: cookie, sesión y guarda.
    """
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


def _usuario(db, id_, email, rol=RolUsuario.operaciones, clave="clave-vieja", forzar=False):
    u = Usuario(
        id=id_, email=email, nombre=email.split("@")[0],
        password_hash=hash_password(clave), rol=rol, activo=True,
        debe_cambiar_password=forzar,
    )
    db.add(u)
    db.commit()
    return u


def _sesion(db, usuario_id) -> str:
    sid = uuid.uuid4()
    ahora = datetime.now(timezone.utc)
    db.add(Sesion(id=sid, usuario_id=usuario_id, creado_en=ahora,
                  expira_en=ahora + timedelta(hours=12)))
    db.commit()
    return str(sid)


# ------------------------------------------------------- la clave temporal


def test_la_clave_temporal_no_trae_caracteres_confundibles():
    """Se dicta por telefono o se copia de un chat: I, l, 1, O y 0 se confunden."""
    for prohibido in "IlO10":
        assert prohibido not in ALFABETO_TEMPORAL


def test_el_alfabeto_deja_suficiente_entropia():
    """Sacar cinco caracteres no puede dejar una clave adivinable."""
    assert len(ALFABETO_TEMPORAL) >= 55
    assert LARGO_TEMPORAL >= 12


def test_el_reset_devuelve_la_clave_una_vez_y_guarda_su_hash(cliente_real, db):
    admin = _usuario(db, 1, "admin@viveprop.com", RolUsuario.admin)
    otro = _usuario(db, 2, "otro@viveprop.com")
    galleta = {COOKIE_NAME: _sesion(db, admin.id)}

    r = cliente_real.post(f"/api/admin/usuarios/{otro.id}/resetear-clave", cookies=galleta)

    assert r.status_code == 200
    temporal = r.json()["clave_temporal"]
    assert len(temporal) == LARGO_TEMPORAL

    db.expire_all()
    guardado = db.get(Usuario, otro.id)
    # Lo que queda en la base es el hash, no el texto.
    assert guardado.password_hash != temporal
    assert verify_password(guardado.password_hash, temporal)
    assert guardado.debe_cambiar_password is True


def test_dos_resets_dan_claves_distintas(cliente_real, db):
    admin = _usuario(db, 1, "admin@viveprop.com", RolUsuario.admin)
    otro = _usuario(db, 2, "otro@viveprop.com")
    galleta = {COOKIE_NAME: _sesion(db, admin.id)}

    una = cliente_real.post(f"/api/admin/usuarios/{otro.id}/resetear-clave", cookies=galleta).json()
    otra = cliente_real.post(f"/api/admin/usuarios/{otro.id}/resetear-clave", cookies=galleta).json()

    assert una["clave_temporal"] != otra["clave_temporal"]


def test_el_reset_cierra_las_sesiones_de_esa_persona(cliente_real, db):
    """Sin esto una pestaña ya abierta seguiria con todos los permisos."""
    admin = _usuario(db, 1, "admin@viveprop.com", RolUsuario.admin)
    otro = _usuario(db, 2, "otro@viveprop.com")
    sesion_del_otro = _sesion(db, otro.id)
    galleta_admin = {COOKIE_NAME: _sesion(db, admin.id)}

    cliente_real.post(f"/api/admin/usuarios/{otro.id}/resetear-clave", cookies=galleta_admin)

    db.expire_all()
    assert db.get(Sesion, uuid.UUID(sesion_del_otro)) is None
    # La del admin sigue viva: no se cierra la sesion de quien reseteo.
    assert len(db.execute(select(Sesion)).scalars().all()) == 1


def test_no_se_puede_resetear_la_propia(cliente_real, db):
    """El unico admin que se resetee a si mismo y pierda el texto queda afuera."""
    admin = _usuario(db, 1, "admin@viveprop.com", RolUsuario.admin)
    galleta = {COOKIE_NAME: _sesion(db, admin.id)}

    r = cliente_real.post(f"/api/admin/usuarios/{admin.id}/resetear-clave", cookies=galleta)

    assert r.status_code == 400
    assert "Cambiar contraseña" in r.json()["detail"]


def test_solo_admin_puede_resetear(cliente_real, db):
    operaciones = _usuario(db, 2, "ops@viveprop.com", RolUsuario.operaciones)
    otro = _usuario(db, 3, "otro@viveprop.com")
    galleta = {COOKIE_NAME: _sesion(db, operaciones.id)}

    r = cliente_real.post(f"/api/admin/usuarios/{otro.id}/resetear-clave", cookies=galleta)

    assert r.status_code == 403


# ------------------------------- la guarda esta en la API, no en la pantalla


@pytest.mark.parametrize("ruta", [
    "/api/canjes",
    "/api/negocios",
    "/api/catalogos",
    "/api/uf/estado",
    "/api/reportes/semanal",
    "/api/admin/usuarios",
])
def test_con_clave_temporal_la_api_no_deja_hacer_nada(cliente_real, db, ruta):
    """Lo que hace que el cambio forzado no sea decorativo."""
    u = _usuario(db, 1, "u@viveprop.com", RolUsuario.admin, forzar=True)
    galleta = {COOKIE_NAME: _sesion(db, u.id)}

    r = cliente_real.get(ruta, cookies=galleta)

    assert r.status_code == 403
    assert r.json()["detail"] == CLAVE_VENCIDA


def test_con_clave_temporal_si_se_puede_ver_quien_soy(cliente_real, db):
    """El front lo necesita para saber que hay que mostrar el formulario."""
    u = _usuario(db, 1, "u@viveprop.com", forzar=True)
    galleta = {COOKIE_NAME: _sesion(db, u.id)}

    r = cliente_real.get("/api/auth/me", cookies=galleta)

    assert r.status_code == 200
    assert r.json()["debe_cambiar_password"] is True


def test_con_clave_temporal_si_se_puede_salir(cliente_real, db):
    u = _usuario(db, 1, "u@viveprop.com", forzar=True)
    galleta = {COOKIE_NAME: _sesion(db, u.id)}

    assert cliente_real.post("/api/auth/logout", cookies=galleta).status_code == 200


def test_con_clave_temporal_si_se_puede_cambiar_la_clave(cliente_real, db):
    """El punto: con la dependencia estricta, quedaria bloqueado del unico
    endpoint que lo desbloquea."""
    u = _usuario(db, 1, "u@viveprop.com", clave="temporal-abc", forzar=True)
    galleta = {COOKIE_NAME: _sesion(db, u.id)}

    r = cliente_real.post(
        "/api/auth/cambiar-clave",
        json={"clave_actual": "temporal-abc", "clave_nueva": "la-mia-nueva"},
        cookies=galleta,
    )

    assert r.status_code == 200
    db.expire_all()
    assert db.get(Usuario, u.id).debe_cambiar_password is False


def test_cambiar_la_clave_desbloquea_el_resto(cliente_real, db):
    u = _usuario(db, 1, "u@viveprop.com", clave="temporal-abc", forzar=True)
    galleta = {COOKIE_NAME: _sesion(db, u.id)}

    assert cliente_real.get("/api/canjes", cookies=galleta).status_code == 403
    cliente_real.post(
        "/api/auth/cambiar-clave",
        json={"clave_actual": "temporal-abc", "clave_nueva": "la-mia-nueva"},
        cookies=galleta,
    )
    assert cliente_real.get("/api/canjes", cookies=galleta).status_code == 200


def test_la_clave_nueva_no_puede_ser_la_misma(cliente_real, db):
    """Si no, "cambiar" la clave temporal por si misma limpiaria el flag."""
    u = _usuario(db, 1, "u@viveprop.com", clave="temporal-abc", forzar=True)
    galleta = {COOKIE_NAME: _sesion(db, u.id)}

    r = cliente_real.post(
        "/api/auth/cambiar-clave",
        json={"clave_actual": "temporal-abc", "clave_nueva": "temporal-abc"},
        cookies=galleta,
    )

    assert r.status_code == 400
    db.expire_all()
    assert db.get(Usuario, u.id).debe_cambiar_password is True


def test_la_clave_actual_equivocada_no_limpia_el_flag(cliente_real, db):
    u = _usuario(db, 1, "u@viveprop.com", clave="temporal-abc", forzar=True)
    galleta = {COOKIE_NAME: _sesion(db, u.id)}

    r = cliente_real.post(
        "/api/auth/cambiar-clave",
        json={"clave_actual": "otra-cosa", "clave_nueva": "la-mia-nueva"},
        cookies=galleta,
    )

    assert r.status_code == 401
    db.expire_all()
    assert db.get(Usuario, u.id).debe_cambiar_password is True


# --------------------------------------------------------- la vuelta entera


def test_la_vuelta_entera(cliente_real, db):
    """Admin resetea, la persona entra con la temporal, la cambia y ya opera."""
    admin = _usuario(db, 1, "admin@viveprop.com", RolUsuario.admin)
    otro = _usuario(db, 2, "otro@viveprop.com")
    galleta_admin = {COOKIE_NAME: _sesion(db, admin.id)}

    temporal = cliente_real.post(
        f"/api/admin/usuarios/{otro.id}/resetear-clave", cookies=galleta_admin
    ).json()["clave_temporal"]

    entrada = cliente_real.post(
        "/api/auth/login", json={"email": otro.email, "password": temporal}
    )
    assert entrada.status_code == 200
    assert entrada.json()["debe_cambiar_password"] is True

    # La cookie de la sesión nueva la puso el login.
    assert cliente_real.get("/api/canjes").status_code == 403

    assert cliente_real.post(
        "/api/auth/cambiar-clave",
        json={"clave_actual": temporal, "clave_nueva": "mi-clave-de-verdad"},
    ).status_code == 200

    assert cliente_real.get("/api/canjes").status_code == 200
    # Y la vieja ya no sirve.
    assert cliente_real.post(
        "/api/auth/login", json={"email": otro.email, "password": temporal}
    ).status_code == 401
