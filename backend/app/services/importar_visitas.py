from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO

import openpyxl
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.visita import Visita

# Los mismos encabezados que trae la consola de administración.
COLUMNAS_REQUERIDAS = [
    "Propiedad",
    "Dirección",
    "Tipo",
    "Mercado",
    "Cliente",
    "RUT",
    "Objetivo de compra",
    "Fecha/hora solicitada",
    "Etapa",
    "Corredor",
    "Solicitada el",
]


class ImportarVisitasResumen(BaseModel):
    nuevas: int = 0
    actualizadas: int = 0
    errores: list[str] = []


@dataclass
class _FilaParseada:
    propiedad: str
    direccion: str | None
    tipo: str | None
    mercado: str | None
    cliente: str | None
    rut: str | None
    objetivo_compra: str | None
    fecha_solicitada: datetime | None
    etapa: str | None
    corredor: str | None
    solicitada_el: datetime | None


def _texto(valor) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _fecha(valor) -> datetime | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        dt = valor
    else:
        dt = datetime.fromisoformat(str(valor).strip())
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _clave(datos) -> tuple:
    """Identifica una visita entre cargas, ya que el archivo no trae ningún ID.

    `Propiedad + Cliente + RUT + Fecha/hora solicitada` es lo que no cambia de
    una exportación a otra de la misma solicitud --a diferencia de `Etapa` y
    `Corredor`, que sí avanzan con el tiempo y por eso no entran en la clave--.

    Sirve tanto para una `_FilaParseada` recién leída del Excel como para un
    `Visita` que ya está en la base. **La fecha se normaliza a UTC-aware en
    los dos casos** porque SQLite no conserva el `tzinfo` de una columna
    `timestamptz` al leerla --vuelve "naive"-- mientras que la recién parseada
    del archivo sí lo trae (`_fecha`); sin esto, la misma solicitud comparaba
    distinto según viniera de la base o del archivo y nunca hacía match,
    duplicando en cada carga. Mismo caso que `app/auth.py::_aware`.
    """
    fecha = datos.fecha_solicitada
    if fecha is not None and fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return (datos.propiedad, datos.cliente, datos.rut, fecha)


def _parsear_fila(headers: dict[str, int], fila: tuple) -> _FilaParseada:
    def val(col):
        return fila[headers[col]]

    propiedad = _texto(val("Propiedad"))
    if propiedad is None:
        raise ValueError("Propiedad vacía")

    return _FilaParseada(
        propiedad=propiedad,
        direccion=_texto(val("Dirección")),
        tipo=_texto(val("Tipo")),
        mercado=_texto(val("Mercado")),
        cliente=_texto(val("Cliente")),
        rut=_texto(val("RUT")),
        objetivo_compra=_texto(val("Objetivo de compra")),
        fecha_solicitada=_fecha(val("Fecha/hora solicitada")),
        etapa=_texto(val("Etapa")),
        corredor=_texto(val("Corredor")),
        solicitada_el=_fecha(val("Solicitada el")),
    )


def importar_visitas(db: Session, contenido_xlsx: bytes) -> ImportarVisitasResumen:
    """Carga el archivo de visitas: solo agrega lo nuevo, sin duplicar.

    **No hay ID en el archivo de origen**, así que la identidad de una visita
    entre cargas la arma `_clave`. Una fila cuya clave ya existe **actualiza**
    la visita en vez de crear otra --antes cada carga insertaba todo de nuevo,
    y reimportar el mismo export duplicaba cada fila--.

    Si hay un solo error de formato no se escribe nada, igual que en canjes y
    negocios: media carga es peor que ninguna.
    """
    libro = openpyxl.load_workbook(BytesIO(contenido_xlsx), data_only=True)
    hoja = libro.worksheets[0]

    encabezados_fila = [c.value for c in hoja[1]]
    headers = {nombre: i for i, nombre in enumerate(encabezados_fila) if nombre}
    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in headers]
    if faltantes:
        raise ValueError(f"Faltan columnas en el archivo: {', '.join(faltantes)}")

    resumen = ImportarVisitasResumen()

    parseadas: list[_FilaParseada] = []
    for num_fila in range(2, hoja.max_row + 1):
        fila = tuple(c.value for c in hoja[num_fila])
        if all(v is None for v in fila):
            continue
        try:
            parseadas.append(_parsear_fila(headers, fila))
        except Exception as exc:
            resumen.errores.append(f"Fila {num_fila}: {exc}")

    if resumen.errores:
        return resumen

    # Una sola consulta para conocer lo que ya existe, igual que en canjes: el
    # archivo se conoce entero de antemano y no hay razón para ir a la base
    # fila por fila.
    existentes = {_clave(v): v for v in db.scalars(select(Visita))}

    for datos in parseadas:
        clave = _clave(datos)
        visita = existentes.get(clave)

        if visita is None:
            visita = Visita(propiedad=datos.propiedad)
            db.add(visita)
            existentes[clave] = visita
            resumen.nuevas += 1
        else:
            resumen.actualizadas += 1

        visita.propiedad = datos.propiedad
        visita.direccion = datos.direccion
        visita.tipo = datos.tipo
        visita.mercado = datos.mercado
        visita.cliente = datos.cliente
        visita.rut = datos.rut
        visita.objetivo_compra = datos.objetivo_compra
        visita.fecha_solicitada = datos.fecha_solicitada
        # Etapa y corredor sí se actualizan: son los dos datos que avanzan con
        # el tiempo para la misma solicitud, y quedarse con la primera versión
        # cargada los dejaría desactualizados para siempre.
        visita.etapa = datos.etapa
        visita.corredor = datos.corredor
        visita.solicitada_el = datos.solicitada_el

    db.commit()

    return resumen
