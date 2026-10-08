"""Cuánto dura cada etapa de un canje, separando activos de inactivos (`D-115`).

**No hay columnas de inicio y término por etapa: se reconstruyen de la
bitácora.** Cada movimiento de canje estampa en `etapa_resultante` dónde quedó el
canje --los registrados desde el modal y los cambios hechos desde la ficha--, así
que la secuencia de estampas ordenada por fecha es la historia de etapas.

**Un tramo** es una racha de estampas con la misma etapa. Empieza en la primera
estampa de la racha y termina en la primera estampa de **otra** etapa. Varias
gestiones seguidas en la misma etapa no son transiciones: cada una estampa la
etapa en la que ya estaba.

**La cancelación no termina un tramo**, por decisión del usuario. El promedio
responde cuánto tarda una etapa cuando el canje avanza; mezclarle lo que tarda en
caerse es la misma confusión que el panel ya evita al separar «Sobreviven antes de
caerse». Así que la última etapa de un cancelado no entra en ningún promedio.

**La etapa en curso de un activo sí cuenta, hasta hoy** --también por decisión del
usuario, que revirtió la primera versión--. Un canje que lleva 40 días en oferta
es justo el dato que importa, y dejarlo fuera escondía los atascos. Solo vale si
la etapa de la ficha coincide con la última estampa: si no, la etapa cambió sin
dejar rastro y no se sabe desde cuándo está ahí.

**El primer tramo de cada canje solo se mide si es «En revisión».** Un canje
arranca en esa etapa (`D-081`), así que su inicio es la fecha de solicitud. Si la
primera estampa es otra etapa, no se sabe cuándo entró ahí: puede ser un canje que
Dataprop mandó ya avanzado --los 605 movimientos migrados no traen etapa-- o uno
que pasó de revisión sin que nadie lo estampara. Medirlo desde esa primera estampa
inventaría un inicio, así que queda fuera.

**Activo o inactivo es el estado de hoy.** Un canje cancelado aporta las etapas
que alcanzó a terminar antes de caerse: esas duraciones son reales aunque el canje
ya no lo sea.
"""
from collections import defaultdict
from datetime import date, datetime, timezone

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.canje import ETAPA_LABELS, Canje, CanjeEstado, CanjeEtapa
from app.models.movimiento import EntityType, Movimiento

# Con menos casos que esto la pantalla no muestra promedio: con uno o dos tramos,
# el número es la anécdota de ese canje y no la duración de la etapa. Viaja en la
# respuesta para que el texto de la pantalla no lo escriba a mano (`D-048`).
MINIMO_CASOS = 3


class DuracionDeGrupo(BaseModel):
    """Los tramos de un grupo. `None` es "no hay casos", no cero."""

    casos: int
    # Cuántos de `casos` son la etapa en curso de un activo, medida hasta hoy.
    # Esos van a seguir creciendo, así que la pantalla dice cuántos son.
    en_curso: int
    promedio: float | None
    mediana: float | None
    minimo: int | None
    maximo: int | None


class DuracionDeEtapa(BaseModel):
    etapa: CanjeEtapa
    rotulo: str
    activos: DuracionDeGrupo
    inactivos: DuracionDeGrupo


class DuracionPorEtapa(BaseModel):
    etapas: list[DuracionDeEtapa]
    minimo_casos: int


def _dia(valor: datetime | date) -> date:
    if isinstance(valor, datetime):
        return valor.astimezone(timezone.utc).date() if valor.tzinfo else valor.date()
    return valor


def _mediana(valores: list[int]) -> float | None:
    if not valores:
        return None
    ordenados = sorted(valores)
    n = len(ordenados)
    if n % 2:
        return float(ordenados[n // 2])
    return (ordenados[n // 2 - 1] + ordenados[n // 2]) / 2


def _grupo(tramos: list[tuple[int, bool]]) -> DuracionDeGrupo:
    dias = [d for d, _ in tramos]
    return DuracionDeGrupo(
        casos=len(dias),
        en_curso=sum(1 for _, en_curso in tramos if en_curso),
        promedio=round(sum(dias) / len(dias), 1) if dias else None,
        mediana=_mediana(dias),
        minimo=min(dias) if dias else None,
        maximo=max(dias) if dias else None,
    )


def tramos_del_canje(
    fecha_solicitud: datetime | date,
    estampas: list[tuple[datetime, str]],
    etapa_actual: CanjeEtapa | None = None,
    hoy: date | None = None,
) -> list[tuple[CanjeEtapa, int, bool]]:
    """Los tramos de un canje, como `(etapa, días, en_curso)`.

    `estampas` va ordenada por fecha. Las etapas que la app ya no conoce --la
    retirada «Recepción», por ejemplo-- se saltan en vez de cortar un tramo.

    Con `hoy` se agrega la etapa en curso, medida hasta hoy, siempre que coincida
    con `etapa_actual` --la de la ficha-- y su inicio se conozca. Se pasa solo para
    los activos: un cancelado ya no avanza y su última etapa crecería para siempre.
    """
    validas = {e.value for e in CanjeEtapa}
    secuencia = [(f, CanjeEtapa(e)) for f, e in estampas if e in validas]
    solicitud = _dia(fecha_solicitud)

    if not secuencia:
        # Sin estampas, un activo que sigue en revisión está ahí desde la
        # solicitud: es donde arranca todo canje (`D-081`). En otra etapa no se
        # sabe desde cuándo.
        if hoy is not None and etapa_actual == CanjeEtapa.EN_REVISION:
            return [(CanjeEtapa.EN_REVISION, max((hoy - solicitud).days, 0), True)]
        return []

    tramos: list[tuple[CanjeEtapa, int, bool]] = []
    _, actual = secuencia[0]
    # Ver el docstring del módulo: el primer tramo solo tiene inicio conocido si
    # es «En revisión», y entonces arranca con la solicitud.
    desde: date | None = solicitud if actual == CanjeEtapa.EN_REVISION else None
    for fecha, etapa in secuencia[1:]:
        if etapa == actual:
            continue
        if desde is not None:
            # Un movimiento no puede ser anterior a la solicitud (lo valida el
            # registro), pero un dato viejo sí: un negativo no es una duración.
            tramos.append((actual, max((_dia(fecha) - desde).days, 0), False))
        actual, desde = etapa, _dia(fecha)

    if hoy is not None and desde is not None and actual == etapa_actual:
        tramos.append((actual, max((hoy - desde).days, 0), True))
    return tramos


def obtener_duracion_por_etapa(db: Session, hoy: date | None = None) -> DuracionPorEtapa:
    hoy = hoy or datetime.now(timezone.utc).date()
    canjes = {c.id: c for c in db.scalars(select(Canje)).all()}

    estampas: dict[int, list[tuple[datetime, str]]] = defaultdict(list)
    filas = db.execute(
        select(Movimiento.entity_id, Movimiento.fecha, Movimiento.etapa_resultante)
        .where(
            Movimiento.entity_type == EntityType.canje,
            Movimiento.etapa_resultante.is_not(None),
        )
        .order_by(Movimiento.entity_id, Movimiento.fecha, Movimiento.id)
    ).all()
    for canje_id, fecha, etapa in filas:
        estampas[canje_id].append((fecha, etapa))

    dias: dict[tuple[CanjeEtapa, bool], list[tuple[int, bool]]] = defaultdict(list)
    # Se recorren todos los canjes y no solo los que tienen estampas: un activo
    # sin ninguna puede estar en revisión desde la solicitud.
    for canje in canjes.values():
        activo = canje.estado == CanjeEstado.ACTIVO
        for etapa, d, en_curso in tramos_del_canje(
            canje.fecha_solicitud,
            estampas.get(canje.id, []),
            canje.etapa,
            hoy if activo else None,
        ):
            dias[(etapa, activo)].append((d, en_curso))

    return DuracionPorEtapa(
        etapas=[
            DuracionDeEtapa(
                etapa=etapa,
                rotulo=ETAPA_LABELS[etapa],
                activos=_grupo(dias[(etapa, True)]),
                inactivos=_grupo(dias[(etapa, False)]),
            )
            for etapa in CanjeEtapa
        ],
        minimo_casos=MINIMO_CASOS,
    )
