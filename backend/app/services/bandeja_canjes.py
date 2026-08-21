"""Semáforo y bandeja diaria de canjes (sprint 20).

Responde una sola pregunta: **qué canje hay que tocar hoy**.

Los umbrales son los de la hoja `CONFIG`: 48 horas sin gestión es crítico, 24 es
advertencia. Son globales y no por tipo de movimiento — `tipos_movimiento` tiene
además un `sla_horas` propio de cada paso, pero eso mide otra cosa: cuánto
debería demorar *ese* paso, no cuánto lleva el canje sin que nadie lo mire.

**`sin_gestion` es un nivel aparte, no "crítico".** Hoy los 194 canjes abiertos
están así, porque el seguimiento se hacía en el Excel. Si se contaran como
críticos, la bandeja abriría con 194 filas rojas y el color dejaría de informar
nada. "Nunca se tocó" y "se tocó y se dejó estar tres días" son problemas
distintos y se resuelven distinto.
"""
from datetime import datetime, timedelta, timezone

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.movimiento import EntityType, Movimiento

# Umbrales de CONFIG, en horas sin gestión.
UMBRAL_CRITICO = 48
UMBRAL_ADVERTENCIA = 24

# Orden de atención: primero lo que nunca se tocó, después lo más abandonado.
PRIORIDAD = {"sin_gestion": 0, "critico": 1, "advertencia": 2, "al_dia": 3}


class FilaBandeja(BaseModel):
    canje_id: int
    fecha_solicitud: datetime
    etapa: CanjeEtapa
    corredor_solicitante_nombre: str | None
    corredor_propietario_nombre: str | None
    comuna: str | None
    direccion: str | None

    nivel: str
    horas_sin_gestion: float | None
    ultimo_movimiento: datetime | None
    ultimo_movimiento_nombre: str | None


class ResumenBandeja(BaseModel):
    sin_gestion: int
    critico: int
    advertencia: int
    al_dia: int

    @property
    def requieren_atencion(self) -> int:
        return self.sin_gestion + self.critico + self.advertencia


class Bandeja(BaseModel):
    resumen: ResumenBandeja
    filas: list[FilaBandeja]
    umbral_critico_horas: int
    umbral_advertencia_horas: int


def clasificar(horas: float | None) -> str:
    """El nivel del semáforo a partir de las horas sin gestión."""
    if horas is None:
        return "sin_gestion"
    if horas >= UMBRAL_CRITICO:
        return "critico"
    if horas >= UMBRAL_ADVERTENCIA:
        return "advertencia"
    return "al_dia"


def obtener_bandeja(db: Session, ahora: datetime | None = None) -> Bandeja:
    """Los canjes que están abiertos de verdad, ordenados por urgencia.

    Abierto quiere decir `estado = ACTIVO` **y** etapa distinta de `CERRADO`.
    Los 31 canjes que están activos pero con etapa cerrada no son trabajo
    pendiente: es el mismo desalineamiento que arrastra el dato de Dataprop.
    """
    ahora = ahora or datetime.now(timezone.utc)

    # Último movimiento de cada canje, en una sola vuelta.
    ultimos = (
        select(
            Movimiento.entity_id.label("canje_id"),
            func.max(Movimiento.fecha).label("fecha"),
        )
        .where(Movimiento.entity_type == EntityType.canje)
        .group_by(Movimiento.entity_id)
        .subquery()
    )

    filas = db.execute(
        select(Canje, ultimos.c.fecha)
        .outerjoin(ultimos, ultimos.c.canje_id == Canje.id)
        .where(Canje.estado == CanjeEstado.ACTIVO, Canje.etapa != CanjeEtapa.CERRADO)
    ).all()

    # El nombre del último movimiento se resuelve aparte: son pocos y así se
    # evita una tercera unión sobre una tabla que hoy está casi vacía.
    nombres: dict[int, str] = {}
    ids_con_movimiento = [c.id for c, ultima in filas if ultima is not None]
    if ids_con_movimiento:
        from app.models.movimiento import TipoMovimiento

        for canje_id, nombre in db.execute(
            select(Movimiento.entity_id, TipoMovimiento.nombre)
            .join(TipoMovimiento, TipoMovimiento.codigo == Movimiento.tipo_movimiento)
            .where(
                Movimiento.entity_type == EntityType.canje,
                Movimiento.entity_id.in_(ids_con_movimiento),
            )
            .order_by(Movimiento.fecha)
        ).all():
            # Al ir en orden ascendente, el último que se escribe es el más nuevo.
            nombres[canje_id] = nombre

    resultado: list[FilaBandeja] = []
    conteo = {"sin_gestion": 0, "critico": 0, "advertencia": 0, "al_dia": 0}

    for canje, ultima in filas:
        if ultima is None:
            horas = None
        else:
            if ultima.tzinfo is None:
                ultima = ultima.replace(tzinfo=timezone.utc)
            horas = round((ahora - ultima).total_seconds() / 3600, 1)

        nivel = clasificar(horas)
        conteo[nivel] += 1
        resultado.append(
            FilaBandeja(
                canje_id=canje.id,
                fecha_solicitud=canje.fecha_solicitud,
                etapa=canje.etapa,
                corredor_solicitante_nombre=canje.corredor_solicitante_nombre,
                corredor_propietario_nombre=canje.corredor_propietario_nombre,
                comuna=canje.comuna,
                direccion=canje.direccion,
                nivel=nivel,
                horas_sin_gestion=horas,
                ultimo_movimiento=ultima,
                ultimo_movimiento_nombre=nombres.get(canje.id),
            )
        )

    # Dentro de cada nivel, lo más viejo primero: entre dos canjes igual de
    # abandonados, el que lleva más tiempo esperando va antes.
    resultado.sort(
        key=lambda f: (
            PRIORIDAD[f.nivel],
            -(f.horas_sin_gestion or 0),
            f.fecha_solicitud,
        )
    )

    return Bandeja(
        resumen=ResumenBandeja(**conteo),
        filas=resultado,
        umbral_critico_horas=UMBRAL_CRITICO,
        umbral_advertencia_horas=UMBRAL_ADVERTENCIA,
    )
