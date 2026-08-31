"""Semáforo y bandeja diaria de canjes (sprint 20).

Responde una sola pregunta: **qué canje hay que tocar hoy**.

Los umbrales son los de la hoja `CONFIG`: 48 horas sin gestión es crítico, 24 es
advertencia. Son globales y no por tipo de movimiento — `tipos_movimiento` tiene
además un `sla_horas` propio de cada paso, pero eso mide otra cosa: cuánto
debería demorar *ese* paso, no cuánto lleva el canje sin que nadie lo mire.

**Un compromiso incumplido deja de proteger (`D-094`).** El compromiso vence, y
desde ahí el semáforo toma el control: el atraso entra a los mismos umbrales que
las horas sin gestión, con **un día de gracia**. Así, vencido ayer sigue siendo
"vencido" --recién vencido no es abandonado-- y a partir del segundo día escala a
advertencia y al tercero a crítico.

Antes el nivel se quedaba en "vencido" para siempre, sin importar si el atraso
era de un día o de un mes, y el usuario lo dijo con precisión: *"cualquier fecha
puesta de seguimiento **oculta** la realidad de gestión"*. Tenía razón: poner una
fecha sacaba al canje del semáforo de forma permanente.

Lo que **sí** sigue protegiendo es el compromiso **vigente**: un canje agendado
para dentro de diez días no tiene gestión en el intertanto por definición, y
someterlo al reloj pondría en rojo todo lo agendado a más de dos días. Agendar
dejaría de servir.

**`sin_gestion` es un nivel aparte, no "crítico".** Hoy los 194 canjes abiertos
están así, porque el seguimiento se hacía en el Excel. Si se contaran como
críticos, la bandeja abriría con 194 filas rojas y el color dejaría de informar
nada. "Nunca se tocó" y "se tocó y se dejó estar tres días" son problemas
distintos y se resuelven distinto.
"""
from datetime import date, datetime, timedelta, timezone

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.movimiento import EntityType, Movimiento

# Umbrales de CONFIG, en horas sin gestión.
UMBRAL_CRITICO = 48
UMBRAL_ADVERTENCIA = 24

# Orden de atención: primero lo que nunca se tocó, después por severidad.
#
# Antes los dos niveles de compromiso iban arriba de todo, porque un compromiso
# registrado vale más que una inferencia. Con el escalamiento (`D-094`) esa
# separación por origen ya no sirve para ordenar: un compromiso vencido hace tres
# días **es** un crítico, así que si los compromisos fueran primero los escalados
# quedarían debajo de "para hoy" y el escalamiento no se vería.
#
# "Vencido" pasa a significar **recién vencido** --un día-- y por eso baja: un
# canje que nadie tocó nunca, o uno abandonado hace una semana, piden atención
# antes que uno cuyo compromiso venció ayer.
PRIORIDAD = {
    "sin_gestion": 0,
    "critico": 1,
    "advertencia": 2,
    "vencido": 3,
    "para_hoy": 4,
    "al_dia": 5,
}


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
    # Lo que se prometió: la fecha del movimiento más reciente que agendó algo.
    # Nulo en los canjes que nunca se gestionaron desde la app.
    proximo_seguimiento: date | None
    # Días de atraso. Positivo si el seguimiento venció, cero si es para hoy,
    # nulo si no hay compromiso. Va calculado para que la pantalla no reste
    # fechas: el "hoy" del cálculo tiene que ser el del servidor.
    dias_de_atraso: int | None


class ResumenBandeja(BaseModel):
    vencido: int
    para_hoy: int
    sin_gestion: int
    critico: int
    advertencia: int
    al_dia: int
    # Los que tienen seguimiento agendado para más adelante. **No están en
    # `filas`**: la pantalla se llama "qué me toca hoy", y listar lo que no toca
    # es lo que hace que se deje de mirar. Se cuentan para que se sepa que
    # existen y que no se perdieron.
    agendados: int

    @property
    def requieren_atencion(self) -> int:
        return (
            self.vencido + self.para_hoy + self.sin_gestion + self.critico + self.advertencia
        )


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


def clasificar_atraso(dias_de_atraso: int) -> str:
    """El nivel de un compromiso **incumplido**, según cuánto lleva vencido.

    Mismos umbrales que el semáforo, corridos **un día de gracia**: vencido ayer
    es "vencido" y recién al segundo día empieza a escalar. Sin la gracia el
    nivel "vencido" quedaría vacío por definición --estar vencido implica al
    menos un día de atraso, y un día son las 24 horas del umbral de
    advertencia-- y ese recuadro pasaría a ser un cartel que siempre marca cero
    (`D-093`, `D-094`).
    """
    horas = (dias_de_atraso - 1) * 24
    if horas >= UMBRAL_CRITICO:
        return "critico"
    if horas >= UMBRAL_ADVERTENCIA:
        return "advertencia"
    return "vencido"


def obtener_bandeja(db: Session, ahora: datetime | None = None) -> Bandeja:
    """Los canjes que están abiertos de verdad, ordenados por urgencia.

    Abierto quiere decir `estado = ACTIVO` **y** etapa distinta de `CERRADO`.
    Los 31 canjes que están activos pero con etapa cerrada no son trabajo
    pendiente: es el mismo desalineamiento que arrastra el dato de Dataprop.
    """
    ahora = ahora or datetime.now(timezone.utc)

    hoy = ahora.date()

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

    # El compromiso vigente es el del último movimiento **que tenga uno**, no el
    # del último movimiento.
    #
    # La diferencia importa: registrar un cambio de etapa desde la ficha crea un
    # movimiento sin seguimiento --corregir un dato no es una gestión-- y si se
    # mirara solo el más reciente, esa corrección borraría el compromiso que
    # había. Un compromiso sigue en pie hasta que alguien pone otro.
    seguimientos: dict[int, date] = {}
    for canje_id, seguimiento in db.execute(
        select(Movimiento.entity_id, Movimiento.proximo_seguimiento)
        .where(
            Movimiento.entity_type == EntityType.canje,
            Movimiento.proximo_seguimiento.is_not(None),
        )
        # Ascendente: el último que se escribe sobre cada canje es el más nuevo.
        .order_by(Movimiento.fecha, Movimiento.id)
    ).all():
        seguimientos[canje_id] = seguimiento

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
    conteo = {
        "vencido": 0, "para_hoy": 0, "sin_gestion": 0,
        "critico": 0, "advertencia": 0, "al_dia": 0, "agendados": 0,
    }

    for canje, ultima in filas:
        if ultima is None:
            horas = None
        else:
            if ultima.tzinfo is None:
                ultima = ultima.replace(tzinfo=timezone.utc)
            horas = round((ahora - ultima).total_seconds() / 3600, 1)

        seguimiento = seguimientos.get(canje.id)
        atraso = (hoy - seguimiento).days if seguimiento is not None else None

        # El compromiso **vigente** manda sobre el semáforo: el semáforo infiere
        # que algo está abandonado por el tiempo que pasó, y el compromiso dice
        # qué se prometió. Cuando los dos opinan, gana el que no es una
        # inferencia. Pero un compromiso **incumplido** ya no dice nada sobre el
        # futuro, así que ahí el atraso escala por el semáforo (`D-094`).
        if atraso is None:
            nivel = clasificar(horas)
        elif atraso > 0:
            nivel = clasificar_atraso(atraso)
        elif atraso == 0:
            nivel = "para_hoy"
        else:
            # Agendado para más adelante: se cuenta y no se lista.
            conteo["agendados"] += 1
            continue

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
                proximo_seguimiento=seguimiento,
                dias_de_atraso=atraso,
            )
        )

    # Dentro de cada nivel, lo más viejo primero: entre dos canjes igual de
    # abandonados, el que lleva más tiempo esperando va antes.
    resultado.sort(
        key=lambda f: (
            PRIORIDAD[f.nivel],
            # Entre dos vencidos, el que lleva más días de atraso.
            -(f.dias_de_atraso or 0),
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
