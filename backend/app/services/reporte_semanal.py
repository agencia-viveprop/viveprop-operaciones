"""Reporte semanal: qué se cerró, qué avanzó, qué se cayó, qué está estancado.

Cubre los **dos dominios**. Un reporte de la semana que ignore los 194 canjes
abiertos sería medio reporte, y quien lo lee opera los dos.

**Es un reporte de movimiento, no de estado.** El dashboard responde "cómo
vamos"; esto responde "qué pasó esta semana". Por eso casi todo se calcula desde
`movimientos` y no desde el estado actual de las filas: el estado dice dónde
estamos, el movimiento dice qué cambió.

La excepción es lo cerrado, que se toma de `fecha_cierre`. Es la fecha en que
entró la plata y es más confiable que buscar el movimiento que la marcó.

**"Avanzó" es toda actividad registrada, no solo un cambio de etapa.** En un
reporte semanal lo que importa es donde hubo progreso, y registrar una
confirmacion por WhatsApp es progreso aunque la etapa no se mueva. Ademas los
movimientos migrados del Excel llevan `etapa_resultante` nulo a proposito
(D-030), asi que filtrar por cambio de etapa dejaria el reporte vacio sobre toda
la historia previa. Cuando el movimiento si mueve la etapa, se dice.

**Un renglón por negocio o por canje, no por movimiento.** Las listas muestran
la **última actualización** de cada uno, con la cuenta de cuántos registros tuvo
en la ventana. Un renglón por movimiento repetía la misma referencia tres veces y
obligaba a leer las tres para saber en qué quedó. Por eso los totales de la
sección cuentan **entidades** y los movimientos van en un campo aparte: una lista
de doce renglones bajo una cifra que dice 23 es el desajuste que se arregló en la
bandeja, y no vale repetirlo acá.

**Los movimientos con fecha de carga no cuentan como actividad de la ventana.**
Una limpieza marcó como cancelados 215 canjes que Dataprop dejó de exportar y les
creó el movimiento con la fecha del día en que corrió: en una ventana que incluye
ese día, «Se cayó» mostraba 215 sobre 303 canjes. Se descuentan y se informan
aparte --nunca en silencio--. El criterio está en `_fecha_puesta_por_la_carga`, y
lo importante es que **no descarta todo lo cargado**: las 11 cancelaciones
migradas del Excel traen fechas reales y siguen contando.

**Estancado** no es un estado guardado, es una ausencia: algo abierto sin
movimiento en más de N días.

**El umbral de estancado es el largo de la ventana.** No es un parámetro
independiente: si la ventana son cuatro semanas, estancado es lo que no se movió
en esas cuatro semanas, y así «Avanzó» y «Estancado» reparten la cartera abierta
en vez de contar dos cosas incomparables. Se puede forzar por parámetro --los
tests lo hacen-- pero el default sale de la ventana.

**Y se mide al cierre de la ventana, no contra hoy.** Antes se medía siempre
contra `ahora`, así que al navegar cuatro semanas atrás las tres primeras cifras
cambiaban y «Estancado» seguía mostrando el estancamiento de hoy. Un período
pasado tiene que decir lo que decía al terminar, o no se puede comparar con el
que sigue.
"""
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.canje import (
    ETAPA_LABELS,
    OPERACION_LABELS,
    Canje,
    CanjeEstado,
    CanjeEtapa,
)
from app.models.catalogo import Catalogo, EstadoNegocio, Etapa
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.negocio import Negocio, NegocioHito, Propiedad

CERO = Decimal("0")

# Tipos que significan "el negocio no prosperó".
CAIDA_NEGOCIO = ("NEG_PERDIDA", "NEG_DESISTIMIENTO")
CAIDA_CANJE = ("CANCELACION",)
TOPE_LISTA = 25

# Los rótulos de etapa de canje, indexados por el valor guardado:
# `movimientos.etapa_resultante` es texto y puede traer algo que ya no esté en el
# enum, así que se busca por clave y no se construye el enum.
LABELS_CANJE = {etapa.value: texto for etapa, texto in ETAPA_LABELS.items()}


class Ubicacion(BaseModel):
    """De qué propiedad se está hablando.

    Va en las cuatro listas de las dos secciones. La referencia sola --«VVP-15»,
    «#344»-- no le dice nada a quien lee el reporte sin abrir otra pantalla, y el
    reporte se lee justamente para decidir a quién llamar hoy.

    `alianza` es de negocios y `operacion` de canjes: cada dominio llena la suya.
    """

    direccion: str | None = None
    comuna: str | None = None
    alianza: str | None = None
    operacion: str | None = None


class ItemCerrado(Ubicacion):
    referencia: str
    detalle: str | None = None
    fecha: date | None = None
    monto: Decimal | None = None


class ItemMovido(Ubicacion):
    referencia: str
    fecha: date
    # Dónde quedó: la etapa que dejó el movimiento, o la actual si no la movió.
    # Así la columna nunca queda muda, que es lo que pasaba con los movimientos
    # migrados del Excel --etapa nula a propósito-- donde salía "—" en fila.
    etapa: str | None = None
    etapa_nombre: str | None = None
    # Si el último movimiento cambió la etapa, o fue gestión sin mover el
    # pipeline. Las dos cosas son avance, pero no son la misma cosa.
    movio_etapa: bool = False
    # Qué pasó, en dos piezas: el tipo de movimiento --la categoría, «Respuesta
    # Corredor»-- y el comentario que se escribió --el detalle del caso--.
    #
    # Van **separadas y no pegadas de este lado**: la primera versión mandaba una
    # sola cadena, y en canjes traía el tipo y tiraba el comentario, así que el
    # dato más específico de cada registro no llegaba a la pantalla. Pegarlas es
    # decisión de presentación; el reporte manda los dos hechos.
    tipo: str | None = None
    comentario: str | None = None
    # Cuántos movimientos tuvo en la ventana, contando este.
    registros: int = 1


class ItemEstancado(Ubicacion):
    referencia: str
    etapa: str | None = None
    etapa_nombre: str | None = None
    dias_sin_movimiento: int | None = None
    # Nunca se le registró nada: la cuenta corre desde su fecha de origen.
    sin_gestion: bool = False


class Seccion(BaseModel):
    cerrados: list[ItemCerrado]
    monto_cerrado: Decimal
    avanzados: list[ItemMovido]
    caidos: list[ItemMovido]
    estancados: list[ItemEstancado]
    # Los totales van aparte porque las listas están topeadas.
    total_cerrados: int
    total_avanzados: int
    total_caidos: int
    total_estancados: int
    # Movimientos, no entidades: `total_avanzados` cuenta negocios o canjes con
    # actividad y este cuenta los registros que hicieron. Los dos números
    # importan y no son el mismo.
    movimientos_avanzados: int
    # Movimientos de la ventana cuya fecha la puso un proceso masivo y no la
    # gestión: se descuentan de todas las cifras y se informan acá. Si se
    # descartaran en silencio, la pantalla diría 0 donde el usuario sabe que hay
    # 215 registros, y eso se lee como que el reporte no funciona.
    movimientos_con_fecha_de_carga: int = 0


class ReporteSemanal(BaseModel):
    desde: date
    hasta: date
    dias_estancado: int
    negocios: Seccion
    canjes: Seccion


def semana_de(referencia: date) -> tuple[date, date]:
    """El lunes y el domingo de la semana que contiene esa fecha."""
    lunes = referencia - timedelta(days=referencia.weekday())
    return lunes, lunes + timedelta(days=6)


def _rango_utc(desde: date, hasta: date) -> tuple[datetime, datetime]:
    """El intervalo completo, con el último día incluido."""
    return (
        datetime.combine(desde, time.min, tzinfo=timezone.utc),
        datetime.combine(hasta, time.max, tzinfo=timezone.utc),
    )


def _ultimos_movimientos(db: Session, tipo: EntityType):
    return (
        select(
            Movimiento.entity_id.label("entity_id"),
            func.max(Movimiento.fecha).label("fecha"),
        )
        .where(Movimiento.entity_type == tipo)
        .group_by(Movimiento.entity_id)
        .subquery()
    )


def _dias(corte: datetime, fecha) -> int | None:
    if fecha is None:
        return None
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return (corte - fecha).days


def _instantes_de_carga(db: Session, tipo: EntityType) -> set[datetime]:
    """Los `creado_en` que comparte más de un movimiento: una carga masiva.

    Dos movimientos con el mismo timestamp **al microsegundo** entraron en la
    misma transacción. No hace falta ninguna marca ni ninguna constante: esa
    coincidencia exacta no pasa por casualidad. Es el mismo criterio con el que el
    reporte de canjes activos distingue lo cargado de lo registrado a mano.
    """
    return {
        instante
        for (instante,) in db.execute(
            select(Movimiento.creado_en)
            .where(Movimiento.entity_type == tipo)
            .group_by(Movimiento.creado_en)
            .having(func.count() > 1)
        ).all()
    }


def _fecha_puesta_por_la_carga(fecha, creado_en, cargas: set[datetime]) -> bool:
    """Si la fecha de ese movimiento la inventó el proceso que lo cargó.

    **El caso que esto resuelve.** Una limpieza marcó como cancelados 215 canjes
    que Dataprop dejó de exportar, y les creó el movimiento de cancelación con la
    fecha del día en que corrió. En una ventana que incluye ese día, «Se cayó»
    mostraba 215 --sobre 303 canjes-- cuando en realidad esos canjes se cayeron en
    algún momento desconocido de los últimos años. La cifra era cierta sobre los
    movimientos y falsa sobre el negocio.

    **No alcanza con "vino de una carga".** El otro grupo cargado --11
    cancelaciones migradas del Excel-- trae fechas reales, de 2024 a 2026, porque
    el archivo las tenía. Esas sí pertenecen a la ventana donde caen y tienen que
    contar. La diferencia no es cómo entraron, es si la fecha es un dato o un
    subproducto: **el script estampó "hoy"**.

    Por eso hacen falta las dos condiciones. Y por eso tampoco alcanza con mirar
    solo la coincidencia de fechas: una cancelación que alguien registra hoy en la
    app también tiene `fecha` de hoy, y esa es una gestión real. Lo que la
    distingue es que su `creado_en` no lo comparte nadie.
    """
    if creado_en is None or creado_en not in cargas:
        return False
    if creado_en.tzinfo is None:
        creado_en = creado_en.replace(tzinfo=timezone.utc)
    return fecha.date() == creado_en.date()


def _direccion(calle: str | None, unidad: str | None) -> str | None:
    """La dirección como se dice en voz alta, con la unidad si la hay."""
    if not calle:
        return None
    return f"{calle} {unidad}" if unidad else calle


def _nombres_de_etapa(db: Session) -> dict[str, str]:
    """`{codigo: nombre}` de las etapas de negocio.

    La tabla tiene siete filas: traerla completa una vez sale más barato que
    unirla en cada consulta, y deja el nombre disponible también cuando la etapa
    viene del negocio y no del movimiento.
    """
    return {codigo: nombre for codigo, nombre in db.execute(select(Etapa.codigo, Etapa.nombre)).all()}


def _ultimo_por_referencia(items: list[ItemMovido]) -> list[ItemMovido]:
    """Un renglón por entidad: el último movimiento, contando los anteriores.

    Recibe la lista en orden ascendente de fecha, así que el que pisa cada clave
    al final es el más reciente. Devuelve del más nuevo al más viejo: con la lista
    topeada, lo que hay que dejar afuera es lo viejo.
    """
    ultimos: dict[str, ItemMovido] = {}
    for item in items:
        previo = ultimos.get(item.referencia)
        if previo is not None:
            item.registros = previo.registros + 1
        ultimos[item.referencia] = item
    return sorted(ultimos.values(), key=lambda i: i.fecha, reverse=True)


# --------------------------------------------------------------- negocios


def _seccion_negocios(db: Session, desde: date, hasta: date, dias: int, corte: datetime) -> Seccion:
    inicio, fin = _rango_utc(desde, hasta)
    etapas = _nombres_de_etapa(db)

    filas_cerradas = db.execute(
        select(Negocio.codigo, NegocioHito.nombre, NegocioHito.fecha_cierre,
               NegocioHito.comision_real_vp, Propiedad.direccion, Propiedad.unidad,
               Propiedad.comuna, Catalogo.nombre)
        .join(Negocio, Negocio.id == NegocioHito.negocio_id)
        .join(Propiedad, Propiedad.id == Negocio.propiedad_id)
        .outerjoin(Catalogo, Catalogo.id == Negocio.alianza_id)
        .where(
            NegocioHito.estado == EstadoNegocio.CERRADO,
            NegocioHito.fecha_cierre >= desde,
            NegocioHito.fecha_cierre <= hasta,
        )
        .order_by(NegocioHito.fecha_cierre)
    ).all()
    cerrados = [
        ItemCerrado(referencia=cod, detalle=nombre, fecha=f, monto=monto or CERO,
                    direccion=_direccion(calle, unidad), comuna=comuna, alianza=alianza)
        for cod, nombre, f, monto, calle, unidad, comuna, alianza in filas_cerradas
    ]
    monto_cerrado = sum((c.monto or CERO for c in cerrados), CERO)

    cargas = _instantes_de_carga(db, EntityType.negocio)
    movidos = db.execute(
        select(Negocio.codigo, Movimiento.fecha, Movimiento.etapa_resultante,
               Movimiento.comentario, Movimiento.tipo_movimiento, Negocio.etapa,
               Propiedad.direccion, Propiedad.unidad, Propiedad.comuna, Catalogo.nombre,
               TipoMovimiento.nombre, Movimiento.creado_en)
        .join(Negocio, Negocio.id == Movimiento.entity_id)
        .join(Propiedad, Propiedad.id == Negocio.propiedad_id)
        .join(TipoMovimiento, TipoMovimiento.codigo == Movimiento.tipo_movimiento)
        .outerjoin(Catalogo, Catalogo.id == Negocio.alianza_id)
        .where(
            Movimiento.entity_type == EntityType.negocio,
            Movimiento.fecha >= inicio,
            Movimiento.fecha <= fin,
        )
        # El id desempata los del mismo instante: sin eso, cuál es "el último"
        # queda a criterio del plan de la consulta.
        .order_by(Movimiento.fecha, Movimiento.id)
    ).all()

    # La fecha de estos movimientos la puso el proceso que los cargó, así que no
    # dicen nada sobre la ventana. Se cuentan aparte y la pantalla los informa.
    descartados = [f for f in movidos if _fecha_puesta_por_la_carga(f[1], f[11], cargas)]
    movidos = [f for f in movidos if not _fecha_puesta_por_la_carga(f[1], f[11], cargas)]

    def _item(fila) -> ItemMovido:
        (cod, f, etapa_mov, com, _tipo, etapa_actual, calle, unidad, comuna,
         alianza, nombre_tipo, _creado) = fila
        etapa = etapa_mov or etapa_actual
        return ItemMovido(
            referencia=cod,
            fecha=f.date(),
            etapa=etapa,
            etapa_nombre=etapas.get(etapa) if etapa else None,
            movio_etapa=etapa_mov is not None,
            tipo=nombre_tipo,
            comentario=com,
            direccion=_direccion(calle, unidad),
            comuna=comuna,
            alianza=alianza,
        )

    # Actividad que no sea una caida: esas se listan aparte y contarlas en las
    # dos columnas seria contar el mismo hecho dos veces.
    planos = [_item(f) for f in movidos if f[4] not in CAIDA_NEGOCIO]
    avanzados = _ultimo_por_referencia(planos)
    caidos = _ultimo_por_referencia([
        # Una caída no es una etapa del pipeline: es su final.
        _item(f).model_copy(update={"etapa": None, "etapa_nombre": None, "movio_etapa": False})
        for f in movidos
        if f[4] in CAIDA_NEGOCIO
    ])

    ultimos = _ultimos_movimientos(db, EntityType.negocio)
    filas_abiertas = db.execute(
        select(Negocio.codigo, Negocio.etapa, ultimos.c.fecha, NegocioHito.fecha_inicio,
               Propiedad.direccion, Propiedad.unidad, Propiedad.comuna, Catalogo.nombre)
        .join(NegocioHito, NegocioHito.negocio_id == Negocio.id)
        .join(Propiedad, Propiedad.id == Negocio.propiedad_id)
        .outerjoin(Catalogo, Catalogo.id == Negocio.alianza_id)
        .outerjoin(ultimos, ultimos.c.entity_id == Negocio.id)
        .where(NegocioHito.estado == EstadoNegocio.ACTIVO)
    ).all()

    # Un negocio con dos hitos activos trae dos filas. Se queda con la referencia
    # más vieja, que es la que da el estancamiento mayor: si no se le registró
    # nada, el hito que empezó antes es el que lleva más tiempo esperando.
    por_negocio: dict[str, tuple] = {}
    for cod, etapa, ultima, inicio_hito, calle, unidad, comuna, alianza in filas_abiertas:
        referencia = ultima or datetime.combine(inicio_hito, time.min, tzinfo=timezone.utc)
        if referencia.tzinfo is None:
            referencia = referencia.replace(tzinfo=timezone.utc)
        previo = por_negocio.get(cod)
        if previo is None or referencia < previo[0]:
            por_negocio[cod] = (referencia, etapa, ultima, calle, unidad, comuna, alianza)

    estancados = []
    for cod, (referencia, etapa, ultima, calle, unidad, comuna, alianza) in por_negocio.items():
        transcurridos = _dias(corte, referencia)
        if transcurridos is not None and transcurridos > dias:
            estancados.append(
                ItemEstancado(
                    referencia=cod,
                    etapa=etapa,
                    etapa_nombre=etapas.get(etapa) if etapa else None,
                    dias_sin_movimiento=transcurridos,
                    sin_gestion=ultima is None,
                    direccion=_direccion(calle, unidad),
                    comuna=comuna,
                    alianza=alianza,
                )
            )
    estancados.sort(key=lambda e: -(e.dias_sin_movimiento or 0))

    return Seccion(
        cerrados=cerrados[:TOPE_LISTA],
        monto_cerrado=monto_cerrado,
        avanzados=avanzados[:TOPE_LISTA],
        caidos=caidos[:TOPE_LISTA],
        estancados=estancados[:TOPE_LISTA],
        total_cerrados=len(cerrados),
        total_avanzados=len(avanzados),
        total_caidos=len(caidos),
        total_estancados=len(estancados),
        movimientos_avanzados=len(planos),
        movimientos_con_fecha_de_carga=len(descartados),
    )


# ----------------------------------------------------------------- canjes


def _operacion(tipo) -> str | None:
    return OPERACION_LABELS.get(tipo) if tipo else None


def _seccion_canjes(db: Session, desde: date, hasta: date, dias: int, corte: datetime) -> Seccion:
    inicio, fin = _rango_utc(desde, hasta)

    filas_cerradas = db.execute(
        select(Canje.id, Canje.corredor_solicitante_nombre, Canje.fecha_cierre,
               Canje.tipo_operacion, Canje.direccion, Canje.comuna)
        .where(
            Canje.etapa == CanjeEtapa.CERRADO,
            Canje.fecha_cierre >= inicio,
            Canje.fecha_cierre <= fin,
        )
        .order_by(Canje.fecha_cierre)
    ).all()
    cerrados = [
        ItemCerrado(referencia=f"#{cid}", detalle=corredor, fecha=f.date() if f else None,
                    operacion=_operacion(op), direccion=calle, comuna=comuna)
        for cid, corredor, f, op, calle, comuna in filas_cerradas
    ]

    cargas = _instantes_de_carga(db, EntityType.canje)
    movidos = db.execute(
        select(Movimiento.entity_id, Movimiento.fecha, Movimiento.etapa_resultante,
               Movimiento.comentario, Movimiento.tipo_movimiento, TipoMovimiento.nombre,
               Canje.etapa, Canje.tipo_operacion, Canje.direccion, Canje.comuna,
               Movimiento.creado_en)
        .join(Canje, Canje.id == Movimiento.entity_id)
        .join(TipoMovimiento, TipoMovimiento.codigo == Movimiento.tipo_movimiento)
        .where(
            Movimiento.entity_type == EntityType.canje,
            Movimiento.fecha >= inicio,
            Movimiento.fecha <= fin,
        )
        .order_by(Movimiento.fecha, Movimiento.id)
    ).all()

    # Los 215 de la limpieza del 21-08 caen acá: su fecha es la del script.
    descartados = [f for f in movidos if _fecha_puesta_por_la_carga(f[1], f[10], cargas)]
    movidos = [f for f in movidos if not _fecha_puesta_por_la_carga(f[1], f[10], cargas)]

    def _item(fila) -> ItemMovido:
        cid, f, etapa_mov, com, _tipo, nombre_tipo, etapa_actual, op, calle, comuna, _creado = fila
        etapa = etapa_mov or (etapa_actual.value if etapa_actual else None)
        return ItemMovido(
            referencia=f"#{cid}",
            fecha=f.date(),
            etapa=etapa,
            etapa_nombre=LABELS_CANJE.get(etapa, etapa) if etapa else None,
            movio_etapa=etapa_mov is not None,
            tipo=nombre_tipo,
            comentario=com,
            operacion=_operacion(op),
            direccion=calle,
            comuna=comuna,
        )

    planos = [_item(f) for f in movidos if f[4] not in CAIDA_CANJE]
    avanzados = _ultimo_por_referencia(planos)
    caidos = _ultimo_por_referencia([
        _item(f).model_copy(update={"etapa": None, "etapa_nombre": None, "movio_etapa": False})
        for f in movidos
        if f[4] in CAIDA_CANJE
    ])

    # Abierto es lo mismo que en la bandeja: activo y con etapa distinta de
    # cerrada, para no contar como pendientes los 31 que arrastran el
    # desalineamiento del dato de Dataprop.
    ultimos = _ultimos_movimientos(db, EntityType.canje)
    filas_abiertas = db.execute(
        select(Canje.id, Canje.etapa, ultimos.c.fecha, Canje.fecha_solicitud,
               Canje.tipo_operacion, Canje.direccion, Canje.comuna)
        .outerjoin(ultimos, ultimos.c.entity_id == Canje.id)
        .where(Canje.estado == CanjeEstado.ACTIVO, Canje.etapa != CanjeEtapa.CERRADO)
    ).all()

    estancados = []
    for cid, etapa, ultima, solicitud, op, calle, comuna in filas_abiertas:
        referencia = ultima or solicitud
        transcurridos = _dias(corte, referencia)
        if transcurridos is not None and transcurridos > dias:
            estancados.append(
                ItemEstancado(
                    referencia=f"#{cid}",
                    etapa=etapa.value,
                    etapa_nombre=LABELS_CANJE.get(etapa.value, etapa.value),
                    dias_sin_movimiento=transcurridos,
                    sin_gestion=ultima is None,
                    operacion=_operacion(op),
                    direccion=calle,
                    comuna=comuna,
                )
            )
    estancados.sort(key=lambda e: -(e.dias_sin_movimiento or 0))

    return Seccion(
        cerrados=cerrados[:TOPE_LISTA],
        monto_cerrado=CERO,  # los canjes no llevan comisión propia en la app
        avanzados=avanzados[:TOPE_LISTA],
        caidos=caidos[:TOPE_LISTA],
        estancados=estancados[:TOPE_LISTA],
        total_cerrados=len(cerrados),
        total_avanzados=len(avanzados),
        total_caidos=len(caidos),
        total_estancados=len(estancados),
        movimientos_avanzados=len(planos),
        movimientos_con_fecha_de_carga=len(descartados),
    )


def obtener_reporte_semanal(
    db: Session,
    desde: date | None = None,
    hasta: date | None = None,
    dias_estancado: int | None = None,
    ahora: datetime | None = None,
) -> ReporteSemanal:
    ahora = ahora or datetime.now(timezone.utc)
    if desde is None or hasta is None:
        desde, hasta = semana_de(ahora.date())

    # El umbral es el largo de la ventana, así que las cuatro cifras hablan del
    # mismo período y no hay dos controles diciendo cosas distintas.
    if dias_estancado is None:
        dias_estancado = (hasta - desde).days + 1

    # Al cierre de la ventana, o ahora si la ventana todavía no termina.
    corte = min(ahora, datetime.combine(hasta, time.max, tzinfo=timezone.utc))

    return ReporteSemanal(
        desde=desde,
        hasta=hasta,
        dias_estancado=dias_estancado,
        negocios=_seccion_negocios(db, desde, hasta, dias_estancado, corte),
        canjes=_seccion_canjes(db, desde, hasta, dias_estancado, corte),
    )
