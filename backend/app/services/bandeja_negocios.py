"""Duraciones y bandeja diaria de negocios.

Responde **qué negocio hay que tocar hoy**, y de paso llena un hueco que era
visible: la pantalla de Negocios no tenía ninguna columna de fecha, así que no
había forma de saber si un negocio llevaba una semana o siete meses.

**Tres duraciones distintas, que conviene no confundir.** Un negocio puede llevar
seis meses abierto y estar avanzando perfecto; otro puede llevar dos meses y
estar muerto.

| Cuál | Cómo sale | Qué responde |
|---|---|---|
| `dias_abierto` | hoy − fecha de inicio | "lleva 4 meses abierto" |
| `dias_sin_gestion` | hoy − último movimiento | "3 semanas que nadie lo toca" |
| `dias_en_etapa` | hoy − último cambio de etapa | "2 meses trabado en E4" |

La tercera es la más útil de las tres: dice **dónde** se atascan los procesos, y
es la que va a habilitar proyectar cierres cuando haya historia. Sale de los
movimientos que traen `etapa_resultante`, no de cualquier movimiento.

**La "última gestión" es la del último movimiento, no `actualizado_en`.** Esa
columna existe y se mueve con cualquier edición: corregir una dirección mal
escrita haría que un negocio parezca activo sin que haya pasado nada. Un
timestamp técnico disfrazado de señal de negocio es peor que no tenerlo, porque
nadie sospecha de él.

**Los umbrales son en días, no en horas.** Los 48/24 horas de `CONFIG` son para
canjes, donde el ciclo es de días. Acá los procesos duran de un mes a varios, así
que medir en horas no distingue nada. Los 30 y 14 días son una estimación mía,
igual que el umbral de estancado del reporte semanal, y por eso viven acá y no en
`CONFIG`: no son una regla que alguien haya acordado.

**`sin_gestion` es un nivel aparte, no "crítico"** (misma razón que `D-029`).
Hoy los 18 negocios están así, porque el pipeline nunca se usó: no hay un solo
movimiento de negocio. Contarlos como críticos dejaría la bandeja en rojo
completo y el color dejaría de informar.

**Un compromiso registrado manda sobre el semáforo**, igual que en canjes
(`D-059`). El semáforo *infiere* que algo está abandonado por el tiempo que pasó;
el compromiso dice qué se prometió. Cuando los dos opinan, gana el que no
infiere. De ahí salen los dos niveles de arriba --`vencido` y `para_hoy`-- y la
regla de que un negocio agendado para adelante **no se lista**: se cuenta y se
dice, porque la pantalla se llama "qué me toca hoy" y listar lo que no toca es lo
que hace que se deje de mirar.

Eso tiene una consecuencia que conviene tener presente: como registrar un avance
agenda 3 días por defecto, ese negocio sale de la lista por 3 días. Con dos
negocios abiertos, avanzar los dos deja la lista vacía hasta que vuelva el
primero. No es un error --es lo mismo que hace canjes-- pero en canjes se diluye
entre cien filas y acá son dos.
"""
from datetime import date, datetime, timezone

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.catalogo import EstadoNegocio
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.negocio import Negocio, NegocioHito

# Días sin gestión. Estimación, no dato del negocio.
UMBRAL_CRITICO = 30
UMBRAL_ADVERTENCIA = 14

# Orden de atención. Los dos primeros salen de un compromiso registrado y por eso
# van antes que el semáforo, que es una inferencia.
PRIORIDAD = {
    "vencido": 0,
    "para_hoy": 1,
    "sin_gestion": 2,
    "critico": 3,
    "advertencia": 4,
    "al_dia": 5,
}


class Duraciones(BaseModel):
    """Las tres duraciones de un negocio, más la del cierre si ya cerró.

    Todas pueden ser nulas, y el nulo significa "no se sabe", no cero. Es
    deliberado: los 7 negocios históricos tienen la misma fecha de inicio y de
    cierre --el Excel traía una sola-- así que su duración de cierre es
    desconocida. Decir "duró 0 días" sería presentar un dato malo como un hecho.
    """

    dias_abierto: int | None
    dias_sin_gestion: int | None
    dias_en_etapa: int | None
    dias_hasta_el_cierre: int | None


class FilaBandejaNegocio(BaseModel):
    negocio_id: int
    codigo: str
    etapa: str | None
    modelo: str
    direccion: str | None
    comuna: str | None
    fecha_inicio: date | None
    comision_real_vp: str | None

    nivel: str
    duraciones: Duraciones
    ultimo_movimiento: datetime | None
    ultimo_movimiento_nombre: str | None
    # Lo que se prometió: el último compromiso que exista, no el del último
    # movimiento. Nulo en los negocios que nunca se gestionaron desde la app.
    proximo_seguimiento: date | None
    # Días de atraso. Positivo si venció, cero si es para hoy, nulo si no hay
    # compromiso. Va calculado para que la pantalla no reste fechas: el "hoy" del
    # cálculo tiene que ser el del servidor.
    dias_de_atraso: int | None


class ResumenBandejaNegocios(BaseModel):
    vencido: int
    para_hoy: int
    sin_gestion: int
    critico: int
    advertencia: int
    al_dia: int
    # Los agendados para más adelante. **No están en `filas`**: la pantalla se
    # llama "qué me toca hoy". Se cuentan para que se sepa que no se perdieron.
    agendados: int


class BandejaNegocios(BaseModel):
    resumen: ResumenBandejaNegocios
    filas: list[FilaBandejaNegocio]
    umbral_critico_dias: int
    umbral_advertencia_dias: int


def clasificar(dias_sin_gestion: int | None, dias_de_atraso: int | None = None) -> str:
    """El nivel a partir de los días sin gestión, o del compromiso si hay uno.

    **El compromiso manda.** Un negocio agendado para el jueves está al día el
    martes aunque lleve dos meses sin tocarse: eso es exactamente lo que significa
    haberlo agendado. Y uno con el compromiso vencido está atrasado aunque se haya
    tocado ayer, porque lo prometido no se cumplió.

    `None` en los dos es "nunca se registró un movimiento", que es su propio nivel
    y no el peor: es trabajo por empezar, no trabajo abandonado.
    """
    if dias_de_atraso is not None:
        if dias_de_atraso > 0:
            return "vencido"
        if dias_de_atraso == 0:
            return "para_hoy"
        return "agendado"
    if dias_sin_gestion is None:
        return "sin_gestion"
    if dias_sin_gestion >= UMBRAL_CRITICO:
        return "critico"
    if dias_sin_gestion >= UMBRAL_ADVERTENCIA:
        return "advertencia"
    return "al_dia"


def _dias(desde: date | datetime | None, hasta: date) -> int | None:
    if desde is None:
        return None
    if isinstance(desde, datetime):
        desde = desde.astimezone(timezone.utc).date() if desde.tzinfo else desde.date()
    return (hasta - desde).days


def duraciones_de(
    inicio: date | None,
    cierre: date | None,
    ultimo_movimiento: datetime | None,
    ultimo_cambio_etapa: datetime | None,
    hoy: date,
    abierto: bool,
) -> Duraciones:
    """Las tres duraciones, y la del cierre cuando se puede saber.

    `abierto` dice si al negocio le queda alguna liquidacion sin resolver, y hace
    falta para el tercer caso: un negocio **perdido sin fecha de cierre**. Ahi
    contar hasta hoy diria que un negocio que se cayo en enero "lleva 8 meses
    abierto" y el numero crece para siempre. No se sabe cuanto duro, asi que se
    dice que no se sabe.

    Va **sin valor por defecto** a proposito. Con un default, pasar una fecha de
    cierre y olvidar el flag hace que la fecha se ignore en silencio -- error que
    se cometio al escribir el primer test de esta funcion. Obligar a declararlo
    saca esa posibilidad.
    """
    # Si inicio y cierre son la misma fecha, la duracion es **desconocida**, y eso
    # vale para las dos: no sabemos que cerro el dia que empezo, sabemos que el
    # Excel traia una sola fecha y la migracion la puso en las dos columnas. Es el
    # caso de los 7 historicos. Un cierre el mismo dia existe en teoria, pero en un
    # negocio de ciclo largo es tan raro que conviene equivocarse del lado de "no
    # se sabe" antes que mostrar "duro 0 dias" como si fuera un hecho.
    sin_fechas_utiles = cierre is not None and inicio is not None and cierre == inicio

    hasta_cierre = None
    if cierre is not None and inicio is not None and not sin_fechas_utiles:
        hasta_cierre = (cierre - inicio).days

    # Tres casos, y el tercero es el que obliga a mirar `abierto`:
    #   sigue abierto            -> cuenta hasta hoy
    #   cerrado con fecha        -> conto hasta que cerro
    #   resuelto sin fecha       -> no se sabe
    if abierto:
        referencia = hoy
    elif cierre is not None:
        referencia = cierre
    else:
        referencia = None

    return Duraciones(
        dias_abierto=(
            None
            if inicio is None or sin_fechas_utiles or referencia is None
            else (referencia - inicio).days
        ),
        dias_sin_gestion=_dias(ultimo_movimiento, hoy),
        dias_en_etapa=_dias(ultimo_cambio_etapa, hoy),
        dias_hasta_el_cierre=hasta_cierre,
    )


def ultimos_movimientos(db: Session):
    """Por negocio: la fecha del último movimiento y la del último que movió etapa.

    Son dos consultas distintas porque son dos preguntas distintas: "cuándo se
    hizo algo" y "cuándo cambió de etapa". Un negocio puede tener diez
    movimientos de gestión sin haberse movido de E4.
    """
    cualquiera = dict(
        db.execute(
            select(Movimiento.entity_id, func.max(Movimiento.fecha))
            .where(Movimiento.entity_type == EntityType.negocio)
            .group_by(Movimiento.entity_id)
        ).all()
    )
    con_etapa = dict(
        db.execute(
            select(Movimiento.entity_id, func.max(Movimiento.fecha))
            .where(
                Movimiento.entity_type == EntityType.negocio,
                Movimiento.etapa_resultante.is_not(None),
            )
            .group_by(Movimiento.entity_id)
        ).all()
    )
    return cualquiera, con_etapa


def compromisos(db: Session) -> dict[int, date]:
    """El compromiso vigente de cada negocio: el último que **exista**.

    No el del último movimiento, y la diferencia importa por la misma razón que en
    canjes (`D-061`): hay movimientos que no agendan nada --un cambio de etapa
    corregido a mano, por ejemplo-- y si se mirara solo el más reciente, esa
    corrección borraría el compromiso que había. Un compromiso sigue en pie hasta
    que alguien pone otro.
    """
    vigentes: dict[int, date] = {}
    for negocio_id, seguimiento in db.execute(
        select(Movimiento.entity_id, Movimiento.proximo_seguimiento)
        .where(
            Movimiento.entity_type == EntityType.negocio,
            Movimiento.proximo_seguimiento.is_not(None),
        )
        # Ascendente: el último que se escribe sobre cada negocio es el más nuevo.
        .order_by(Movimiento.fecha, Movimiento.id)
    ).all():
        vigentes[negocio_id] = seguimiento
    return vigentes


def _nombres_ultimo_movimiento(db: Session) -> dict[int, str]:
    """El nombre del tipo del último movimiento de cada negocio."""
    subconsulta = (
        select(
            Movimiento.entity_id.label("entity_id"),
            func.max(Movimiento.fecha).label("fecha"),
        )
        .where(Movimiento.entity_type == EntityType.negocio)
        .group_by(Movimiento.entity_id)
        .subquery()
    )
    return dict(
        db.execute(
            select(Movimiento.entity_id, TipoMovimiento.nombre)
            .join(TipoMovimiento, TipoMovimiento.codigo == Movimiento.tipo_movimiento)
            .join(
                subconsulta,
                (subconsulta.c.entity_id == Movimiento.entity_id)
                & (subconsulta.c.fecha == Movimiento.fecha),
            )
            .where(Movimiento.entity_type == EntityType.negocio)
        ).all()
    )


def obtener_bandeja_negocios(db: Session, hoy: date | None = None) -> BandejaNegocios:
    """Los negocios con liquidaciones abiertas, ordenados por urgencia.

    Entra el negocio que tiene **al menos un hito activo**: el estado vive en el
    hito (`D-027`), así que un negocio con la promesa cerrada y la escritura
    abierta sigue siendo trabajo pendiente.
    """
    hoy = hoy or datetime.now(timezone.utc).date()
    cualquiera, con_etapa = ultimos_movimientos(db)
    nombres = _nombres_ultimo_movimiento(db)
    seguimientos = compromisos(db)

    negocios = db.execute(
        select(Negocio)
        .join(NegocioHito, NegocioHito.negocio_id == Negocio.id)
        .where(NegocioHito.estado == EstadoNegocio.ACTIVO)
        .distinct()
    ).scalars().all()

    filas: list[FilaBandejaNegocio] = []
    agendados = 0
    for n in negocios:
        activos = [h for h in n.hitos if h.estado == EstadoNegocio.ACTIVO]
        # El hito abierto mas antiguo es el que define desde cuando esta abierto.
        inicio = min((h.fecha_inicio for h in activos if h.fecha_inicio), default=None)
        real = sum((h.comision_real_vp or 0) for h in activos)

        # La bandeja solo lista negocios con liquidaciones abiertas.
        d = duraciones_de(inicio, None, cualquiera.get(n.id), con_etapa.get(n.id), hoy, abierto=True)

        seguimiento = seguimientos.get(n.id)
        atraso = (hoy - seguimiento).days if seguimiento is not None else None
        nivel = clasificar(d.dias_sin_gestion, atraso)

        # Agendado para más adelante: se cuenta y no se lista. La pantalla se
        # llama "qué me toca hoy", y este negocio no toca hoy.
        if nivel == "agendado":
            agendados += 1
            continue

        filas.append(
            FilaBandejaNegocio(
                negocio_id=n.id,
                codigo=n.codigo,
                etapa=n.etapa,
                modelo=n.modelo.value if hasattr(n.modelo, "value") else str(n.modelo),
                direccion=n.propiedad.direccion if n.propiedad else None,
                comuna=n.propiedad.comuna if n.propiedad else None,
                fecha_inicio=inicio,
                comision_real_vp=str(real),
                nivel=nivel,
                duraciones=d,
                ultimo_movimiento=cualquiera.get(n.id),
                ultimo_movimiento_nombre=nombres.get(n.id),
                proximo_seguimiento=seguimiento,
                dias_de_atraso=atraso,
            )
        )

    # Primero lo mas urgente; dentro del mismo nivel, lo que lleva mas tiempo
    # abierto, que es lo que mas riesgo acumula.
    filas.sort(key=lambda f: (PRIORIDAD[f.nivel], -(f.duraciones.dias_abierto or 0)))

    cuantos = lambda nivel: sum(1 for f in filas if f.nivel == nivel)  # noqa: E731

    return BandejaNegocios(
        resumen=ResumenBandejaNegocios(
            vencido=cuantos("vencido"),
            para_hoy=cuantos("para_hoy"),
            sin_gestion=cuantos("sin_gestion"),
            critico=cuantos("critico"),
            advertencia=cuantos("advertencia"),
            al_dia=cuantos("al_dia"),
            agendados=agendados,
        ),
        filas=filas,
        umbral_critico_dias=UMBRAL_CRITICO,
        umbral_advertencia_dias=UMBRAL_ADVERTENCIA,
    )
