"""Descarga la serie de UF desde el SII, para no tener que cargarla a mano.

**Por qué el SII y no las otras dos fuentes.** Se verificó el 2026-08-21 contra
la serie que ya estaba en Neon —que viene del Excel, o sea un origen
independiente— y coincidió en **617 fechas de 617, al centavo**, entre 2025 y
2026. `mindicador.cl` no respondió en dos intentos y no se puede construir sobre
una fuente que no se pudo verificar. El Banco Central es la fuente de origen y
tiene API JSON de verdad, más robusta que parsear HTML, pero exige registrarse y
guardar credenciales; queda como el camino de mejora si esto se vuelve frágil.

**El SII publica hacia adelante.** La UF se fija del 10 de un mes al 9 del
siguiente, así que su página siempre llega más lejos que hoy. Eso es lo que hace
que esto sirva: al chequear a fin de mes ya está el mes que viene.

**Una página por año, y la del año que viene no existe hasta que existe.** En la
segunda mitad de diciembre los valores de enero están en la página del año
siguiente, que hasta entonces devuelve 404. Por eso `anios_a_consultar` pide dos
años cerca del cambio y el 404 de la futura no es un error. Sin eso la
automatización andaría once meses y fallaría exactamente cuando más se necesita.

**Si el parseo falla no se escribe nada.** Es la misma regla de la carga manual:
media serie cargada es peor que ninguna, porque nadie sabe cuál mitad. Y la
escritura pasa por `guardar_serie`, el mismo upsert que usa la plantilla.
"""
import re
from datetime import date
from decimal import Decimal, InvalidOperation

import httpx
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.services.importar_uf import ResumenCargaUF, guardar_serie

URL = "https://www.sii.cl/valores_y_fechas/uf/uf{anio}.htm"

# El SII sirve la página en latin-1 y no siempre lo declara bien en la cabecera.
CODIFICACION = "latin-1"
TIMEOUT = 20.0

# La tabla que interesa es la única con este id: día en la primera columna, los
# doce meses en las siguientes. Las otras nueve tablas de la página son la misma
# información repartida en bloques de tres columnas por mes, más incómoda.
ID_TABLA = "table_export"

_TABLA = re.compile(rf'<table[^>]*id="{ID_TABLA}".*?</table>', re.S)
_FILA = re.compile(r"<tr.*?</tr>", re.S)
_CELDA = re.compile(r"<t[dh].*?</t[dh]>", re.S)
_ETIQUETA = re.compile(r"<[^>]+>")
_NUMERO = re.compile(r"[\d.]+,\d+")

# Un año con menos fechas que esto es una página que no se entendió, no un año
# corto. Cubre el caso de enero, donde legítimamente hay pocas.
MINIMO_FECHAS = 20


class ResumenSII(BaseModel):
    anios: list[int]
    fechas_leidas: int
    carga: ResumenCargaUF
    ultima: date | None


class SIINoDisponible(Exception):
    """El SII no respondió, o respondió algo que no se pudo entender."""


def anios_a_consultar(hoy: date) -> list[int]:
    """El año en curso, y el vecino cuando el cambio de año está cerca.

    **En diciembre, también el siguiente**: la UF de enero se publica alrededor
    del 9 de diciembre y vive en la página del año que viene.

    **En enero, también el anterior**: si esto no corrió por unos días sobre el
    cambio de año, diciembre quedaría con un hueco que la página del año nuevo
    no cubre. Y un hueco en el medio de la serie no lo avisa nadie -- el aviso
    de vencimiento mira la última fecha, no los agujeros.
    """
    if hoy.month == 12:
        return [hoy.year, hoy.year + 1]
    if hoy.month == 1:
        return [hoy.year - 1, hoy.year]
    return [hoy.year]


def descargar(anio: int) -> str | None:
    """El HTML del año, o `None` si el SII todavía no publicó esa página.

    Distingue las dos cosas a propósito: un 404 en el año futuro es normal y no
    debe abortar la actualización; cualquier otra falla sí es un problema.
    """
    try:
        respuesta = httpx.get(URL.format(anio=anio), timeout=TIMEOUT, follow_redirects=True)
    except httpx.HTTPError as exc:
        raise SIINoDisponible(f"No se pudo consultar el SII para {anio}: {exc}") from exc

    if respuesta.status_code == 404:
        return None
    if respuesta.status_code != 200:
        raise SIINoDisponible(f"El SII respondió {respuesta.status_code} para {anio}.")
    return respuesta.content.decode(CODIFICACION, errors="replace")


def parsear(html: str, anio: int) -> dict[date, Decimal]:
    """Saca la serie del año de la tabla de la página.

    Falla ruidoso si la página cambió de forma. Es la diferencia entre enterarse
    y quedarse con la serie congelada sin que nadie lo note.
    """
    tabla = _TABLA.search(html)
    if tabla is None:
        raise SIINoDisponible(
            f"La página del SII de {anio} no trae la tabla '{ID_TABLA}'. "
            "Probablemente cambió el formato: hay que revisar el parser."
        )

    serie: dict[date, Decimal] = {}
    for fila in _FILA.findall(tabla.group(0)):
        celdas = [
            _ETIQUETA.sub("", c).replace("&nbsp;", "").strip()
            for c in _CELDA.findall(fila)
        ]
        if not celdas or not celdas[0].isdigit():
            continue  # encabezado
        dia = int(celdas[0])
        for mes, bruto in enumerate(celdas[1:13], start=1):
            if not bruto or not _NUMERO.fullmatch(bruto):
                continue  # celda vacía: día que ese mes no tiene, o mes sin publicar
            try:
                # Formato chileno: 40.859,28
                valor = Decimal(bruto.replace(".", "").replace(",", "."))
                serie[date(anio, mes, dia)] = valor
            except (InvalidOperation, ValueError):
                # Un 31 de febrero de la grilla, o un número que no se entiende.
                continue

    if len(serie) < MINIMO_FECHAS:
        raise SIINoDisponible(
            f"Solo se entendieron {len(serie)} fechas en la página de {anio}. "
            "Se esperaban muchas más: hay que revisar el parser."
        )
    return serie


def actualizar_desde_sii(db: Session, hoy: date, descargador=descargar) -> ResumenSII:
    """Trae lo que el SII publica y lo guarda, sin escribir nada si algo falla.

    El descargador entra por parámetro para que los tests corran contra un HTML
    guardado: un test que sale a internet falla el día que el SII se cae, y eso
    lo convierte en ruido en vez de en una señal.
    """
    serie: dict[date, Decimal] = {}
    anios_leidos: list[int] = []

    for anio in anios_a_consultar(hoy):
        html = descargador(anio)
        if html is None:
            continue  # el SII todavía no publicó ese año
        serie.update(parsear(html, anio))
        anios_leidos.append(anio)

    if not anios_leidos:
        raise SIINoDisponible("El SII no tiene publicada ninguna de las páginas consultadas.")

    # El parseo ya terminó bien: recién acá se toca la base.
    carga = guardar_serie(db, serie)
    return ResumenSII(
        anios=anios_leidos,
        fechas_leidas=len(serie),
        carga=carga,
        ultima=max(serie) if serie else None,
    )
