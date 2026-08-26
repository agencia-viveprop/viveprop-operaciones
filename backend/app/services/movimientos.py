from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.canje import ETAPA_LABELS, Canje, CanjeEstado, CanjeEtapa, CorredorCanje
from app.models.catalogo import EstadoNegocio
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.negocio import Negocio


class MovimientoError(Exception):
    pass


# Margen para el desfase entre el reloj del navegador y el del servidor. Sin él,
# registrar un movimiento "ahora" desde una máquina un minuto adelantada se
# rechazaría por venir del futuro.
HOLGURA_RELOJ = timedelta(minutes=5)

# El unico tipo de movimiento de canje que cambia el estado y no solo la etapa.
CANCELACION = "CANCELACION"

# El tipo que registra un cambio de etapa hecho desde la ficha del canje. No se
# ofrece en el selector --nadie lo elige, lo escribe el sistema-- y por eso va
# como `activo = false` en el catalogo.
CAMBIO_ETAPA = "CAMBIO_ETAPA"


# Cuántos días hacia adelante se agenda un seguimiento cuando no se indica uno.
# Son dos números y no uno porque son dos ritmos: un canje se responde en días y
# un negocio dura de un mes a varios.
DIAS_SEGUIMIENTO = 2
DIAS_SEGUIMIENTO_NEGOCIO = 3

# El sábado es 5 y el domingo 6 en `weekday()`.
FIN_DE_SEMANA = (5, 6)


def proximo_habil(desde: date, dias: int = DIAS_SEGUIMIENTO) -> date:
    """`desde` más `dias`, corrido al siguiente día hábil si cae fin de semana.

    **Los feriados no se saltan, y hay que decirlo.** Saltarlos necesita saber
    cuáles son, y los de Chile incluyen movibles --la ley de traslado de San Pedro
    y del 12 de octubre-- más Pascua y los días de elección. Calcularlos mal
    dejaría el error escondido en el código hasta que alguien agende un
    seguimiento para el 18 de septiembre. Se decidió empezar por fines de semana
    y dejar los feriados para cuando haya una lista verificada; hasta entonces la
    pantalla lo declara en vez de dar a entender que los conoce.

    Los días se cuentan de corrido y **después** se corre el resultado, que no es
    lo mismo que contar dos días hábiles: un viernes más dos da domingo, y el
    lunes es el hábil siguiente. Contar hábiles daría martes. Dos días de corrido
    es lo que uno quiere decir con "te llamo en un par de días".
    """
    fecha = desde + timedelta(days=dias)
    while fecha.weekday() in FIN_DE_SEMANA:
        fecha += timedelta(days=1)
    return fecha


def seguimiento_de_negocio(fecha_movimiento: date) -> date:
    """El seguimiento por defecto de un avance de negocio: 3 días.

    **Se cuenta desde la fecha que se registra, no desde hoy**, y eso es distinto
    de canjes a pedido explícito. Tiene una consecuencia que conviene tener
    presente: cargar hoy un avance con fecha de hace un mes agenda un seguimiento
    vencido hace casi un mes, así que el negocio aparece de inmediato como
    atrasado. Es la lectura correcta --se registró algo viejo, su seguimiento ya
    está atrasado-- pero es una decisión, no un efecto secundario.

    El fin de semana se corre igual que en canjes: 3 días de corrido y después el
    resultado se mueve al lunes si cayó sábado o domingo. Los feriados no se
    saltan, por el motivo que explica `proximo_habil`.
    """
    return proximo_habil(fecha_movimiento, DIAS_SEGUIMIENTO_NEGOCIO)


def seguimiento_por_defecto(fecha_movimiento: date, hoy: date) -> date:
    """El seguimiento que se agenda cuando nadie indica uno, en canjes.

    **Se cuenta desde el más nuevo de los dos.** Anclarlo solo a la fecha del
    movimiento haría que anotar hoy una gestión de hace tres meses agendara un
    seguimiento vencido hace tres meses, y la bandeja se llenaría de vencidos que
    nadie prometió. Anclarlo solo a hoy perdería el caso normal --la gestión es de
    hoy y el seguimiento sale de ella--. Tomando el mayor, los dos casos dan lo
    que uno esperaría.
    """
    return proximo_habil(max(fecha_movimiento, hoy))


def _etapa_vigente(db: Session, tipo: EntityType, entity_id: int) -> str | None:
    """La etapa del movimiento **más reciente** que traiga una, no la del último
    que se guardó.

    **Por qué no es lo mismo.** Desde que la fecha del movimiento se puede
    atrasar, el último que se inserta no es necesariamente el más nuevo. Sin esto,
    anotar el lunes una gestión del día 10 en un canje que el día 20 ya había
    pasado a «En negocio» lo devolvía a «En revisión»: la etapa retrocedía sola,
    contra un movimiento posterior que seguía ahí. Medido antes de arreglarlo.

    Se resuelve leyendo, no acumulando: la etapa vigente es una consecuencia de la
    línea de tiempo, así que se deriva de ella.
    """
    return db.scalar(
        select(Movimiento.etapa_resultante)
        .where(
            Movimiento.entity_type == tipo,
            Movimiento.entity_id == entity_id,
            Movimiento.etapa_resultante.is_not(None),
        )
        .order_by(Movimiento.fecha.desc(), Movimiento.id.desc())
        .limit(1)
    )


def _validar_fecha(fecha: datetime | None, minimo: datetime | None, que_es_el_minimo: str) -> None:
    """La fecha de un movimiento se puede atrasar, no adelantar.

    **Por qué hace falta.** La pantalla dejó de fijar la fecha en "ahora" para que
    se pueda registrar gestión de días pasados, que es el caso real: uno anota el
    lunes lo que pasó el viernes. Pero la API acepta cualquier `datetime`, y una
    fecha futura envenena el reloj de la bandeja --`horas_sin_gestion` es
    `ahora - ultimo_movimiento`, así que daría **horas negativas** en pantalla-- y
    con ella el semáforo y el reporte semanal.

    Y una fecha anterior a que la cosa existiera tampoco es un dato: es un error
    de tipeo. Se rechaza con el mínimo a la vista, para que se vea cuál era.
    """
    if fecha is None:
        return

    # Una fecha sin zona viene del navegador ya convertida a UTC; se asume así en
    # vez de rechazarla, que es lo que hace el resto del proyecto.
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)

    ahora = datetime.now(timezone.utc)
    if fecha > ahora + HOLGURA_RELOJ:
        raise MovimientoError(
            f"La fecha del movimiento no puede ser futura: {fecha:%d-%m-%Y %H:%M}. "
            "La gestión se registra después de que pasa, no antes."
        )

    if minimo is not None:
        if minimo.tzinfo is None:
            minimo = minimo.replace(tzinfo=timezone.utc)
        if fecha < minimo:
            raise MovimientoError(
                f"La fecha del movimiento ({fecha:%d-%m-%Y}) es anterior a "
                f"{que_es_el_minimo} ({minimo:%d-%m-%Y})."
            )


def crear_movimiento_canje(
    db: Session,
    canje_id: int,
    tipo_codigo: str,
    autor_id: int | None,
    comentario: str | None = None,
    fecha: datetime | None = None,
    proximo_seguimiento: date | None = None,
    etapa: CanjeEtapa | None = None,
    corredor: CorredorCanje | None = None,
) -> Movimiento:
    """Registra la gestión y agenda cuándo hay que volver a mirar el canje.

    **`corredor` es optativo a propósito.** Dice sobre cuál de los dos se hizo la
    gestión, y hay movimientos que no son sobre ninguno --una cancelación, un
    comentario general--. Forzarlo obligaría a poner un dato falso en esos casos.

    **`etapa` y `tipo_codigo` son dos datos distintos y conviven.** El tipo dice
    qué se hizo --una llamada, un WhatsApp-- y la etapa dónde quedó el canje. Antes
    la etapa salía implícita del tipo, lo que ataba las dos cosas: con una llamada
    de seguimiento no había forma de decir que el canje avanzó, ni de avanzarlo sin
    inventar un tipo que lo hiciera.

    Si no se indica etapa se cae al `etapa_resultante` del tipo, que es lo que
    hacía antes. Eso mantiene funcionando a quien llame sin el parámetro --la
    migración de cancelación masiva, por ejemplo-- y deja el cambio aditivo.

    `proximo_seguimiento` es opcional: si no viene, se agenda para dos días
    corridos después, corrido al siguiente hábil si cae fin de semana. **Nunca
    queda en nulo**, porque un canje sin seguimiento agendado vuelve a depender
    del reloj de horas sin gestión, que es el proxy que esto vino a reemplazar.
    """
    canje = db.get(Canje, canje_id)
    if canje is None:
        raise MovimientoError("Canje no encontrado")

    tipo = db.get(TipoMovimiento, tipo_codigo)
    if tipo is None or tipo.entity_type != EntityType.canje:
        raise MovimientoError("Tipo de movimiento inválido para Canjes")

    _validar_fecha(fecha, canje.fecha_solicitud, "la fecha de solicitud del canje")

    # La etapa elegida gana sobre la del tipo. Se guarda como texto en el
    # movimiento --igual que antes-- para que la línea de tiempo diga a dónde
    # movió cada gestión.
    etapa_del_registro = etapa.value if etapa is not None else tipo.etapa_resultante

    hoy = datetime.now(timezone.utc).date()
    fecha_base = (fecha or datetime.now(timezone.utc)).date()

    movimiento = Movimiento(
        entity_type=EntityType.canje,
        entity_id=canje_id,
        tipo_movimiento=tipo.codigo,
        etapa_resultante=etapa_del_registro,
        corredor=corredor.value if corredor is not None else None,
        autor_id=autor_id,
        comentario=comentario,
        proximo_seguimiento=(
            proximo_seguimiento
            if proximo_seguimiento is not None
            else seguimiento_por_defecto(fecha_base, hoy)
        ),
        **({"fecha": fecha} if fecha is not None else {}),
    )
    db.add(movimiento)

    # Se necesita el movimiento en la base para que entre en la comparacion de
    # fechas; el commit viene despues igual.
    db.flush()
    vigente = _etapa_vigente(db, EntityType.canje, canje_id)
    if vigente is not None:
        canje.etapa = CanjeEtapa(vigente)

    # La cancelacion no se recalcula desde la linea de tiempo: un canje que se
    # canceló quedó cancelado, y que despues alguien anote otra gestion no lo
    # revive. Deshacerlo es una edicion manual, no un movimiento.
    if tipo.codigo == CANCELACION:
        canje.estado = CanjeEstado.CANCELADO
    canje.gestionado_en_app = True

    db.commit()
    db.refresh(movimiento)
    return movimiento


def registrar_cambio_de_etapa(
    db: Session,
    canje: Canje,
    anterior: CanjeEtapa,
    nueva: CanjeEtapa,
    autor_id: int | None,
) -> Movimiento:
    """Deja en la bitácora un cambio de etapa hecho desde la ficha del canje.

    **Por qué hace falta.** La etapa se puede cambiar por dos caminos: registrando
    un movimiento, o editando la ficha. El primero quedaba en la línea de tiempo y
    el segundo no, así que la ficha podía decir «En oferta» mientras la bitácora
    seguía mostrando que el último movimiento la había dejado en «En negocio».
    Peor para lo que esto sirve: un cambio de etapa sin rastro no tiene fecha ni
    autor, y un reporte de línea de tiempo no lo ve.

    **No agenda seguimiento.** Corregir un dato no es una gestión: agendar uno
    metería el canje en «Qué me toca hoy» por una razón que nadie eligió. Por eso
    la bandeja toma el último compromiso **que exista**, y no el del último
    movimiento: si no, este registro borraría el que había.

    No comitea: lo hace quien llama, en la misma transacción que el cambio.
    """
    movimiento = Movimiento(
        entity_type=EntityType.canje,
        entity_id=canje.id,
        tipo_movimiento=CAMBIO_ETAPA,
        etapa_resultante=nueva.value,
        autor_id=autor_id,
        # Los rótulos y no los códigos: el comentario lo lee una persona en la
        # línea de tiempo, y «EN_OFERTA» ahí es ruido.
        comentario=(
            f"De «{ETAPA_LABELS[anterior]}» a «{ETAPA_LABELS[nueva]}». "
            "Editado desde la ficha del canje."
        ),
    )
    db.add(movimiento)
    return movimiento


def eliminar_movimiento_canje(db: Session, canje_id: int, movimiento_id: int) -> None:
    """Borra un movimiento y deja el canje como si nunca se hubiera registrado.

    **Por qué existe.** Se podían agregar movimientos y no sacarlos, así que un
    tipeo --un tipo equivocado, una gestión anotada en el canje de al lado--
    quedaba para siempre, moviendo la etapa y el reloj del semáforo. Corregirlo
    exigía tocar la base a mano.

    **Es un borrado de verdad, no un anulado.** Un movimiento marcado como
    "anulado" obliga a filtrarlo en la línea de tiempo, en el semáforo, en el
    reporte semanal y en el cálculo de la etapa: cinco lugares donde olvidarlo
    produce un número mal. Y lo que queda no es historia útil sino ruido: "acá
    hubo algo que no pasó". Para dos personas corrigiendo sus propios registros,
    el borrado es lo proporcionado.

    **Lo que arrastra se recalcula, no se adivina.**

    - La etapa se vuelve a derivar de los movimientos que quedan **cuando alguno
      declara una**. Si ninguno lo hace, la etapa del canje **no se toca**.

      La primera versión la devolvía a `RECEPCION` en ese caso, razonando que la
      etapa la había puesto el movimiento borrado. Eso es cierto para un canje
      creado en la app y **falso para los 297 que vinieron de Dataprop**: su
      etapa la trajo el export, y ninguno de sus movimientos migrados declara
      una. Medido: borrar cualquier movimiento del canje 360 lo mandaba de «En
      oferta» a «Recepción», perdiendo un dato que el borrado no había puesto.
      Quedarse con una etapa vieja es preferible a borrar una que era correcta.
    - Si el borrado era la cancelación y no queda otra, el canje vuelve a
      `ACTIVO`. Registrarla fue el error, así que el canje no estaba cancelado.
    - **`gestionado_en_app` no se toca.** Es tentador devolverlo a `False` cuando
      no quedan movimientos, pero no lo pone solo el seguimiento: también lo pone
      crear o editar el canje a mano. Revertirlo dejaría que la próxima
      importación sobreescriba en silencio datos corregidos por una persona.
    """
    canje = db.get(Canje, canje_id)
    if canje is None:
        raise MovimientoError("Canje no encontrado")

    movimiento = db.get(Movimiento, movimiento_id)
    if (
        movimiento is None
        or movimiento.entity_type != EntityType.canje
        or movimiento.entity_id != canje_id
    ):
        raise MovimientoError(
            f"El movimiento {movimiento_id} no pertenece al canje {canje_id}."
        )

    era_cancelacion = movimiento.tipo_movimiento == CANCELACION
    db.delete(movimiento)
    # Sin el flush, el movimiento borrado seguiria contando en las dos consultas
    # de abajo y el recalculo daria lo mismo que antes.
    db.flush()

    # Solo se mueve si queda quien sostenga una etapa. Ver el docstring: resetear
    # cuando no queda ninguna borraba la etapa que vino del import.
    vigente = _etapa_vigente(db, EntityType.canje, canje_id)
    if vigente is not None:
        canje.etapa = CanjeEtapa(vigente)

    if era_cancelacion:
        queda_otra = db.scalar(
            select(Movimiento.id)
            .where(
                Movimiento.entity_type == EntityType.canje,
                Movimiento.entity_id == canje_id,
                Movimiento.tipo_movimiento == CANCELACION,
            )
            .limit(1)
        )
        if queda_otra is None:
            canje.estado = CanjeEstado.ACTIVO

    db.commit()


# Estos tipos no mueven el negocio en el pipeline, cambian el desenlace de sus
# liquidaciones abiertas. El estado vive en el hito (ver D-027), asi que se
# aplica ahi y no en el negocio.
DESENLACES = {
    "NEG_PERDIDA": EstadoNegocio.PERDIDO,
    "NEG_DESISTIMIENTO": EstadoNegocio.DESISTIDO,
}


def crear_movimiento_negocio(
    db: Session,
    negocio_id: int,
    tipo_codigo: str,
    autor_id: int | None,
    comentario: str | None = None,
    fecha: datetime | None = None,
    proximo_seguimiento: date | None = None,
) -> Movimiento:
    """Registra un movimiento y, si el tipo lo dice, avanza el negocio de etapa.

    **`proximo_seguimiento` es optativo y cuando no viene se agenda solo**, a 3
    días de la fecha del avance (`seguimiento_de_negocio`). Nunca queda en nulo
    por omisión: un avance registrado siempre deja un próximo paso comprometido,
    que es lo que hace que la bandeja pueda ordenarse por lo prometido en vez de
    solo por el tiempo que pasó.

    `movimientos.entity_id` no tiene ni puede tener clave foranea porque apunta a
    dos tablas (canje o negocio). Por eso la existencia del negocio se verifica
    aca, igual que hace `crear_movimiento_canje` con el canje.
    """
    negocio = db.get(Negocio, negocio_id)
    if negocio is None:
        raise MovimientoError(f"No existe el negocio {negocio_id}")

    tipo = db.get(TipoMovimiento, tipo_codigo)
    if tipo is None or tipo.entity_type != EntityType.negocio:
        raise MovimientoError(f"Tipo de movimiento invalido para Negocios: '{tipo_codigo}'")

    # El mínimo es el hito más antiguo: un negocio empieza cuando empieza su
    # primera liquidación. Sin hitos no hay mínimo que exigir, solo el futuro.
    inicio = min((h.fecha_inicio for h in negocio.hitos if h.fecha_inicio), default=None)
    _validar_fecha(
        fecha,
        datetime.combine(inicio, datetime.min.time(), tzinfo=timezone.utc) if inicio else None,
        "la fecha de inicio del negocio",
    )

    momento = fecha or datetime.now(timezone.utc)
    movimiento = Movimiento(
        entity_type=EntityType.negocio,
        entity_id=negocio_id,
        tipo_movimiento=tipo.codigo,
        etapa_resultante=tipo.etapa_resultante,
        autor_id=autor_id,
        comentario=comentario,
        proximo_seguimiento=(
            proximo_seguimiento
            if proximo_seguimiento is not None
            else seguimiento_de_negocio(momento.date())
        ),
        **({"fecha": fecha} if fecha is not None else {}),
    )
    db.add(movimiento)

    db.flush()
    vigente = _etapa_vigente(db, EntityType.negocio, negocio_id)
    if vigente is not None:
        negocio.etapa = vigente

    if tipo.codigo in DESENLACES:
        nuevo = DESENLACES[tipo.codigo]
        # Solo las liquidaciones que siguen abiertas: una promesa ya cerrada no
        # se vuelve perdida porque la escritura se cayo.
        for hito in negocio.hitos:
            if hito.estado == EstadoNegocio.ACTIVO:
                hito.estado = nuevo

    db.commit()
    db.refresh(movimiento)
    return movimiento
