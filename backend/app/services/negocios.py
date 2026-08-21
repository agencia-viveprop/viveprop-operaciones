"""Capa de servicio de negocios: valorizacion, comisiones y validaciones.

Aca se juntan las tres piezas de los sprints anteriores. El orden importa y es
siempre el mismo:

    1. Resolver la valorizacion   -> congela la UF y calcula el CLP
    2. Resolver la base           -> el manual le gana al calculado (D-017)
    3. Calcular las comisiones    -> con la formula del modelo (D-018)
    4. Persistir los siete montos

Los montos se calculan **al guardar** y quedan escritos. No se recalculan al
leer: si manana cambia una regla, la historia no se mueve.
"""
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalogo import Catalogo, Etapa, TipoCatalogo
from app.models.canje import MonedaTipo
from app.models.negocio import Negocio, NegocioHito, Propiedad
from app.services import comisiones as motor
from app.services.uf import UFNoDisponible, valor_uf

CENTAVO = Decimal("0.01")


class NegocioError(Exception):
    """Error de negocio que el router traduce a un 400 con mensaje util."""


# ---------------------------------------------------------------- validaciones


def validar_catalogo(db: Session, catalogo_id: int | None, tipo: TipoCatalogo, campo: str) -> None:
    """Verifica que el id apunte a un catalogo del tipo correcto.

    Es el costo que aceptamos en D-021 al usar una tabla generica: la base no
    puede impedir que `alianza_id` apunte a un tipo de propiedad, asi que la
    validacion vive aca.
    """
    if catalogo_id is None:
        return
    fila = db.get(Catalogo, catalogo_id)
    if fila is None:
        raise NegocioError(f"{campo}: no existe el catálogo {catalogo_id}.")
    if fila.tipo != tipo.value:
        raise NegocioError(
            f"{campo}: el catálogo {catalogo_id} es de tipo '{fila.tipo}', "
            f"y se esperaba '{tipo.value}'."
        )
    if not fila.activo:
        raise NegocioError(f"{campo}: '{fila.nombre}' está dado de baja.")


def validar_etapa(db: Session, etapa: str | None) -> None:
    if etapa is None:
        return
    if db.get(Etapa, etapa) is None:
        validas = db.scalars(select(Etapa.codigo).order_by(Etapa.orden)).all()
        raise NegocioError(f"Etapa desconocida: '{etapa}'. Las válidas son: {', '.join(validas)}.")


# --------------------------------------------------------------- valorizacion


def resolver_valorizacion(db: Session, hito: NegocioHito) -> None:
    """Congela la UF y deja `valor_clp_calculado` al dia.

    La fecha de referencia es `fecha_valorizacion` si esta, y si no
    `fecha_inicio` -- la regla que se levanto de las 19 filas del historico.

    No toca `valor_clp_manual`: ese lo pone una persona y el sistema no opina.
    """
    if hito.valor_negocio is None or hito.moneda is None:
        hito.uf_snapshot = None
        hito.valor_clp_calculado = None
        return

    if hito.moneda == MonedaTipo.CLP:
        hito.uf_snapshot = None
        hito.valor_clp_calculado = hito.valor_negocio
        return

    if hito.moneda != MonedaTipo.UF:
        raise NegocioError(
            f"No se puede valorizar en '{hito.moneda.value}': solo UF y CLP tienen conversión."
        )

    fecha_ref: date = hito.fecha_valorizacion or hito.fecha_inicio
    try:
        uf = valor_uf(db, fecha_ref)
    except UFNoDisponible as exc:
        raise NegocioError(f"{exc} Hay que cargar el nuevo tramo antes de valorizar.") from exc

    hito.uf_snapshot = uf
    hito.valor_clp_calculado = (hito.valor_negocio * uf).quantize(CENTAVO)


def recalcular_comisiones(hito: NegocioHito, modelo: str) -> None:
    """Aplica el motor y persiste los siete montos en el hito.

    Si no hay base todavia -- un negocio recien abierto sin valor -- los montos
    quedan en nulo en vez de en cero, para distinguir "sin valorizar" de
    "valorizado en cero".
    """
    base = hito.base_comision
    if base is None:
        for campo in (
            "comision_total", "comision_broker", "rebate_concentrador",
            "comision_vp_bruta", "comision_equipo", "comision_tercero",
            "comision_real_vp",
        ):
            setattr(hito, campo, None)
        return

    cero = Decimal("0")
    resultado = motor.calcular(
        modelo=modelo,
        estado=hito.estado.value if hasattr(hito.estado, "value") else str(hito.estado),
        base=base,
        pct_lado_vendedor=hito.pct_lado_vendedor or cero,
        pct_lado_comprador=hito.pct_lado_comprador or cero,
        pct_rebate_concentrador=hito.pct_rebate_concentrador or cero,
        pct_broker_vendedor=hito.pct_broker_vendedor or cero,
        pct_broker_comprador=hito.pct_broker_comprador or cero,
        pct_vp_vendedor=hito.pct_vp_vendedor or cero,
        pct_vp_comprador=hito.pct_vp_comprador or cero,
        pct_equipo=hito.pct_equipo or cero,
        pct_tercero=hito.pct_tercero or cero,
    )

    hito.comision_total = resultado.comision_total.quantize(CENTAVO)
    hito.comision_broker = resultado.comision_broker.quantize(CENTAVO)
    hito.rebate_concentrador = resultado.rebate_concentrador.quantize(CENTAVO)
    hito.comision_vp_bruta = resultado.comision_vp_bruta.quantize(CENTAVO)
    hito.comision_equipo = resultado.comision_equipo.quantize(CENTAVO)
    hito.comision_tercero = resultado.comision_tercero.quantize(CENTAVO)
    hito.comision_real_vp = resultado.comision_real_vp.quantize(CENTAVO)


def refrescar_hito(db: Session, hito: NegocioHito, modelo: str) -> None:
    """Los dos pasos que van siempre juntos, en el orden correcto."""
    resolver_valorizacion(db, hito)
    recalcular_comisiones(hito, modelo)


# ------------------------------------------------------------------ propiedad


def obtener_o_crear_propiedad(db: Session, datos: dict) -> Propiedad:
    """Reusa la propiedad si ya existe con esa direccion, unidad y comuna.

    Sin esto, cada reintento sobre la misma unidad crearia una propiedad nueva y
    el patron que la tabla existe para mostrar quedaria invisible igual que en
    el Excel.
    """
    for campo in ("direccion", "comuna"):
        if not datos.get(campo):
            raise NegocioError(f"La propiedad necesita {campo}.")

    validar_catalogo(db, datos.get("tipo_propiedad_id"), TipoCatalogo.TIPO_PROPIEDAD, "tipo_propiedad_id")
    validar_catalogo(db, datos.get("estado_propiedad_id"), TipoCatalogo.ESTADO_PROPIEDAD, "estado_propiedad_id")

    existente = db.scalar(
        select(Propiedad).where(
            Propiedad.direccion == datos["direccion"],
            Propiedad.unidad == datos.get("unidad"),
            Propiedad.comuna == datos["comuna"],
        )
    )
    if existente is not None:
        return existente

    propiedad = Propiedad(**datos)
    db.add(propiedad)
    db.flush()
    return propiedad


def buscar_propiedades_parecidas(db: Session, texto: str, limite: int = 10) -> list[Propiedad]:
    """Para que el alta ofrezca lo que ya existe antes de crear un duplicado.

    La clave unica no alcanza: en los datos reales la misma unidad aparece como
    "Av. Fernandez Albano 492" y como "Fernandez Albano 492".
    """
    patron = f"%{texto.strip()}%"
    return list(
        db.scalars(
            select(Propiedad)
            .where(Propiedad.direccion.ilike(patron))
            .order_by(Propiedad.direccion)
            .limit(limite)
        ).all()
    )
