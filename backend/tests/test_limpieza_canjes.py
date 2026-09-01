"""Borrado definitivo de canjes antiguos, y el corte que evita que vuelvan.

El test que da sentido al archivo es
`test_la_importacion_no_repone_lo_que_el_corte_dejo_fuera`: sin esa guarda el
borrado dura hasta la próxima carga del export de Dataprop, porque el importador
crea cualquier canje cuyo ID no esté en la base. Borrar sin ese corte es trabajo
que se deshace solo.
"""
from datetime import date, datetime, timezone

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.catalogo import Catalogo
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.obligacion import Obligacion, TipoObligacion
from app.models.usuario import RolUsuario, Usuario
from app.services.limpieza_canjes import (
    CORTE_HISTORICO,
    borrar_canje,
    canjes_anteriores_al_corte,
    es_anterior_al_corte,
)


def _instante(iso: str) -> datetime:
    return datetime.fromisoformat(iso).replace(tzinfo=timezone.utc)


@pytest.fixture
def cartera(db):
    """Cuatro canjes alrededor del corte, uno sin fecha de solicitud."""
    filas = [
        Canje(id=1, fecha_solicitud=_instante("2023-04-10"), estado=CanjeEstado.CANCELADO,
              etapa=CanjeEtapa.EN_REVISION, comuna="Nunoa"),
        Canje(id=2, fecha_solicitud=_instante("2025-05-31"), estado=CanjeEstado.CANCELADO,
              etapa=CanjeEtapa.EN_OFERTA, comuna="Santiago"),
        Canje(id=3, fecha_solicitud=_instante("2025-06-01"), estado=CanjeEstado.ACTIVO,
              etapa=CanjeEtapa.EN_REVISION, comuna="Las Condes"),
        Canje(id=4, fecha_solicitud=_instante("2026-08-01"), estado=CanjeEstado.ACTIVO,
              etapa=CanjeEtapa.EN_NEGOCIO, comuna="Providencia"),
    ]
    db.add_all(filas)
    db.commit()
    return filas


# ------------------------------------------------------------------ el corte


def test_el_corte_mira_la_solicitud_y_usa_la_creacion_de_respaldo():
    """«Fecha de solicitud o creación», como lo pidió el usuario.

    El respaldo cubre un canje cargado a mano sin fecha de solicitud: sin él, un
    nulo lo salvaría del corte por accidente.
    """
    assert es_anterior_al_corte(_instante("2025-05-31"), None) is True
    assert es_anterior_al_corte(_instante("2025-06-01"), None) is False
    # Sin solicitud manda la creación.
    assert es_anterior_al_corte(None, _instante("2024-01-01")) is True
    assert es_anterior_al_corte(None, _instante("2026-01-01")) is False
    # Y la solicitud le gana a la creación cuando las dos están.
    assert es_anterior_al_corte(_instante("2026-01-01"), _instante("2024-01-01")) is False


def test_sin_ninguna_de_las_dos_fechas_el_canje_no_cae():
    """Nulo en las dos es «no se sabe cuándo», y eso no autoriza a borrarlo."""
    assert es_anterior_al_corte(None, None) is False


def test_el_corte_por_defecto_es_junio_de_2025():
    """Está fijado porque es una política, no un parámetro de una corrida: la
    importación usa el mismo valor para no reponer lo borrado."""
    assert CORTE_HISTORICO == date(2025, 6, 1)


def test_la_consulta_trae_solo_los_anteriores_al_corte(db, cartera):
    ids = [c.id for c in canjes_anteriores_al_corte(db)]

    assert ids == [1, 2]


def test_el_corte_se_puede_correr_para_una_limpieza_puntual(db, cartera):
    ids = [c.id for c in canjes_anteriores_al_corte(db, date(2024, 1, 1))]

    assert ids == [1]


# ------------------------------------------------------------- lo que se lleva


def test_borrar_un_canje_se_lleva_sus_movimientos_y_sus_obligaciones(db, cartera):
    """**Los movimientos hay que borrarlos a mano.**

    `obligaciones.canje_id` tiene clave foránea con `ON DELETE CASCADE`, así que
    esas se van solas. `movimientos` no tiene clave foránea --usa `entity_type` +
    `entity_id` (`D-002`)-- así que la base no puede limpiarlos y quedarían
    huérfanos apuntando a un canje que ya no existe, con el reporte semanal
    contándolos en «Se cayó».
    """
    db.add(TipoMovimiento(codigo="CANCELACION", nombre="Cancelación", entity_type=EntityType.canje))
    estado = Catalogo(tipo="estado_facturacion", codigo="POR_FACTURAR", nombre="Por Facturar")
    db.add(estado)
    db.commit()
    db.add_all([
        Movimiento(entity_type=EntityType.canje, entity_id=1, tipo_movimiento="CANCELACION",
                   fecha=_instante("2023-05-01")),
        Movimiento(entity_type=EntityType.canje, entity_id=1, tipo_movimiento="CANCELACION",
                   fecha=_instante("2023-05-02")),
        # De otro canje: no se tiene que ir.
        Movimiento(entity_type=EntityType.canje, entity_id=4, tipo_movimiento="CANCELACION",
                   fecha=_instante("2026-08-02")),
    ])
    db.add(Obligacion(canje_id=1, tipo=TipoObligacion.FACT_CORREDOR_SOLICITANTE,
                      estado_id=estado.id))
    db.commit()

    movimientos, obligaciones = borrar_canje(db, db.get(Canje, 1))
    db.commit()

    assert (movimientos, obligaciones) == (2, 1)
    assert db.get(Canje, 1) is None
    quedan = db.query(Movimiento).filter_by(entity_type=EntityType.canje).all()
    assert [m.entity_id for m in quedan] == [4], "no toca los movimientos de otros canjes"
    assert db.query(Obligacion).count() == 0


# ------------------------------------------------------------------ el endpoint


def test_el_endpoint_borra_el_canje(cliente, cartera):
    r = cliente.delete("/api/canjes/1")

    assert r.status_code == 204
    assert cliente.get("/api/canjes/1").status_code == 404


def test_borrar_un_canje_que_no_existe_es_404(cliente, cartera):
    assert cliente.delete("/api/canjes/999").status_code == 404


def test_solo_un_admin_puede_borrar(db, cartera):
    """Es la única operación de la app que destruye datos sin dejar rastro.

    Cancelar deja el canje con su línea de tiempo; esto lo saca de la base. El rol
    más alto es la guarda barata para algo que no tiene deshacer.
    """
    from fastapi.testclient import TestClient

    from app.auth import get_current_user
    from app.config import settings
    from app.db import get_db
    from app.main import app

    settings.tareas_de_fondo = False
    operaciones = Usuario(
        id=9, email="opera@viveprop.com", nombre="Opera", password_hash="x",
        rol=RolUsuario.operaciones,
    )
    db.add(operaciones)
    db.commit()
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: operaciones
    try:
        with TestClient(app) as c:
            assert c.delete("/api/canjes/1").status_code == 403
    finally:
        app.dependency_overrides.clear()

    assert db.get(Canje, 1) is not None
