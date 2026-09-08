from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO

import openpyxl
from pydantic import BaseModel
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
    "Solicitada el",
]


class ImportarVisitasResumen(BaseModel):
    nuevas: int = 0
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
        solicitada_el=_fecha(val("Solicitada el")),
    )


def importar_visitas(db: Session, contenido_xlsx: bytes) -> ImportarVisitasResumen:
    """Carga el archivo de visitas: no hay ID en el origen, así que no hay que
    buscar existentes ni actualizar --cada fila válida es una visita nueva.

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

    for datos in parseadas:
        db.add(
            Visita(
                propiedad=datos.propiedad,
                direccion=datos.direccion,
                tipo=datos.tipo,
                mercado=datos.mercado,
                cliente=datos.cliente,
                rut=datos.rut,
                objetivo_compra=datos.objetivo_compra,
                fecha_solicitada=datos.fecha_solicitada,
                etapa=datos.etapa,
                solicitada_el=datos.solicitada_el,
            )
        )
    db.commit()
    resumen.nuevas = len(parseadas)

    return resumen
