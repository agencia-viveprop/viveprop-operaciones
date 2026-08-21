"""Tests de la descarga automática de UF desde el SII (sprint 23).

Corren contra `datos/sii_uf_2026.html`, un recorte real de la página bajado el
2026-08-21. **Ningún test sale a internet**: uno que dependa de la red falla el
día que el SII se cae, y ahí deja de ser una señal y pasa a ser ruido.

Las dos propiedades que protegen:

1. **Si el parseo falla no se escribe nada.** Una página con otro formato tiene
   que reventar, no cargar media serie: nadie sabría cuál mitad quedó.
2. **El cambio de año se consulta de los dos lados.** En diciembre hace falta la
   página del año siguiente, y en enero la del anterior. Sin eso la
   automatización anda once meses y falla justo cuando el mes nuevo importa.
"""
from datetime import date
from decimal import Decimal as D
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.uf import UFDiaria
from app.services.uf_sii import (
    ANIO_MINIMO,
    MINIMO_FECHAS,
    SIINoDisponible,
    actualizar_desde_sii,
    anios_a_consultar,
    cargar_historia,
    parsear,
)

DATOS = Path(__file__).parent / "datos"
HOY = date(2026, 8, 21)


@pytest.fixture
def html_sii() -> str:
    return (DATOS / "sii_uf_2026.html").read_text(encoding="latin-1")


@pytest.fixture
def descargador(html_sii):
    """Devuelve la página guardada para 2026 y 404 para cualquier otro año."""
    def _descargar(anio: int):
        return html_sii if anio == 2026 else None
    return _descargar


# ------------------------------------------------------------------ parseo


def test_parsea_la_serie_completa_del_anio(html_sii):
    serie = parsear(html_sii, 2026)

    assert len(serie) == 252
    assert min(serie) == date(2026, 1, 1)
    # El SII publica hasta el 9 del mes siguiente: eso es lo que hace útil esto.
    assert max(serie) == date(2026, 9, 9)


def test_no_deja_huecos_en_el_rango(html_sii):
    serie = parsear(html_sii, 2026)
    dias = (max(serie) - min(serie)).days + 1

    assert len(serie) == dias


@pytest.mark.parametrize("fecha, esperado", [
    # Valores reales, verificados contra la serie que venía del Excel.
    (date(2026, 1, 2), D("39735.63")),
    (date(2026, 6, 1), D("40627.62")),
    (date(2026, 8, 20), D("40859.28")),
    (date(2026, 9, 9), D("40885.63")),
])
def test_los_valores_son_los_correctos(html_sii, fecha, esperado):
    """El formato chileno `40.859,28` tiene que llegar como 40859.28."""
    assert parsear(html_sii, 2026)[fecha] == esperado


def test_no_inventa_dias_que_el_mes_no_tiene(html_sii):
    """La grilla del SII es de 31 filas y los meses cortos traen celdas vacías.

    Febrero de 2026 tiene 28 días, así que un 29 ni se puede construir como
    fecha: el parser lo descarta al intentarlo. Se cuenta el mes completo en vez
    de nombrar el día inexistente, que es lo que hacía fallar a este test.
    """
    serie = parsear(html_sii, 2026)

    assert len([f for f in serie if f.month == 2]) == 28
    assert date(2026, 2, 28) in serie
    assert len([f for f in serie if f.month == 4]) == 30  # abril tiene 30


def test_los_meses_sin_publicar_no_aparecen(html_sii):
    """Octubre en adelante está vacío en la página de agosto."""
    serie = parsear(html_sii, 2026)

    assert not [f for f in serie if f.month > 9]


# ------------------------------------------------ el parseo falla ruidoso


def test_una_pagina_sin_la_tabla_es_un_error():
    with pytest.raises(SIINoDisponible, match="table_export"):
        parsear("<html><body><p>El sitio está en mantención</p></body></html>", 2026)


def test_una_tabla_con_muy_pocas_fechas_es_un_error():
    """Media docena de valores es una página que no se entendió, no un año corto."""
    filas = "".join(f"<tr><td>{d}</td><td>40.000,00</td></tr>" for d in range(1, 5))
    html = f'<table id="table_export">{filas}</table>'

    with pytest.raises(SIINoDisponible, match=str(MINIMO_FECHAS)):
        parsear(html, 2026)


def test_si_el_parseo_falla_no_se_escribe_nada(db):
    """La regla de la carga manual: media serie es peor que ninguna."""
    def roto(_anio):
        return "<html>otra cosa</html>"

    with pytest.raises(SIINoDisponible):
        actualizar_desde_sii(db, HOY, descargador=roto)

    assert db.execute(select(UFDiaria)).first() is None


def test_si_el_sii_no_tiene_ninguna_pagina_es_un_error(db):
    with pytest.raises(SIINoDisponible, match="ninguna"):
        actualizar_desde_sii(db, HOY, descargador=lambda _a: None)


# ------------------------------------------------------- años a consultar


@pytest.mark.parametrize("hoy, esperado", [
    (date(2026, 8, 21), [2026]),
    (date(2026, 3, 1), [2026]),
    # En diciembre la UF de enero ya está publicada, en la página del año que viene.
    (date(2026, 12, 1), [2026, 2027]),
    (date(2026, 12, 31), [2026, 2027]),
    # En enero, el año anterior por si diciembre quedó con un hueco.
    (date(2027, 1, 1), [2026, 2027]),
    (date(2027, 1, 31), [2026, 2027]),
])
def test_el_cambio_de_anio_se_consulta_de_los_dos_lados(hoy, esperado):
    assert anios_a_consultar(hoy) == esperado


def test_el_404_del_anio_futuro_no_aborta_la_carga(db, html_sii):
    """En diciembre la página del año siguiente puede no existir todavía."""
    def _descargar(anio):
        return html_sii if anio == 2026 else None

    resumen = actualizar_desde_sii(db, date(2026, 12, 15), descargador=_descargar)

    assert resumen.anios == [2026]
    assert resumen.carga.nuevas == 252


# ------------------------------------------------------------- escritura


def test_la_primera_carga_trae_todo(db, descargador):
    resumen = actualizar_desde_sii(db, HOY, descargador=descargador)

    assert resumen.fechas_leidas == 252
    assert (resumen.carga.nuevas, resumen.carga.actualizadas, resumen.carga.sin_cambio) == (252, 0, 0)
    assert resumen.ultima == date(2026, 9, 9)
    assert db.execute(select(UFDiaria)).scalars().all().__len__() == 252


def test_correrla_dos_veces_no_cambia_nada(db, descargador):
    """Tiene que ser idempotente: la tarea de fondo puede repetirse."""
    actualizar_desde_sii(db, HOY, descargador=descargador)
    segunda = actualizar_desde_sii(db, HOY, descargador=descargador)

    assert (segunda.carga.nuevas, segunda.carga.actualizadas) == (0, 0)
    assert segunda.carga.sin_cambio == 252


def test_un_valor_distinto_se_actualiza_y_se_informa(db, descargador):
    """El SII corrige un valor: se sobreescribe y queda dicho, no en silencio."""
    db.add(UFDiaria(fecha=date(2026, 6, 1), valor=D("1.00")))
    db.commit()

    resumen = actualizar_desde_sii(db, HOY, descargador=descargador)

    assert resumen.carga.actualizadas == 1
    assert resumen.carga.nuevas == 251
    guardado = db.execute(
        select(UFDiaria.valor).where(UFDiaria.fecha == date(2026, 6, 1))
    ).scalar_one()
    assert D(guardado) == D("40627.62")


# -------------------------------------------------------------- endpoint


def test_el_endpoint_actualiza(cliente, db, monkeypatch, descargador):
    import app.routers.uf as router

    monkeypatch.setattr(router, "actualizar_desde_sii",
                        lambda db_, hoy: actualizar_desde_sii(db_, HOY, descargador=descargador))
    r = cliente.post("/api/uf/actualizar-desde-sii")

    assert r.status_code == 200
    assert r.json()["carga"]["nuevas"] == 252


def test_el_endpoint_da_502_cuando_el_sii_no_responde(cliente, monkeypatch):
    """502 y no 500: la falla es de un tercero y la salida es la carga manual."""
    import app.routers.uf as router

    def explotar(*_a, **_k):
        raise SIINoDisponible("El SII respondió 503 para 2026.")

    monkeypatch.setattr(router, "actualizar_desde_sii", explotar)
    r = cliente.post("/api/uf/actualizar-desde-sii")

    assert r.status_code == 502
    assert "503" in r.json()["detail"]


# ----------------------------------------------------------- tarea de fondo


def test_la_tarea_no_descarga_si_la_serie_tiene_colchon(db, monkeypatch):
    """No pide la página del SII todos los días para nada."""
    from app import tareas

    # Serie que llega muy adelante: no hace falta actualizar.
    db.add(UFDiaria(fecha=date(2026, 12, 31), valor=D("41000.00")))
    db.commit()

    llamadas = []
    monkeypatch.setattr(tareas, "SessionLocal", lambda: _sesion_falsa(db))
    monkeypatch.setattr(tareas, "actualizar_desde_sii",
                        lambda *a, **k: llamadas.append(1))
    monkeypatch.setattr(tareas, "datetime", _reloj(date(2026, 8, 21)))

    tareas.actualizar_uf_si_hace_falta()
    assert llamadas == []


def test_la_tarea_descarga_cuando_la_serie_se_acaba(db, monkeypatch):
    from app import tareas

    db.add(UFDiaria(fecha=date(2026, 8, 25), valor=D("40900.00")))
    db.commit()

    llamadas = []
    monkeypatch.setattr(tareas, "SessionLocal", lambda: _sesion_falsa(db))
    monkeypatch.setattr(tareas, "actualizar_desde_sii",
                        lambda *a, **k: llamadas.append(1) or _resumen_vacio())
    monkeypatch.setattr(tareas, "datetime", _reloj(date(2026, 8, 21)))

    tareas.actualizar_uf_si_hace_falta()
    assert llamadas == [1]


def test_la_tarea_no_propaga_la_falla_del_sii(db, monkeypatch):
    """Si tumbara el ciclo, la app quedaría sin actualización para siempre."""
    from app import tareas

    def explotar(*_a, **_k):
        raise SIINoDisponible("timeout")

    monkeypatch.setattr(tareas, "SessionLocal", lambda: _sesion_falsa(db))
    monkeypatch.setattr(tareas, "actualizar_desde_sii", explotar)
    monkeypatch.setattr(tareas, "datetime", _reloj(date(2026, 8, 21)))

    tareas.actualizar_uf_si_hace_falta()  # no debe levantar nada


# ------------------------------------------------------------- utilidades


def _sesion_falsa(db):
    """Envuelve la sesión de test para que sobreviva al `with` de la tarea."""
    class _Ctx:
        def __enter__(self_):
            return db

        def __exit__(self_, *_a):
            return False

    return _Ctx()


def _reloj(hoy: date):
    class _DT:
        @staticmethod
        def now(_tz=None):
            class _Ahora:
                @staticmethod
                def date():
                    return hoy
            return _Ahora()

    return _DT


def _resumen_vacio():
    from app.services.importar_uf import ResumenCargaUF
    from app.services.uf_sii import ResumenSII

    return ResumenSII(anios=[2026], fechas_leidas=0, carga=ResumenCargaUF(), ultima=None)


# ------------------------------------------------------ carga de historia
#
# Existe por el caso de produccion: la tabla estaba vacia y la actualizacion
# diaria solo cubre el anio en curso, asi que habria quedado con 2026 y sin
# 2022-2025 -- alcanza para valorizar hoy, no para un negocio del anio pasado.


@pytest.fixture
def descargador_varios_anios(html_sii):
    """Devuelve la misma pagina para 2022..2026 y 404 para el resto.

    Sirve igual para verificar el recorrido de anios: cada anio se parsea con su
    propio numero, asi que las fechas resultantes son distintas aunque el HTML
    sea el mismo.
    """
    def _descargar(anio: int):
        return html_sii if 2022 <= anio <= 2026 else None
    return _descargar


def test_la_historia_recorre_todos_los_anios(db, descargador_varios_anios):
    resumen = cargar_historia(db, HOY, descargador=descargador_varios_anios)

    assert resumen.anios == [2022, 2023, 2024, 2025, 2026]
    assert resumen.anios_sin_pagina == []
    # 252 fechas por anio, cada una con su propio anio: no se pisan entre si.
    assert resumen.fechas_leidas == 252 * 5
    assert resumen.carga.nuevas == 252 * 5


def test_trae_anios_completos_incluido_lo_previo_al_primer_canje(db, descargador_varios_anios):
    """La carga original arrancaba en 2022-11 y dejaba fuera enero a octubre.

    Traer el anio entero es mas simple que un corte a mitad de anio y evita que
    un negocio con fecha de mediados de 2022 se quede sin poder valorizarse.
    """
    cargar_historia(db, HOY, descargador=descargador_varios_anios)

    guardadas = db.execute(select(UFDiaria.fecha)).scalars().all()
    assert date(2022, 1, 2) in guardadas
    assert min(guardadas).year == ANIO_MINIMO


def test_un_anio_sin_pagina_no_aborta_el_resto(db, html_sii):
    """2024 caido no puede impedir que se carguen los otros cuatro."""
    def _descargar(anio):
        return None if anio == 2024 else html_sii

    resumen = cargar_historia(db, HOY, descargador=_descargar)

    assert resumen.anios == [2022, 2023, 2025, 2026]
    assert resumen.anios_sin_pagina == [2024]
    assert resumen.carga.nuevas == 252 * 4


def test_si_no_se_pudo_leer_ningun_anio_es_un_error(db):
    """Distinto de "el SII no publico 2027": esto se arregla distinto."""
    with pytest.raises(SIINoDisponible, match="ninguna"):
        cargar_historia(db, HOY, descargador=lambda _a: None)


def test_un_anio_roto_no_deja_media_historia_cargada(db, html_sii):
    """El parseo entero termina antes de que se toque la base."""
    def _descargar(anio):
        return html_sii if anio < 2025 else "<html>otra cosa</html>"

    with pytest.raises(SIINoDisponible):
        cargar_historia(db, HOY, descargador=_descargar)

    assert db.execute(select(UFDiaria)).first() is None


@pytest.mark.parametrize("desde, hasta, trozo", [
    (2021, None, str(ANIO_MINIMO)),
    (2026, 2025, "anterior"),
])
def test_rechaza_rangos_imposibles(db, desde, hasta, trozo, descargador_varios_anios):
    with pytest.raises(ValueError, match=trozo):
        cargar_historia(db, HOY, desde, hasta, descargador=descargador_varios_anios)


def test_la_historia_tambien_es_idempotente(db, descargador_varios_anios):
    cargar_historia(db, HOY, descargador=descargador_varios_anios)
    segunda = cargar_historia(db, HOY, descargador=descargador_varios_anios)

    assert (segunda.carga.nuevas, segunda.carga.actualizadas) == (0, 0)
    assert segunda.carga.sin_cambio == 252 * 5


def test_el_endpoint_de_historia_responde(cliente, monkeypatch, descargador_varios_anios):
    import app.routers.uf as router

    monkeypatch.setattr(
        router, "cargar_historia",
        lambda db_, hoy, d=None, h=None: cargar_historia(db_, HOY, descargador=descargador_varios_anios),
    )
    r = cliente.post("/api/uf/cargar-historia")

    assert r.status_code == 200
    assert r.json()["anios"] == [2022, 2023, 2024, 2025, 2026]


def test_el_endpoint_de_historia_rechaza_un_anio_muy_viejo(cliente):
    """Lo ataja la validacion de FastAPI, antes de llegar al servicio."""
    r = cliente.post("/api/uf/cargar-historia", params={"desde_anio": 1990})

    assert r.status_code == 422
