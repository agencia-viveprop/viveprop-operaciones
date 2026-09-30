"""Tests del listado de canjes y sus filtros.

El filtro por **N° de solicitud** es el que motiva este archivo. Busca por
prefijo y no por igualdad: mientras alguien escribe «364», el «3» y el «36»
tienen que mostrar algo, o la pantalla parpadea en vacio y se lee como que el
canje no existe.
"""
from datetime import datetime, timezone

import pytest

from app.models.canje import Canje, CanjeEstado, CanjeEtapa

SOLICITUD = datetime(2026, 8, 1, tzinfo=timezone.utc)


@pytest.fixture
def cartera(db):
    """Numeros elegidos para que el prefijo distinga: 36, 364, 3640 y 401.

    Y los corredores elegidos para el caso que importa: **Jorge aparece como
    solicitante en dos canjes y como propietario en otro.** Si los dos filtros
    miraran la misma columna, o una sola, ese cruce pasaria desapercibido.
    """
    for id_, comuna, tipo_inmueble, estado, solicitante, propietario in (
        (36, "Nunoa", "DEPARTAMENTO", CanjeEstado.ACTIVO, "JORGE ROMAN VIVANCO", "MARIA BELEN COX"),
        (364, "La Florida", "CASA", CanjeEstado.ACTIVO, "JORGE ROMAN VIVANCO", "DATABROKERS"),
        (3640, "Vitacura", "DEPARTAMENTO", CanjeEstado.CANCELADO, "VICENTE FARIAS", "JORGE ROMAN VIVANCO"),
        (401, "Las Condes", "OFICINA", CanjeEstado.ACTIVO, "KAREN ORTIZ DELGADO", None),
    ):
        db.add(Canje(
            id=id_, fecha_solicitud=SOLICITUD, estado=estado,
            etapa=CanjeEtapa.EN_REVISION, comuna=comuna, tipo_inmueble=tipo_inmueble,
            corredor_solicitante_nombre=solicitante,
            corredor_propietario_nombre=propietario,
        ))
    db.commit()
    return db


def _numeros(cliente, **params):
    r = cliente.get("/api/canjes", params=params)
    assert r.status_code == 200, r.text
    return sorted(c["id"] for c in r.json())


def test_sin_filtro_vienen_todos(cliente, cartera):
    assert _numeros(cliente) == [36, 364, 401, 3640]


def test_el_numero_completo_trae_ese_canje(cliente, cartera):
    assert _numeros(cliente, numero="401") == [401]


def test_el_numero_incompleto_busca_por_prefijo(cliente, cartera):
    """Lo que hace que escribir no pase por un vacio intermedio."""
    assert _numeros(cliente, numero="36") == [36, 364, 3640]
    assert _numeros(cliente, numero="364") == [364, 3640]


def test_el_prefijo_no_es_una_busqueda_en_cualquier_posicion(cliente, cartera):
    """«64» no puede traer el 364: en un numero, el prefijo es lo que se recuerda."""
    assert _numeros(cliente, numero="64") == []


def test_se_puede_pegar_la_referencia_con_gato(cliente, cartera):
    """La app escribe las referencias como «#364» en los reportes."""
    assert _numeros(cliente, numero="#364") == [364, 3640]


def test_una_entrada_sin_digitos_no_filtra_nada(cliente, cartera):
    """Mejor mostrar todo que una lista vacia sin explicacion."""
    assert _numeros(cliente, numero="abc") == [36, 364, 401, 3640]


def test_el_numero_se_combina_con_los_otros_filtros(cliente, cartera):
    """Los filtros se suman: si no, elegir dos daria mas resultados que uno."""
    assert _numeros(cliente, numero="36", estado="ACTIVO") == [36, 364]
    assert _numeros(cliente, numero="36", comuna="florida") == [364]


# ------------------------------------------------------- orden del listado


def test_el_listado_viene_del_mas_nuevo_al_mas_antiguo(cliente, cartera):
    """El caso real: dos canjes del mismo día aparecían en cualquier orden.

    Los cuatro canjes de `cartera` comparten la misma `fecha_solicitud`, así
    que ordenar solo por fecha los deja empatados y Postgres puede devolverlos
    en el orden que le convenga --no necesariamente el de llegada--. El N° de
    solicitud desempata: crece con el tiempo, igual que la fecha, así que el
    más nuevo tiene que quedar primero.
    """
    r = cliente.get("/api/canjes")
    assert r.status_code == 200, r.text
    assert [c["id"] for c in r.json()] == [3640, 401, 364, 36]


# ------------------------------------------------- filtros por corredor


def test_el_filtro_de_solicitante_no_trae_los_canjes_donde_es_propietario(cliente, cartera):
    """**El caso que justifica que sean dos filtros y no uno.**

    Jorge pide dos canjes y es el propietario de un tercero. Preguntar "con quien
    estoy trabajando" y "de quien es la propiedad" son dos preguntas, y un filtro
    unico sobre "el corredor" las mezclaria sin avisar.
    """
    assert _numeros(cliente, solicitante="JORGE ROMAN VIVANCO") == [36, 364]
    assert _numeros(cliente, propietario="JORGE ROMAN VIVANCO") == [3640]


def test_el_corredor_se_busca_por_parte_del_nombre_y_sin_importar_mayusculas(cliente, cartera):
    """Nadie escribe «JORGE ROMAN VIVANCO» completo para filtrar."""
    assert _numeros(cliente, solicitante="jorge") == [36, 364]
    assert _numeros(cliente, solicitante="roman") == [36, 364]
    assert _numeros(cliente, propietario="databrokers") == [364]


def test_los_filtros_de_corredor_se_combinan_con_el_resto(cliente, cartera):
    assert _numeros(cliente, solicitante="jorge", estado="ACTIVO") == [36, 364]
    assert _numeros(cliente, solicitante="jorge", propietario="databrokers") == [364]
    assert _numeros(cliente, solicitante="jorge", numero="364") == [364]


def test_un_corredor_que_no_existe_no_trae_nada(cliente, cartera):
    """Un filtro que no encuentra tiene que devolver vacio, no todo."""
    assert _numeros(cliente, solicitante="nadie") == []


# --------------------------------------------- las sugerencias de los filtros


def test_las_opciones_vienen_por_filtro_distintas_y_ordenadas(cliente, cartera):
    r = cliente.get("/api/canjes/filtros")

    assert r.status_code == 200, r.text
    cuerpo = r.json()
    # Jorge aparece en las dos listas porque cumple los dos roles, y una sola vez
    # en la de solicitantes aunque pida dos canjes.
    assert cuerpo["solicitantes"] == ["JORGE ROMAN VIVANCO", "KAREN ORTIZ DELGADO", "VICENTE FARIAS"]
    assert cuerpo["propietarios"] == ["DATABROKERS", "JORGE ROMAN VIVANCO", "MARIA BELEN COX"]


def test_las_sugerencias_no_traen_vacios(cliente, cartera):
    """El canje 401 no tiene propietario: eso no puede aparecer como una opcion."""
    propietarios = cliente.get("/api/canjes/filtros").json()["propietarios"]

    assert all(p for p in propietarios)
    assert len(propietarios) == 3


def test_las_comunas_tambien_se_sugieren(cliente, cartera):
    """El filtro de comuna ya aceptaba texto libre; lo que le faltaba era la lista.

    Con 43 comunas en los datos, escribir de memoria obliga a acertar como esta
    escrita cada una.
    """
    comunas = cliente.get("/api/canjes/filtros").json()["comunas"]

    assert comunas == ["La Florida", "Las Condes", "Nunoa", "Vitacura"]


def test_los_tipos_de_inmueble_tambien_se_sugieren(cliente, cartera):
    """A diferencia de las comunas, los 9 tipos de Dataprop se sugieren siempre
    --incluidos BODEGA, CASA EN CONDOMINIO, INDUSTRIAL, LOCAL COMERCIAL,
    PARCELA y TERRENO - SITIO, que ningun canje de la cartera de prueba usa--,
    ver test_un_tipo_de_inmueble_sin_ningun_canje_igual_se_sugiere.
    """
    tipos = cliente.get("/api/canjes/filtros").json()["tipos_inmueble"]

    assert tipos == [
        "BODEGA", "CASA", "CASA EN CONDOMINIO", "DEPARTAMENTO", "INDUSTRIAL",
        "LOCAL COMERCIAL", "OFICINA", "PARCELA", "TERRENO - SITIO",
    ]


def test_un_tipo_de_inmueble_sin_ningun_canje_igual_se_sugiere(cliente, db):
    """El caso que motiva la base fija: un tipo poco frecuente puede no tener
    ningun canje cargado todavia y necesita sugerirse igual al crear uno nuevo.
    """
    tipos = cliente.get("/api/canjes/filtros").json()["tipos_inmueble"]

    assert "OFICINA" in tipos
    assert "BODEGA" in tipos
    assert "INDUSTRIAL" in tipos


def test_un_tipo_de_inmueble_nuevo_se_suma_a_la_base_fija(cliente, db):
    """La base fija no reemplaza lo real: un valor cargado que no esta en la
    base --un tipo nuevo o una variante-- se sigue sumando."""
    db.add(Canje(
        id=9001, fecha_solicitud=SOLICITUD, estado=CanjeEstado.ACTIVO,
        etapa=CanjeEtapa.EN_REVISION, tipo_inmueble="ESTACIONAMIENTO",
    ))
    db.commit()

    tipos = cliente.get("/api/canjes/filtros").json()["tipos_inmueble"]

    assert "ESTACIONAMIENTO" in tipos
    assert "OFICINA" in tipos


def test_las_sugerencias_no_dependen_de_los_filtros(cliente, cartera):
    """**La razon por la que esto es un endpoint aparte.**

    Si la lista saliera del listado ya filtrado, elegir un corredor haria
    desaparecer al resto de las opciones y para cambiar de corredor habria que
    limpiar el filtro primero.
    """
    entero = cliente.get("/api/canjes/filtros").json()

    filtrado = cliente.get("/api/canjes/filtros", params={"solicitante": "jorge"}).json()

    assert filtrado == entero
