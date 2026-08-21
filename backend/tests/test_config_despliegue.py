"""Tests de la configuración de despliegue (sprint 2).

Lo que protegen es un modo de falla silencioso: antes, `secure` de la cookie de
sesión se activaba solo si `ENVIRONMENT == "production"`. Si esa variable
faltaba en Render o venía con un typo, la cookie salía sin `secure` sobre HTTPS
y **nada fallaba** -- la app seguía funcionando igual, solo que la sesión viajaba
expuesta a cualquier interceptor de la red. Un test que fije la dirección del
default es la única forma de que eso no vuelva.
"""
import pytest
from fastapi import Response

from app.auth import COOKIE_NAME, set_session_cookie
from app.config import Settings


@pytest.mark.parametrize("valor", ["development", "local", "test", "  Development  ", "TEST"])
def test_los_ambientes_locales_declarados_son_locales(valor):
    assert Settings(environment=valor).es_local is True


@pytest.mark.parametrize(
    "valor",
    [
        "production",
        "",            # la variable existe pero vacía
        "prod",        # abreviatura razonable que igual no es "production"
        "developmnet",  # el typo que antes dejaba la cookie sin `secure`
        "staging",
    ],
)
def test_cualquier_otro_valor_cae_del_lado_seguro(valor):
    assert Settings(environment=valor).es_local is False


def test_la_cookie_de_sesion_lleva_las_tres_defensas(monkeypatch):
    """`secure` contra la red, `httponly` contra el script, `lax` contra el CSRF."""
    import app.auth as modulo

    monkeypatch.setattr(modulo.settings, "environment", "production")
    respuesta = Response()
    set_session_cookie(respuesta, "11111111-2222-3333-4444-555555555555")

    cookie = respuesta.headers["set-cookie"]
    assert cookie.startswith(f"{COOKIE_NAME}=")
    assert "Secure" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie


def test_en_local_la_cookie_sale_sin_secure(monkeypatch):
    """Si no, el navegador no la guarda sobre http://localhost y no hay login."""
    import app.auth as modulo

    monkeypatch.setattr(modulo.settings, "environment", "development")
    respuesta = Response()
    set_session_cookie(respuesta, "11111111-2222-3333-4444-555555555555")

    cookie = respuesta.headers["set-cookie"]
    assert "Secure" not in cookie
    # Las otras dos no dependen del ambiente.
    assert "HttpOnly" in cookie


# ------------------------------------------------------------------ health


def test_health_no_toca_la_base(cliente):
    """Es el que mira Render: si dependiera de Neon, un despertar lento de la
    rama se leería como servicio caído."""
    r = cliente.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_health_db_confirma_que_la_base_responde(cliente):
    r = cliente.get("/api/health/db")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "base": "ok"}


def test_health_db_da_503_si_la_base_falla(cliente, db, monkeypatch):
    from sqlalchemy.exc import OperationalError

    def explotar(*_a, **_k):
        raise OperationalError("SELECT 1", {}, Exception("no se pudo conectar a ep-xxx.neon.tech"))

    monkeypatch.setattr(db, "execute", explotar)
    r = cliente.get("/api/health/db")

    assert r.status_code == 503
    cuerpo = r.json()
    assert cuerpo == {"status": "error", "base": "OperationalError"}
    # El host de la base no puede salir en un endpoint sin sesión.
    assert "neon.tech" not in r.text


# ------------------------------------------------------- servido de la SPA


@pytest.fixture
def estatico(tmp_path):
    """Un `static/` de mentira, con la forma del que arma el build de Render."""
    (tmp_path / "index.html").write_text("<!doctype html>SPA", encoding="utf-8")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "index-abc123.js").write_text("console.log(1)", encoding="utf-8")
    (tmp_path.parent / "secreto.env").write_text("DATABASE_URL=postgres://...", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize("ruta", ["api", "api/", "api/esto-no-existe", "api/canjes/999/raro"])
def test_un_api_sin_router_es_404_y_no_la_spa(estatico, ruta):
    """El defecto verificado en produccion: devolvia 200 con el index.html."""
    from fastapi import HTTPException

    from app.main import resolver_ruta_spa

    with pytest.raises(HTTPException) as e:
        resolver_ruta_spa(estatico, ruta)
    assert e.value.status_code == 404


@pytest.mark.parametrize("ruta", ["negocios", "reportes/semanal", "", "apiario"])
def test_las_rutas_de_la_spa_caen_en_el_index(estatico, ruta):
    """Ojo con `apiario`: empieza con "api" pero no es del prefijo."""
    from app.main import resolver_ruta_spa

    assert resolver_ruta_spa(estatico, ruta) == estatico / "index.html"


def test_un_archivo_que_existe_se_sirve_tal_cual(estatico):
    from app.main import resolver_ruta_spa

    assert resolver_ruta_spa(estatico, "assets/index-abc123.js") == estatico / "assets" / "index-abc123.js"


@pytest.mark.parametrize("ruta", [
    "../secreto.env",
    "assets/../../secreto.env",
    "./../secreto.env",
])
def test_no_se_puede_salir_de_static(estatico, ruta):
    """Debajo de `static/` estan el codigo y el .env; una ruta que sube cae en
    el index, no en el archivo."""
    from app.main import resolver_ruta_spa

    assert resolver_ruta_spa(estatico, ruta) == estatico / "index.html"
