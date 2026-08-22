"""Tests del endurecimiento del login.

Las tres propiedades que fijan, y que eran las tres exposiciones reales:

1. **El límite corta antes de verificar el hash.** Cada verificación Argon2id
   cuesta ~70 ms de CPU. Un límite evaluado después frenaría la fuerza bruta pero
   no la saturación, que es la otra mitad del problema.
2. **El tiempo de respuesta no dice si el email existe.** Antes, un correo
   desconocido volvía en microsegundos y uno real en ~70 ms.
3. **La política de contraseñas es largo mínimo**, no un juego de mayúsculas y
   símbolos: esas reglas producen `Viveprop2026!`, que cumple todo y es
   adivinable.
"""
import time
from datetime import datetime, timedelta, timezone

import pytest

from app.models.intento_login import IntentoLogin
from app.models.usuario import RolUsuario, Usuario
from app.security import hash_password
from app.services.intentos_login import (
    BLOQUEO,
    LARGO_MINIMO,
    PROHIBIDAS,
    UMBRAL_EMAIL,
    UMBRAL_IP,
    ClaveDebil,
    DemasiadosIntentos,
    limpiar_viejos,
    registrar_exito,
    registrar_fallo,
    validar_clave,
    verificar,
)

AHORA = datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc)
CLAVE_BUENA = "una-clave-larga-y-propia"


@pytest.fixture
def cliente_real(db):
    """`TestClient` con la autenticación real: el login es lo que se prueba."""
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


@pytest.fixture
def usuario(db):
    u = Usuario(
        id=1, email="felipe@viveprop.com", nombre="Felipe",
        password_hash=hash_password(CLAVE_BUENA), rol=RolUsuario.admin, activo=True,
    )
    db.add(u)
    db.commit()
    return u


def _login(cliente, clave, email="felipe@viveprop.com"):
    return cliente.post("/api/auth/login", json={"email": email, "password": clave})


# ------------------------------------------------- política de contraseñas


@pytest.mark.parametrize("clave", ["", "1", "corta", "123456789"])
def test_se_rechaza_una_clave_corta(clave):
    with pytest.raises(ClaveDebil, match=str(LARGO_MINIMO)):
        validar_clave(clave)


def test_el_largo_minimo_alcanza():
    """Sin mayúsculas ni símbolos: el largo es lo único que correlaciona."""
    validar_clave("a" * LARGO_MINIMO)   # no levanta


@pytest.mark.parametrize("clave", ["viveprop2026", "VIVEPROP2026", "1234567890", "contrasena"])
def test_se_rechazan_las_peores_aunque_sean_largas(clave):
    """`viveprop2026` tiene 12 caracteres y es exactamente lo que alguien elige
    cuando tiene que inventar una clave en el momento."""
    assert len(clave) >= LARGO_MINIMO
    with pytest.raises(ClaveDebil, match="más usadas"):
        validar_clave(clave)


def test_la_lista_de_prohibidas_esta_en_minuscula():
    """Si tuviera mayúsculas, la comparación en minúscula nunca las encontraría."""
    assert all(p == p.lower() for p in PROHIBIDAS)


def test_una_frase_con_espacios_sirve():
    """El largo se mide tal cual: los espacios son parte de la contraseña."""
    validar_clave("mi perro se llama mateo")


# ------------------------------------------- el límite corta antes del hash


def test_el_bloqueo_no_verifica_el_hash(db, usuario, monkeypatch):
    """La propiedad que hace que esto también sirva contra la saturación."""
    import app.routers.auth as router

    llamadas = []
    original = router.verify_password
    monkeypatch.setattr(
        router, "verify_password",
        lambda h, c: llamadas.append(1) or original(h, c),
    )

    db.add(IntentoLogin(
        clave="email:felipe@viveprop.com", fallidos=UMBRAL_EMAIL,
        bloqueado_hasta=datetime.now(timezone.utc) + BLOQUEO,
    ))
    db.commit()

    from fastapi.testclient import TestClient

    from app.config import settings
    from app.db import get_db
    from app.main import app

    settings.tareas_de_fondo = False
    app.dependency_overrides[get_db] = lambda: db
    try:
        with TestClient(app) as c:
            r = c.post("/api/auth/login",
                       json={"email": "felipe@viveprop.com", "password": CLAVE_BUENA})
    finally:
        app.dependency_overrides.clear()

    assert r.status_code == 429
    # Ni una verificación de hash: el rechazo no cuesta CPU.
    assert llamadas == []


def test_a_los_cinco_fallos_se_bloquea(cliente_real, usuario):
    for i in range(UMBRAL_EMAIL):
        assert _login(cliente_real, "incorrecta").status_code == 401, f"intento {i}"

    r = _login(cliente_real, "incorrecta")
    assert r.status_code == 429
    assert "segundos" in r.json()["detail"]


def test_la_clave_correcta_tampoco_pasa_estando_bloqueado(cliente_real, usuario):
    """Si la correcta pasara, bastaria con acertar en el intento numero seis."""
    for _ in range(UMBRAL_EMAIL):
        _login(cliente_real, "incorrecta")

    assert _login(cliente_real, CLAVE_BUENA).status_code == 429


def test_entrar_bien_limpia_el_contador(cliente_real, usuario, db):
    for _ in range(UMBRAL_EMAIL - 1):
        _login(cliente_real, "incorrecta")

    assert _login(cliente_real, CLAVE_BUENA).status_code == 200
    assert db.get(IntentoLogin, "email:felipe@viveprop.com") is None

    # Y el contador arranca de cero: hay margen completo otra vez.
    for _ in range(UMBRAL_EMAIL - 1):
        assert _login(cliente_real, "incorrecta").status_code == 401


def test_el_bloqueo_vence_y_perdona_el_contador(db, usuario):
    """Pasada la ventana se vuelve a contar de cero, no se queda al borde."""
    for _ in range(UMBRAL_EMAIL):
        registrar_fallo(db, usuario.email, "1.2.3.4", ahora=AHORA)

    with pytest.raises(DemasiadosIntentos):
        verificar(db, usuario.email, "1.2.3.4", ahora=AHORA + timedelta(minutes=1))

    despues = AHORA + BLOQUEO + timedelta(seconds=1)
    verificar(db, usuario.email, "1.2.3.4", ahora=despues)   # no levanta

    registrar_fallo(db, usuario.email, "1.2.3.4", ahora=despues)
    assert db.get(IntentoLogin, "email:felipe@viveprop.com").fallidos == 1


def test_el_mismo_email_con_otro_case_cuenta_igual(db, usuario):
    """Si no, el limite se esquiva escribiendo FELIPE@ en vez de felipe@."""
    for _ in range(UMBRAL_EMAIL):
        registrar_fallo(db, "FELIPE@VIVEPROP.COM", None, ahora=AHORA)

    with pytest.raises(DemasiadosIntentos):
        verificar(db, "felipe@viveprop.com", None, ahora=AHORA)


def test_se_cuenta_por_ip_ademas_de_por_email(db):
    """Protege al servidor de quien prueba correos al azar: por email nunca
    llegaria al umbral, pero la IP si."""
    for i in range(UMBRAL_IP):
        registrar_fallo(db, f"desconocido{i}@viveprop.com", "9.9.9.9", ahora=AHORA)

    with pytest.raises(DemasiadosIntentos):
        verificar(db, "otro-mas@viveprop.com", "9.9.9.9", ahora=AHORA)


def test_el_umbral_de_ip_es_mas_alto_que_el_de_email():
    """Una oficina comparte salida: varias personas pueden fallar el mismo dia."""
    assert UMBRAL_IP > UMBRAL_EMAIL


def test_sin_ip_solo_se_cuenta_el_email(db, usuario):
    """`request.client` puede venir vacio; eso no puede romper el login."""
    for _ in range(UMBRAL_EMAIL):
        registrar_fallo(db, usuario.email, None, ahora=AHORA)

    with pytest.raises(DemasiadosIntentos):
        verificar(db, usuario.email, None, ahora=AHORA)


# ----------------------------------------------------- la fuga de tiempos


def test_un_email_inexistente_tarda_lo_mismo_que_uno_real(cliente_real, db, usuario):
    """Antes, el desconocido volvia en microsegundos y el real en ~70 ms.

    Se comparan medianas de tres corridas: una sola medicion en una maquina
    compartida es ruido. El margen es amplio a proposito -- lo que se prueba es
    que no queda un orden de magnitud de diferencia, no que sean identicas.
    """
    def medir(email):
        tiempos = []
        for _ in range(3):
            inicio = time.perf_counter()
            _login(cliente_real, "incorrecta-pero-larga", email=email)
            tiempos.append(time.perf_counter() - inicio)
            # Se limpia el contador entre mediciones para no topar el bloqueo, que
            # devolveria rapido y falsearia el resultado.
            registrar_exito(db, email, None)
        return sorted(tiempos)[1]

    desconocido = medir("nadie-aqui@viveprop.com")
    real = medir(usuario.email)

    assert min(desconocido, real) > 0
    assert max(desconocido, real) / min(desconocido, real) < 5


def test_el_email_inexistente_no_dice_que_no_existe(cliente_real, usuario):
    """El mensaje es el mismo en los dos casos."""
    a = _login(cliente_real, "incorrecta-pero-larga", email="nadie@viveprop.com")
    b = _login(cliente_real, "incorrecta-pero-larga")

    assert a.status_code == b.status_code == 401
    assert a.json()["detail"] == b.json()["detail"]


def test_un_usuario_inactivo_no_se_distingue_de_uno_inexistente(cliente_real, db, usuario):
    usuario.activo = False
    db.commit()

    r = _login(cliente_real, CLAVE_BUENA)

    assert r.status_code == 401
    assert r.json()["detail"] == "Email o contraseña incorrectos"


# ------------------------------------------------------------- limpieza


def test_la_limpieza_borra_las_filas_viejas(db):
    db.add_all([
        IntentoLogin(clave="ip:vieja", fallidos=1,
                     actualizado_en=AHORA - timedelta(days=30)),
        IntentoLogin(clave="ip:reciente", fallidos=1,
                     actualizado_en=AHORA - timedelta(hours=1)),
    ])
    db.commit()

    assert limpiar_viejos(db, ahora=AHORA) == 1
    assert db.get(IntentoLogin, "ip:vieja") is None
    assert db.get(IntentoLogin, "ip:reciente") is not None
