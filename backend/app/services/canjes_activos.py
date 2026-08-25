"""Listado de canjes activos con su estado de gestión.

Es un **reporte**, no una lista de trabajo, y esa diferencia explica todo lo que
lo separa de `bandeja_canjes`:

| | «Qué me toca hoy» | Este listado |
|---|---|---|
| Para qué | qué llamar hoy | cómo viene cada canje abierto |
| Qué muestra | lo que hay que tocar | **todos** los activos |
| Agendados a futuro | los esconde | los muestra, con su fecha |
| Estados | seis niveles | dos: al día o pendiente |

Los agendados a futuro son el caso que más los separa. La bandeja los saca de la
vista a propósito --si te comprometiste a llamar el jueves, el martes no es tu
problema--, pero un reporte que esconde filas no es un reporte: alguien lo lee
para saber cuántos canjes abiertos hay, y ese número tiene que estar completo.

**El estado se calcula sobre `fecha`, no sobre `creado_en`.** Son dos columnas
distintas y la diferencia importa: `fecha` es cuándo se hizo la gestión --la
elige la persona en el modal-- y `creado_en` es cuándo quedó registrada, que la
pone el servidor. "Hace cuánto que nadie toca este canje" es una pregunta sobre
el trabajo, no sobre cuándo se tipeó, así que manda `fecha`.

Pero la otra fecha no se descarta: cuando las dos no coinciden, el movimiento lo
dice en la línea del historial. Sin eso, un registro cargado tarde deja un canje
con cara de al día, y uno antedatado hace lo contrario, y en los dos casos sin
que se note. **No es una señal de estado**, es un dato al lado del movimiento: si
se registró tarde no cambia que la gestión ocurrió cuando ocurrió.

**Los registros de una carga masiva no llevan ese aviso**, y eso se descubrió
mirando la pantalla con datos reales: los 605 movimientos migrados del Excel
decían todos "registrado 10 días después", porque una carga masiva es, por
definición, un registro posterior a la gestión. Repetido en las 35 líneas del
historial deja de ser una señal y se vuelve empapelado.

Distinguirlos no necesita ningún dato nuevo ni ninguna constante: **una carga
comparte el `creado_en` al microsegundo**, porque es una sola transacción. Dos
movimientos con el mismo instante de creación entraron juntos, y punto. La primera
hipótesis --"los migrados no tienen autor"-- era **falsa**: 384 de ellos sí tienen
autor, porque la carga corrió como el usuario admin. Se verificó antes de usarla.

Y el aviso que reemplaza a los 35 dice algo más útil que el original: cuántos de
esos registros vinieron del Excel y cuántos son trabajo hecho en la app.
"""
from datetime import date, datetime, timezone

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado, CanjeEtapa
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.usuario import Usuario
from app.services.bandeja_canjes import UMBRAL_CRITICO

AL_DIA = "al_dia"
PENDIENTE = "pendiente"

# Cuánto puede separarse `fecha` de `creado_en` antes de que valga la pena
# decirlo. Un día de margen: registrar a la mañana lo de ayer a la tarde es
# trabajo normal, no un registro atrasado.
HOLGURA_REGISTRO_DIAS = 1


class MovimientoDelListado(BaseModel):
    """Un movimiento, tal como lo muestra el historial desplegado."""

    id: int
    fecha: datetime
    tipo_nombre: str
    etapa_resultante: str | None
    corredor: str | None
    autor_nombre: str | None
    comentario: str | None
    # Cuántos días pasaron entre la gestión y su registro, cuando pasó más de la
    # holgura. Nulo cuando se registró el mismo día o el siguiente --lo habitual,
    # no hace falta decirlo-- y también cuando vino de una carga masiva, donde el
    # atraso es la definición de la carga y no una señal de nada.
    dias_hasta_el_registro: int | None
    # Si entró en una carga masiva. Se sabe porque comparte el instante exacto de
    # creación con otros: una carga es una sola transacción.
    de_carga_masiva: bool


class FilaCanjeActivo(BaseModel):
    canje_id: int
    fecha_solicitud: datetime
    etapa: CanjeEtapa
    corredor_solicitante_nombre: str | None
    corredor_propietario_nombre: str | None
    comuna: str | None
    direccion: str | None

    # `al_dia` o `pendiente`. Dos estados y no seis: este listado responde "cómo
    # viene", y para eso el detalle del semáforo es ruido.
    estado: str
    # Nulo cuando el canje nunca se gestionó. **No es cero**: son cosas
    # distintas y un cero diría que se gestionó hoy.
    horas_sin_gestion: float | None
    ultima_gestion: datetime | None
    # El compromiso vigente, si alguien agendó algo, y cuántos días lleva
    # vencido. Positivo si venció, cero si es para hoy, negativo si es a futuro.
    proximo_seguimiento: date | None
    dias_de_atraso: int | None
    # Cuántos de sus registros vinieron de una carga masiva, y de cuándo es esa
    # carga. Se dice una vez arriba del historial en vez de repetirlo por línea.
    registros_de_carga: int
    fecha_de_carga: date | None
    # El historial completo, en orden cronológico: del más viejo al más nuevo.
    movimientos: list[MovimientoDelListado]


class ListadoCanjesActivos(BaseModel):
    filas: list[FilaCanjeActivo]
    al_dia: int
    pendientes: int
    umbral_horas: int


def clasificar(horas: float | None, dias_de_atraso: int | None) -> str:
    """Al día o pendiente.

    **Cuando hay un compromiso, manda el compromiso.** Es la misma regla que la
    bandeja (`D-059`) y por el mismo motivo: el tiempo sin gestión es una
    inferencia --"pasaron dos días, seguro está abandonado"-- y el compromiso es
    un hecho, alguien dijo cuándo iba a volver. Entre los dos gana el que no
    infiere.

    Un canje agendado a futuro está **al día** aunque lleve un mes sin gestión:
    eso es exactamente lo que significa haberlo agendado.
    """
    if dias_de_atraso is not None:
        return PENDIENTE if dias_de_atraso > 0 else AL_DIA
    # Nunca gestionado: pendiente. Es trabajo sin empezar, y en un reporte de dos
    # estados no hay dónde ponerlo que no sea acá.
    if horas is None:
        return PENDIENTE
    return PENDIENTE if horas >= UMBRAL_CRITICO else AL_DIA


def _dias_hasta_el_registro(fecha: datetime, creado_en: datetime) -> int | None:
    """Los días entre la gestión y su registro, si pasaron más que la holgura.

    Los 605 movimientos migrados del Excel dan años de diferencia --la gestión es
    de 2022 y la carga del 22 de agosto--, así que este dato existe casi siempre
    en el histórico. Es correcto: la carga masiva es, literalmente, un registro
    muy posterior a la gestión.
    """
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    if creado_en.tzinfo is None:
        creado_en = creado_en.replace(tzinfo=timezone.utc)
    dias = (creado_en.date() - fecha.date()).days
    return dias if dias > HOLGURA_REGISTRO_DIAS else None


def obtener_listado(db: Session, ahora: datetime | None = None) -> ListadoCanjesActivos:
    """Los canjes abiertos, con su estado y su historial completo.

    Abierto es `estado = ACTIVO` **y** etapa distinta de Cierre, igual que en la
    bandeja: los que están activos con la etapa cerrada arrastran el
    desalineamiento del dato de Dataprop y no son trabajo abierto.

    El historial viene **en la misma respuesta** y no en una llamada por fila. Son
    pocos canjes abiertos por definición --hoy 4, con 35 movimientos entre todos--
    y traerlos juntos evita que desplegar una fila tenga que esperar.
    """
    ahora = ahora or datetime.now(timezone.utc)
    hoy = ahora.date()

    canjes = db.scalars(
        select(Canje)
        .where(Canje.estado == CanjeEstado.ACTIVO, Canje.etapa != CanjeEtapa.CERRADO)
        .order_by(Canje.id)
    ).all()
    if not canjes:
        return ListadoCanjesActivos(filas=[], al_dia=0, pendientes=0, umbral_horas=UMBRAL_CRITICO)

    ids = [c.id for c in canjes]
    nombres_tipo = dict(db.execute(select(TipoMovimiento.codigo, TipoMovimiento.nombre)).all())
    autores = dict(db.execute(select(Usuario.id, Usuario.nombre)).all())

    # Todos los movimientos de todos los canjes abiertos, en una sola vuelta y en
    # orden cronológico: así el historial de cada fila ya sale armado.
    crudos = db.scalars(
        select(Movimiento)
        .where(Movimiento.entity_type == EntityType.canje, Movimiento.entity_id.in_(ids))
        .order_by(Movimiento.fecha, Movimiento.id)
    ).all()

    # Cuántos movimientos comparten cada instante de creación. Dos o más con el
    # mismo `creado_en` al microsegundo entraron en la misma transacción, o sea en
    # una carga masiva. No hace falta ninguna constante ni ninguna marca: la
    # coincidencia exacta de un timestamp de microsegundos no pasa por casualidad.
    juntos: dict[datetime, int] = {}
    for m in crudos:
        juntos[m.creado_en] = juntos.get(m.creado_en, 0) + 1

    por_canje: dict[int, list[MovimientoDelListado]] = {i: [] for i in ids}
    cargas: dict[int, list[datetime]] = {i: [] for i in ids}
    for m in crudos:
        de_carga = juntos[m.creado_en] > 1
        if de_carga:
            cargas[m.entity_id].append(m.creado_en)
        por_canje[m.entity_id].append(
            MovimientoDelListado(
                id=m.id,
                fecha=m.fecha,
                tipo_nombre=nombres_tipo.get(m.tipo_movimiento, m.tipo_movimiento),
                etapa_resultante=m.etapa_resultante,
                corredor=m.corredor,
                autor_nombre=autores.get(m.autor_id) if m.autor_id else None,
                comentario=m.comentario,
                dias_hasta_el_registro=(
                    None if de_carga else _dias_hasta_el_registro(m.fecha, m.creado_en)
                ),
                de_carga_masiva=de_carga,
            )
        )

    filas: list[FilaCanjeActivo] = []
    for canje in canjes:
        movimientos = por_canje[canje.id]

        # La última gestión es la del movimiento con `fecha` más nueva, que al
        # venir ordenado es el último de la lista.
        ultima = movimientos[-1].fecha if movimientos else None
        if ultima is None:
            horas = None
        else:
            referencia = ultima if ultima.tzinfo else ultima.replace(tzinfo=timezone.utc)
            horas = round((ahora - referencia).total_seconds() / 3600, 1)

        # El compromiso vigente es el último que **exista**, no el del último
        # movimiento: un movimiento sin seguimiento no borra lo que se prometió
        # antes (`D-061`).
        seguimiento = None
        for m in db.scalars(
            select(Movimiento)
            .where(
                Movimiento.entity_type == EntityType.canje,
                Movimiento.entity_id == canje.id,
                Movimiento.proximo_seguimiento.is_not(None),
            )
            .order_by(Movimiento.fecha, Movimiento.id)
        ).all():
            seguimiento = m.proximo_seguimiento

        atraso = (hoy - seguimiento).days if seguimiento is not None else None

        filas.append(
            FilaCanjeActivo(
                canje_id=canje.id,
                fecha_solicitud=canje.fecha_solicitud,
                etapa=canje.etapa,
                corredor_solicitante_nombre=canje.corredor_solicitante_nombre,
                corredor_propietario_nombre=canje.corredor_propietario_nombre,
                comuna=canje.comuna,
                direccion=canje.direccion,
                registros_de_carga=len(cargas[canje.id]),
                # La más reciente, si hubo más de una carga.
                fecha_de_carga=max(cargas[canje.id]).date() if cargas[canje.id] else None,
                estado=clasificar(horas, atraso),
                horas_sin_gestion=horas,
                ultima_gestion=ultima,
                proximo_seguimiento=seguimiento,
                dias_de_atraso=atraso,
                movimientos=movimientos,
            )
        )

    # Primero los pendientes, y dentro de cada grupo el que lleva más tiempo sin
    # gestión: es el orden en que uno querría atacarlos.
    filas.sort(key=lambda f: (f.estado != PENDIENTE, -(f.horas_sin_gestion or 10**9)))

    return ListadoCanjesActivos(
        filas=filas,
        al_dia=sum(1 for f in filas if f.estado == AL_DIA),
        pendientes=sum(1 for f in filas if f.estado == PENDIENTE),
        umbral_horas=UMBRAL_CRITICO,
    )
