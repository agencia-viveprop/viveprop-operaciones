"""Dominios de la organización y autorización de accesos externos (`D-078`).

Las propiedades que protegen:

1. **La lista vacía cierra, no abre.** Es lo contrario de lo que hacía la variable
   de entorno que reemplaza, donde vacío significaba «sin restricción». Un campo
   que se edita a mano no puede tener un accidente que abra la app en silencio.
2. **Un correo de fuera se acepta, pero con nombre y fecha.** Los directores y
   advisors tienen correos cualesquiera y son parte del diseño; lo que no puede
   pasar es que para dejar entrar a uno haya que abrir su dominio entero.
3. **La lista no re-valida hacia atrás.** Quitar un dominio no le saca el acceso a
   nadie: eso lo hace el switch `activo` del usuario.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.models.catalogo import Catalogo
from app.models.usuario import RolUsuario, Usuario
from app.services import dominios_organizacion as servicio

CLAVE_OK = "Rinoceronte-Verde-42"


@pytest.fixture
def dominios(db):
    """Los dos que siembra la migración."""
    servicio.agregar(db, "viveprop.com", "ViveProp")
    servicio.agregar(db, "dataprop.cl", "Dataprop")
    return db


@pytest.fixture
def cliente_operaciones(db):
    """El mismo TestClient, pero con un usuario que no es admin."""
    from fastapi.testclient import TestClient

    from app.auth import get_current_user
    from app.config import settings
    from app.db import get_db
    from app.main import app

    settings.tareas_de_fondo = False
    usuario = Usuario(
        id=9, email="opera@viveprop.com", nombre="Opera", password_hash="x",
        rol=RolUsuario.operaciones,
    )
    db.add(usuario)
    db.commit()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: usuario
    try:
        with TestClient(app) as c:
            yield c
    finally:
        app.dependency_overrides.clear()


# --------------------------------------------------------- normalizacion


@pytest.mark.parametrize("entrada, esperado", [
    ("viveprop.com", "viveprop.com"),
    ("  ViveProp.COM  ", "viveprop.com"),
    ("@dataprop.cl", "dataprop.cl"),
    # Pegar un correo completo es lo que uno tiene a mano cuando esta agregando
    # el dominio de alguien: rechazarlo seria un tramite inventado.
    ("Felipe@ViveProp.com", "viveprop.com"),
    ("sub.dominio.co.uk", "sub.dominio.co.uk"),
])
def test_el_dominio_se_normaliza(entrada, esperado):
    assert servicio.normalizar(entrada) == esperado


@pytest.mark.parametrize("entrada", [
    "", "   ", "@", "viveprop", "vive prop.com", "-viveprop.com", "viveprop-.com",
    "viveprop.com/algo", "https://viveprop.com", "a" * 45 + ".com",
])
def test_lo_que_no_es_un_dominio_se_rechaza(entrada):
    with pytest.raises(servicio.DominioInvalido):
        servicio.normalizar(entrada)


# ---------------------------------------------------------- la lista


def test_agregar_deja_el_dominio_activo_y_en_orden(db):
    primero = servicio.agregar(db, "viveprop.com", "ViveProp")
    segundo = servicio.agregar(db, "dataprop.cl", "Dataprop")

    assert (primero.codigo, primero.activo, primero.orden) == ("viveprop.com", True, 1)
    assert (segundo.codigo, segundo.orden) == ("dataprop.cl", 2)


def test_agregar_dos_veces_el_mismo_no_lo_duplica(dominios):
    with pytest.raises(servicio.DominioDuplicado):
        servicio.agregar(dominios, "VIVEPROP.com")


def test_agregar_uno_apagado_lo_reactiva(dominios):
    """Sin esto habria que borrarlo para poder volver a agregarlo."""
    fila = servicio.listar(dominios)[0]
    servicio.desactivar(dominios, fila.id)

    revivido = servicio.agregar(dominios, fila.codigo)
    assert revivido.id == fila.id and revivido.activo is True


def test_desactivar_no_borra_la_fila(dominios):
    """La lista es un registro de decisiones: se ve que alguien lo quitó."""
    fila = servicio.listar(dominios)[0]
    servicio.desactivar(dominios, fila.id)

    quedan = servicio.listar(dominios)
    assert len(quedan) == 2
    assert [f.activo for f in quedan if f.id == fila.id] == [False]


def test_desactivar_algo_que_no_es_un_dominio_no_hace_nada(db):
    """Un id equivocado no puede apagar una alianza."""
    alianza = Catalogo(tipo="alianza", codigo="ASSETPLAN", nombre="Assetplan")
    db.add(alianza)
    db.commit()

    assert servicio.desactivar(db, alianza.id) is None
    assert db.get(Catalogo, alianza.id).activo is True


# ------------------------------------------------- de la organizacion o no


@pytest.mark.parametrize("email, adentro", [
    ("felipe@viveprop.com", True),
    ("FELIPE@VIVEPROP.COM", True),
    ("alguien@dataprop.cl", True),
    ("director@gmail.com", False),
    ("raro@viveprop.com.co", False),
    ("sin-arroba", False),
])
def test_quien_es_de_la_organizacion(dominios, email, adentro):
    assert servicio.es_de_la_organizacion(dominios, email) is adentro


def test_un_dominio_apagado_deja_de_ser_de_la_organizacion(dominios):
    fila = next(f for f in servicio.listar(dominios) if f.codigo == "dataprop.cl")
    servicio.desactivar(dominios, fila.id)

    assert servicio.es_de_la_organizacion(dominios, "alguien@dataprop.cl") is False


def test_la_lista_vacia_cierra_no_abre(db):
    """**La propiedad central.**

    La variable de entorno que esto reemplaza hacía lo contrario: vacía
    significaba «sin restricción», así que borrarla por error abría la app a
    cualquier dominio y nadie se enteraba.
    """
    assert servicio.es_de_la_organizacion(db, "felipe@viveprop.com") is False


# --------------------------------------------------------- la API de dominios


def test_solo_admin_administra_los_dominios(cliente_operaciones):
    assert cliente_operaciones.get("/api/admin/dominios").status_code == 403
    assert cliente_operaciones.post("/api/admin/dominios", json={"dominio": "x.cl"}).status_code == 403
    assert cliente_operaciones.delete("/api/admin/dominios/1").status_code == 403


def test_el_endpoint_lista_agrega_y_apaga(cliente, dominios):
    assert [d["dominio"] for d in cliente.get("/api/admin/dominios").json()] == [
        "viveprop.com", "dataprop.cl",
    ]

    r = cliente.post("/api/admin/dominios", json={"dominio": " Gmail.COM ", "nombre": "Externos"})
    assert r.status_code == 201
    assert (r.json()["dominio"], r.json()["nombre"]) == ("gmail.com", "Externos")

    apagado = cliente.delete(f"/api/admin/dominios/{r.json()['id']}")
    assert apagado.status_code == 200 and apagado.json()["activo"] is False


@pytest.mark.parametrize("payload, codigo, trozo", [
    ({"dominio": "viveprop.com"}, 409, "ya está en la lista"),
    ({"dominio": "no-es-dominio"}, 400, "no parece un dominio"),
])
def test_el_endpoint_explica_por_que_no(cliente, dominios, payload, codigo, trozo):
    r = cliente.post("/api/admin/dominios", json=payload)
    assert r.status_code == codigo
    assert trozo in r.json()["detail"]


def test_apagar_un_dominio_no_toca_a_los_usuarios_que_ya_existen(cliente, dominios):
    """La lista se aplica al crear o al cambiar el correo, no re-valida a nadie."""
    creado = cliente.post("/api/admin/usuarios", json={
        "email": "nuevo@dataprop.cl", "nombre": "Nuevo", "password": CLAVE_OK,
    })
    assert creado.status_code == 201

    fila = next(f for f in servicio.listar(dominios) if f.codigo == "dataprop.cl")
    cliente.delete(f"/api/admin/dominios/{fila.id}")

    quedo = next(u for u in cliente.get("/api/admin/usuarios").json() if u["email"] == "nuevo@dataprop.cl")
    assert quedo["activo"] is True
    assert quedo["es_externo"] is False


# ----------------------------------------------- crear usuarios externos


def test_un_correo_de_la_organizacion_no_pide_nada(cliente, dominios):
    r = cliente.post("/api/admin/usuarios", json={
        "email": "nueva@viveprop.com", "nombre": "Nueva", "password": CLAVE_OK,
    })
    assert r.status_code == 201
    assert r.json()["es_externo"] is False
    assert r.json()["externo_autorizado_por"] is None


def test_un_correo_de_fuera_sin_autorizar_se_rechaza(cliente, dominios):
    r = cliente.post("/api/admin/usuarios", json={
        "email": "director@gmail.com", "nombre": "Director", "password": CLAVE_OK,
    })
    assert r.status_code == 400
    assert "no es de la organización" in r.json()["detail"]


def test_un_correo_de_fuera_autorizado_queda_con_nombre_y_fecha(cliente, dominios, db):
    antes = datetime.now(timezone.utc)
    r = cliente.post("/api/admin/usuarios", json={
        "email": "director@gmail.com", "nombre": "Director", "password": CLAVE_OK,
        "rol": "gerencia", "autoriza_externo": True,
    })

    assert r.status_code == 201
    cuerpo = r.json()
    assert cuerpo["es_externo"] is True
    # El nombre del admin de la sesion, no su id: la pantalla no tiene que cruzar.
    assert cuerpo["externo_autorizado_por"] == "Test"
    # Sin zona: la columna es `timestamptz` y en Postgres vuelve con offset, pero
    # SQLite --la base de los tests-- lo pierde. Lo que se prueba es que la fecha
    # sea de ahora, no cómo la serializa cada motor.
    marca = datetime.fromisoformat(cuerpo["externo_autorizado_en"]).replace(tzinfo=None)
    assert marca >= antes.replace(tzinfo=None, microsecond=0)

    guardado = db.scalar(select(Usuario).where(Usuario.email == "director@gmail.com"))
    assert guardado.externo_autorizado_por_id == 1


def test_con_la_lista_vacia_hasta_el_correo_de_la_casa_pide_autorizacion(cliente):
    """El fallo cerrado, visto desde la API."""
    r = cliente.post("/api/admin/usuarios", json={
        "email": "otra@viveprop.com", "nombre": "Otra", "password": CLAVE_OK,
    })
    assert r.status_code == 400

    con_permiso = cliente.post("/api/admin/usuarios", json={
        "email": "otra@viveprop.com", "nombre": "Otra", "password": CLAVE_OK,
        "autoriza_externo": True,
    })
    assert con_permiso.status_code == 201


# ------------------------------------------------- cambiarle el correo


def test_cambiar_el_correo_a_uno_de_fuera_pide_la_misma_autorizacion(cliente, dominios, db):
    creado = cliente.post("/api/admin/usuarios", json={
        "email": "persona@viveprop.com", "nombre": "Persona", "password": CLAVE_OK,
    }).json()

    sin_permiso = cliente.patch(f"/api/admin/usuarios/{creado['id']}", json={"email": "persona@gmail.com"})
    assert sin_permiso.status_code == 400

    con_permiso = cliente.patch(
        f"/api/admin/usuarios/{creado['id']}",
        json={"email": "persona@gmail.com", "autoriza_externo": True},
    )
    assert con_permiso.status_code == 200
    assert con_permiso.json()["es_externo"] is True


def test_volver_a_un_correo_de_la_organizacion_limpia_el_rastro(cliente, dominios):
    """El rastro sigue al correo: el de la organización no necesita autorización."""
    externo = cliente.post("/api/admin/usuarios", json={
        "email": "director@gmail.com", "nombre": "Director", "password": CLAVE_OK,
        "autoriza_externo": True,
    }).json()
    assert externo["es_externo"] is True

    vuelto = cliente.patch(
        f"/api/admin/usuarios/{externo['id']}", json={"email": "director@viveprop.com"}
    )
    assert vuelto.status_code == 200
    assert vuelto.json()["es_externo"] is False
    assert vuelto.json()["externo_autorizado_en"] is None


def test_editar_otra_cosa_no_revisa_el_dominio(cliente, dominios):
    """Cambiarle el rol a un externo no puede exigir autorizar de nuevo."""
    externo = cliente.post("/api/admin/usuarios", json={
        "email": "advisor@gmail.com", "nombre": "Advisor", "password": CLAVE_OK,
        "autoriza_externo": True,
    }).json()

    r = cliente.patch(f"/api/admin/usuarios/{externo['id']}", json={"rol": "gerencia"})
    assert r.status_code == 200
    # Y el rastro sigue ahi: no se toca si el correo no cambia.
    assert r.json()["es_externo"] is True
    assert r.json()["externo_autorizado_por"] == "Test"
