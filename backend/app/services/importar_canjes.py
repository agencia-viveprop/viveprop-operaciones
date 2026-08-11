from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO

import openpyxl
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa, MonedaTipo, OperacionTipo

# Nombres de columna esperados = mismos alias de la query SQL validada contra Dataprop.
COLUMNAS_REQUERIDAS = [
    "ID_CANJE",
    "FECHA_SOLICITUD",
    "FECHA_CIERRE",
    "ESTADO",
    "ETAPA",
    "NOMBRE_CORREDOR_SOLICITANTE",
    "NOMBRE_CORREDOR_PROPIETARIO",
    "EMAIL_CORREDOR_SOLICITANTE",
    "EMAIL_CORREDOR_PROPIETARIO",
    "TIPO_OPERACION",
    "TIPO_PROPIEDAD",
    "COMUNA_PROPIEDAD",
    "DIRECCION_PROPIEDAD",
    "VALOR_PROP",
    "MONEDA_VALOR",
    "LINK_PROPIEDAD",
]

ESTADO_MAP = {"Activo": CanjeEstado.ACTIVO, "Cancelado": CanjeEstado.CANCELADO}
ETAPA_MAP = {
    "Sin etapa": CanjeEtapa.SIN_ETAPA,
    "En revisión": CanjeEtapa.EN_REVISION,
    "Proceso de acuerdo": CanjeEtapa.PROCESO_DE_ACUERDO,
    "En oferta": CanjeEtapa.EN_OFERTA,
    "En negocio": CanjeEtapa.EN_NEGOCIO,
    "Cerrado": CanjeEtapa.CERRADO,
}
OPERACION_MAP = {"Venta": OperacionTipo.VENTA, "Arriendo": OperacionTipo.ARRIENDO, "Otro/Desconocido": OperacionTipo.OTRO}
MONEDA_MAP = {"CLP": MonedaTipo.CLP, "UF": MonedaTipo.UF, "Otra": MonedaTipo.OTRA}


class ImportarCanjesResumen(BaseModel):
    nuevas: int = 0
    actualizadas: int = 0
    ignoradas: int = 0
    errores: list[str] = []


@dataclass
class _FilaParseada:
    id: int
    fecha_solicitud: datetime
    fecha_cierre: datetime | None
    estado: CanjeEstado
    etapa: CanjeEtapa
    corredor_solicitante_nombre: str | None
    corredor_propietario_nombre: str | None
    corredor_solicitante_email: str | None
    corredor_propietario_email: str | None
    tipo_operacion: OperacionTipo | None
    tipo_inmueble: str | None
    comuna: str | None
    direccion: str | None
    valor_prop: float | None
    moneda_valor: MonedaTipo | None
    link_propiedad: str | None


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


def _numero(valor) -> float | None:
    if valor is None or valor == "":
        return None
    return float(valor)


def _mapear(valor, mapa: dict, nombre_campo: str):
    texto = _texto(valor)
    if texto is None:
        return None
    if texto not in mapa:
        raise ValueError(f"{nombre_campo} desconocido: '{texto}'")
    return mapa[texto]


def _parsear_fila(headers: dict[str, int], fila: tuple) -> _FilaParseada:
    def val(col):
        return fila[headers[col]]

    id_canje = val("ID_CANJE")
    if id_canje is None or id_canje == "":
        raise ValueError("ID_CANJE vacío")

    fecha_solicitud = _fecha(val("FECHA_SOLICITUD"))
    if fecha_solicitud is None:
        raise ValueError("FECHA_SOLICITUD vacía")

    estado = _mapear(val("ESTADO"), ESTADO_MAP, "ESTADO")
    if estado is None:
        raise ValueError("ESTADO vacío")

    return _FilaParseada(
        id=int(float(id_canje)),
        fecha_solicitud=fecha_solicitud,
        fecha_cierre=_fecha(val("FECHA_CIERRE")),
        estado=estado,
        etapa=_mapear(val("ETAPA"), ETAPA_MAP, "ETAPA") or CanjeEtapa.SIN_ETAPA,
        corredor_solicitante_nombre=_texto(val("NOMBRE_CORREDOR_SOLICITANTE")),
        corredor_propietario_nombre=_texto(val("NOMBRE_CORREDOR_PROPIETARIO")),
        corredor_solicitante_email=_texto(val("EMAIL_CORREDOR_SOLICITANTE")),
        corredor_propietario_email=_texto(val("EMAIL_CORREDOR_PROPIETARIO")),
        tipo_operacion=_mapear(val("TIPO_OPERACION"), OPERACION_MAP, "TIPO_OPERACION"),
        tipo_inmueble=_texto(val("TIPO_PROPIEDAD")),
        comuna=_texto(val("COMUNA_PROPIEDAD")),
        direccion=_texto(val("DIRECCION_PROPIEDAD")),
        valor_prop=_numero(val("VALOR_PROP")),
        moneda_valor=_mapear(val("MONEDA_VALOR"), MONEDA_MAP, "MONEDA_VALOR"),
        link_propiedad=_texto(val("LINK_PROPIEDAD")),
    )


def importar_canjes(db: Session, contenido_xlsx: bytes) -> ImportarCanjesResumen:
    libro = openpyxl.load_workbook(BytesIO(contenido_xlsx), data_only=True)
    hoja = libro.worksheets[0]

    encabezados_fila = [c.value for c in hoja[1]]
    headers = {nombre: i for i, nombre in enumerate(encabezados_fila) if nombre}
    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in headers]
    if faltantes:
        raise ValueError(f"Faltan columnas en el archivo: {', '.join(faltantes)}")

    resumen = ImportarCanjesResumen()

    for num_fila in range(2, hoja.max_row + 1):
        fila = tuple(c.value for c in hoja[num_fila])
        if all(v is None for v in fila):
            continue

        try:
            datos = _parsear_fila(headers, fila)
        except Exception as exc:
            resumen.errores.append(f"Fila {num_fila}: {exc}")
            continue

        try:
            canje = db.get(Canje, datos.id)
            if canje is None:
                canje = Canje(
                    id=datos.id,
                    fecha_solicitud=datos.fecha_solicitud,
                    fecha_cierre=datos.fecha_cierre,
                    estado=datos.estado,
                    etapa=datos.etapa,
                    corredor_solicitante_nombre=datos.corredor_solicitante_nombre,
                    corredor_propietario_nombre=datos.corredor_propietario_nombre,
                    corredor_solicitante_email=datos.corredor_solicitante_email,
                    corredor_propietario_email=datos.corredor_propietario_email,
                    tipo_operacion=datos.tipo_operacion,
                    tipo_inmueble=datos.tipo_inmueble,
                    comuna=datos.comuna,
                    direccion=datos.direccion,
                    valor_prop=datos.valor_prop,
                    moneda_valor=datos.moneda_valor,
                    link_propiedad=datos.link_propiedad,
                    gestionado_en_app=False,
                )
                db.add(canje)
                db.commit()
                resumen.nuevas += 1
            elif not canje.gestionado_en_app:
                # Nunca se tocan estado/etapa aqui -- esos los gobierna la app
                # (movimientos o edicion manual), no la importacion.
                canje.fecha_cierre = datos.fecha_cierre
                canje.corredor_solicitante_nombre = datos.corredor_solicitante_nombre
                canje.corredor_propietario_nombre = datos.corredor_propietario_nombre
                canje.corredor_solicitante_email = datos.corredor_solicitante_email
                canje.corredor_propietario_email = datos.corredor_propietario_email
                canje.tipo_operacion = datos.tipo_operacion
                canje.tipo_inmueble = datos.tipo_inmueble
                canje.comuna = datos.comuna
                canje.direccion = datos.direccion
                canje.valor_prop = datos.valor_prop
                canje.moneda_valor = datos.moneda_valor
                canje.link_propiedad = datos.link_propiedad
                db.commit()
                resumen.actualizadas += 1
            else:
                resumen.ignoradas += 1
        except Exception as exc:
            db.rollback()
            resumen.errores.append(f"Fila {num_fila} (ID {datos.id}): {exc}")

    return resumen
