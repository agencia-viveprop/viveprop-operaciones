"""Facturación y pago: qué se espera cobrar o pagar, y en qué va cada parte.

**El monto esperado se calcula; el registrado se escribe.** Cada parte tiene un
monto que sale del motor de comisiones --el usuario fue explícito: «no me cuadra
que se registre solo a mano, con las reglas de cálculos de comisiones y
distribución de comisiones según Modelo/alianza tienes cómo calcular este ítem»--
y el que efectivamente se facturó o se pagó, que puede diferir «ya que podrían
existir ajustes o cambios por acuerdos». Los dos se guardan y los dos se muestran:
la diferencia entre ambos es justamente el ajuste, y esconderla sería perderla.

**El mapeo de negocios, parte por parte.** Los seis conceptos son *dos niveles de
la misma plata* --la comisión total se reparte, y lo que le queda a ViveProp se
reparte otra vez--, así que se totalizan **por tipo** y nunca en una suma general:
sumar los seis contaría la misma plata dos veces.

| Parte | Monto esperado |
|---|---|
| Facturación comisión total | `comision_total` |
| Pago partner comercial | `comision_broker` |
| Facturación corredor ViveProp | `comision_vp_bruta - comision_tercero` |
| Facturación captador alianza | `comision_tercero` |
| Pago equipo ViveProp | `comision_equipo` |
| Pago comisión real VP | `comision_real_vp` |

Las dos filas que no son obvias, y cómo se resolvieron con los datos del Excel:

- **Corredor ViveProp** es el lado de ViveProp de la comisión, no el del partner:
  VVP-15 tiene `comision_broker` en cero y esta fila con estado real, así que no
  puede ser la del broker. Y es la bruta **menos el tercero**, no la bruta: lo que
  ViveProp factura por sí mismo no incluye lo que le corresponde al captador de la
  alianza, que se factura aparte en la fila siguiente. En 17 de las 19
  liquidaciones da idéntico --no hay tercero--; solo se separa en VVP-3.
- **Captador alianza** es `comision_tercero`: está en «Pagado» exactamente en los
  dos negocios que tienen tercero mayor que cero, y en «No Aplica Captador» en los
  otros.

**En canjes la plata es de Dataprop.** ViveProp opera el Centro de Canje a nombre
de Dataprop y no percibe nada, así que estos montos no se suman nunca con los de
negocios. Son dos facturas, una por corredor, y por regla general iguales --la
mitad de la comisión de Dataprop cada una--, con la opción de corregirlas a mano
que el usuario pidió: «por regla general deben ser iguales, pero sería bueno tener
la opción de modificar manualmente».

**Una obligación se crea al primer registro.** No se pre-crean filas vacías: con
606 canjes serían 1.212 filas que no dicen nada. La pantalla muestra siempre las
partes del dominio y las que no existen dicen «sin registrar», que es información
distinta de un monto en cero.

**No se exige orden entre estados.** El circuito es Por Facturar → Facturado → Por
Pagar → Pagado, pero un salto se registra igual: en la operación real pasa, y el
sistema que lo prohíbe termina con la plata anotada en un campo de texto. La
historia queda en `obligacion_avances` y ahí se ve el salto.
"""
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.canje import Canje, CanjeEstado
from app.models.catalogo import Catalogo, TipoCatalogo
from app.models.negocio import Negocio, NegocioHito
from app.models.obligacion import (
    OBLIGACION_LABELS,
    TIPOS_DE_CANJE,
    TIPOS_DE_NEGOCIO,
    Obligacion,
    ObligacionAvance,
    TipoObligacion,
)
from app.models.usuario import Usuario
from app.services.comisiones_canjes import CORREDORES, calcular
from app.services.plata_canjes import uf_del_canje

CERO = Decimal("0")

# El circuito que pidió el usuario. No se impone como transición obligatoria --ver
# el docstring del módulo--; sirve para ordenar la pantalla y para saber cuál es el
# estado que sigue.
CIRCUITO = ("POR_FACTURAR", "FACTURADO", "POR_PAGAR", "PAGADO")


class ObligacionError(Exception):
    """Dato inválido al registrar un avance. El router lo traduce a 4xx."""


class AvanceOut(BaseModel):
    id: int
    estado_codigo: str | None
    estado_nombre: str | None
    monto: Decimal | None
    fecha: date | None
    autor: str | None
    creado_en: datetime


class ObligacionOut(BaseModel):
    """Una parte del dominio, esté registrada o no.

    `registrada` en falso significa que nadie la tocó todavía: `estado` y `monto`
    van nulos y la pantalla dice «sin registrar». `monto_esperado` está igual, que
    es lo que permite ofrecerlo prellenado en el formulario.
    """

    tipo: str
    rotulo: str
    registrada: bool
    estado_id: int | None = None
    estado_codigo: str | None = None
    estado_nombre: str | None = None
    monto: Decimal | None = None
    monto_esperado: Decimal | None = None
    fecha: date | None = None
    avances: list[AvanceOut] = []


def _menos(a: Decimal | None, b: Decimal | None) -> Decimal | None:
    """`a - b` tratando el nulo de `b` como cero, y el de `a` como desconocido."""
    if a is None:
        return None
    return Decimal(a) - (Decimal(b) if b is not None else CERO)


def montos_esperados_de_hito(hito: NegocioHito) -> dict[TipoObligacion, Decimal | None]:
    """Los seis montos que salen del motor. Nulo donde el hito no tiene el dato.

    Nulo y no cero: un hito sin liquidar no tiene comisión calculada, y mostrar
    cero diría «no corresponde plata» cuando lo que pasa es que todavía no se sabe.
    """
    return {
        TipoObligacion.FACT_COMISION_TOTAL: hito.comision_total,
        TipoObligacion.PAGO_PARTNER_COMERCIAL: hito.comision_broker,
        TipoObligacion.FACT_CORREDOR_VP: _menos(hito.comision_vp_bruta, hito.comision_tercero),
        TipoObligacion.FACT_CAPTADOR_ALIANZA: hito.comision_tercero,
        TipoObligacion.PAGO_EQUIPO_VP: hito.comision_equipo,
        TipoObligacion.PAGO_COMISION_REAL_VP: hito.comision_real_vp,
    }


def montos_esperados_de_canje(
    db: Session, canje: Canje, hoy: date | None = None
) -> dict[TipoObligacion, Decimal | None]:
    """La mitad de la comisión de Dataprop para cada corredor.

    Manda la comisión **registrada** cuando existe, que es la que se negoció y se
    va a facturar; el motor solo cubre el canje que todavía no la tiene. Es la
    misma jerarquía que usa la vista de plata de canjes: de un canje cerrado
    importa lo que se cobró, no lo que la regla estimaba.
    """
    total = _comision_del_canje(db, canje, hoy)
    mitad = (total / CORREDORES) if total is not None else None
    return {tipo: mitad for tipo in TIPOS_DE_CANJE}


def _comision_del_canje(db: Session, canje: Canje, hoy: date | None) -> Decimal | None:
    """La comisión de Dataprop de este canje, o nulo si no hay una que esperar.

    Manda la registrada. Si no hay, se calcula --pero **solo si el canje sigue
    vivo o cerró**: de un canje cancelado no hay nada que facturar, y el número
    del motor ahí no es un esperado sino una cifra sin destinatario. Además
    varios cancelados traen el valor mal etiquetado en el Excel de origen
    --3.500.000 marcado en UF en un arriendo-- y valorizarlo daba miles de
    millones.

    La UF sale de `uf_del_canje`, que es la política única: la del cierre para un
    cerrado, la de hoy para uno abierto.
    """
    if canje.comision_dataprop:
        return Decimal(canje.comision_dataprop)
    if canje.estado == CanjeEstado.CANCELADO:
        return None
    uf = uf_del_canje(db, canje, hoy or date.today())
    if uf is None:
        return None
    calculo = calcular(canje.tipo_operacion, canje.valor_prop, canje.moneda_valor, uf)
    return calculo.comision_dataprop if calculo else None


def _catalogos(db: Session, ids: set[int]) -> dict[int, Catalogo]:
    if not ids:
        return {}
    return {c.id: c for c in db.scalars(select(Catalogo).where(Catalogo.id.in_(ids)))}


def _vista(
    tipos: tuple[TipoObligacion, ...],
    filas: list[Obligacion],
    esperados: dict[TipoObligacion, Decimal | None],
    catalogos: dict[int, Catalogo],
    autores: dict[int, str],
) -> list[ObligacionOut]:
    por_tipo = {f.tipo: f for f in filas}
    salida = []
    for tipo in tipos:
        fila = por_tipo.get(tipo)
        base = ObligacionOut(
            tipo=tipo.value,
            rotulo=OBLIGACION_LABELS[tipo],
            registrada=fila is not None,
            monto_esperado=esperados.get(tipo),
        )
        if fila is not None:
            estado = catalogos.get(fila.estado_id) if fila.estado_id else None
            base.estado_id = fila.estado_id
            base.estado_codigo = estado.codigo if estado else None
            base.estado_nombre = estado.nombre if estado else None
            base.monto = fila.monto
            base.fecha = fila.fecha
            # Del más reciente al más antiguo, como el resto de los historiales de
            # la app (`D-081`).
            base.avances = [
                AvanceOut(
                    id=a.id,
                    estado_codigo=(catalogos.get(a.estado_id).codigo if a.estado_id in catalogos else None),
                    estado_nombre=(catalogos.get(a.estado_id).nombre if a.estado_id in catalogos else None),
                    monto=a.monto,
                    fecha=a.fecha,
                    autor=autores.get(a.autor_id) if a.autor_id else None,
                    creado_en=a.creado_en,
                )
                for a in sorted(fila.avances, key=lambda a: a.id, reverse=True)
            ]
        salida.append(base)
    return salida


def _completar(db: Session, tipos, filas, esperados) -> list[ObligacionOut]:
    ids_catalogo = {f.estado_id for f in filas if f.estado_id}
    ids_autor = set()
    for f in filas:
        for a in f.avances:
            if a.estado_id:
                ids_catalogo.add(a.estado_id)
            if a.autor_id:
                ids_autor.add(a.autor_id)
    autores = {}
    if ids_autor:
        autores = {
            u.id: u.nombre or u.email
            for u in db.scalars(select(Usuario).where(Usuario.id.in_(ids_autor)))
        }
    return _vista(tipos, filas, esperados, _catalogos(db, ids_catalogo), autores)


def obligaciones_del_hito(db: Session, hito: NegocioHito) -> list[ObligacionOut]:
    filas = list(
        db.scalars(
            select(Obligacion)
            .where(Obligacion.hito_id == hito.id)
            .options(selectinload(Obligacion.avances))
        )
    )
    return _completar(db, TIPOS_DE_NEGOCIO, filas, montos_esperados_de_hito(hito))


def obligaciones_del_canje(
    db: Session, canje: Canje, hoy: date | None = None
) -> list[ObligacionOut]:
    filas = list(
        db.scalars(
            select(Obligacion)
            .where(Obligacion.canje_id == canje.id)
            .options(selectinload(Obligacion.avances))
        )
    )
    return _completar(db, TIPOS_DE_CANJE, filas, montos_esperados_de_canje(db, canje, hoy))


def registrar_avance(
    db: Session,
    *,
    tipo: str,
    estado_id: int,
    monto: Decimal | None,
    fecha: date | None,
    autor_id: int | None,
    hito: NegocioHito | None = None,
    canje: Canje | None = None,
) -> Obligacion:
    """Deja el estado vigente y agrega el avance. Crea la obligación si no existe.

    La fila queda espejando el último avance: estado, monto y fecha son «lo que
    está registrado hoy», y los valores anteriores viven en la historia. Por eso el
    formulario manda los tres siempre, prellenados con lo vigente.
    """
    if (hito is None) == (canje is None):
        raise ObligacionError("Una obligación cuelga de una liquidación o de un canje.")

    esperado_de = TIPOS_DE_NEGOCIO if hito is not None else TIPOS_DE_CANJE
    try:
        parte = TipoObligacion(tipo)
    except ValueError:
        raise ObligacionError(f"tipo: '{tipo}' no es una parte conocida.") from None
    if parte not in esperado_de:
        dominio = "un negocio" if hito is not None else "un canje"
        raise ObligacionError(
            f"tipo: '{OBLIGACION_LABELS[parte]}' no corresponde a {dominio}."
        )

    estado = db.get(Catalogo, estado_id)
    if estado is None or estado.tipo != TipoCatalogo.ESTADO_FACTURACION.value:
        raise ObligacionError(f"estado_id: no es un estado de facturación ({estado_id}).")
    if not estado.activo:
        raise ObligacionError(f"estado_id: '{estado.nombre}' está dado de baja.")

    condicion = (
        Obligacion.hito_id == hito.id if hito is not None else Obligacion.canje_id == canje.id
    )
    obligacion = db.scalar(select(Obligacion).where(condicion, Obligacion.tipo == parte))
    if obligacion is None:
        obligacion = Obligacion(
            hito_id=hito.id if hito is not None else None,
            canje_id=canje.id if canje is not None else None,
            tipo=parte,
        )
        db.add(obligacion)

    obligacion.estado_id = estado.id
    obligacion.monto = monto
    obligacion.fecha = fecha
    db.flush()
    db.add(
        ObligacionAvance(
            obligacion_id=obligacion.id,
            estado_id=estado.id,
            monto=monto,
            fecha=fecha,
            autor_id=autor_id,
        )
    )
    db.flush()
    return obligacion


# ------------------------------------------------------------------ cobranza


class TramoDeCobranza(BaseModel):
    """Lo que hay en un estado, dentro de una parte."""

    estado_codigo: str | None
    estado_nombre: str | None
    casos: int
    # Los dos por separado y nunca mezclados: uno es lo que se registró y el otro
    # lo que el motor calculó. Sumarlos en una sola cifra inventaría plata.
    monto_registrado: Decimal
    monto_esperado: Decimal
    # De cuántos de esos casos se registró monto. Con esto se lee si el registrado
    # está incompleto en vez de parecer bajo.
    con_monto: int


class ParteDeCobranza(BaseModel):
    tipo: str
    rotulo: str
    casos: int
    monto_registrado: Decimal
    monto_esperado: Decimal
    tramos: list[TramoDeCobranza]


class Cobranza(BaseModel):
    """Las dos mitades, separadas a propósito.

    La plata de negocios es de ViveProp y la de canjes es de Dataprop, así que van
    en dos listas y no hay ningún total que las cruce (`D-045`).
    """

    negocios: list[ParteDeCobranza]
    canjes: list[ParteDeCobranza]
    # Entidades sin ninguna parte registrada, para que la vista no parezca completa
    # cuando lo que pasa es que casi nada se registró todavía.
    liquidaciones_sin_registrar: int
    canjes_sin_registrar: int


def _orden_de_estado(codigo: str | None) -> tuple[int, str]:
    if codigo in CIRCUITO:
        return (CIRCUITO.index(codigo), "")
    # Los «No Aplica» y los estados viejos del Excel van después del circuito, en
    # orden alfabético estable.
    return (len(CIRCUITO), codigo or "")


def _partes(
    tipos: tuple[TipoObligacion, ...],
    filas: list[tuple[Obligacion, Decimal | None]],
    catalogos: dict[int, Catalogo],
) -> list[ParteDeCobranza]:
    salida = []
    for tipo in tipos:
        del_tipo = [(o, e) for o, e in filas if o.tipo == tipo]
        por_estado: dict[str | None, list[tuple[Obligacion, Decimal | None]]] = {}
        for o, esperado in del_tipo:
            estado = catalogos.get(o.estado_id) if o.estado_id else None
            por_estado.setdefault(estado.codigo if estado else None, []).append((o, esperado))

        tramos = []
        for codigo in sorted(por_estado, key=_orden_de_estado):
            items = por_estado[codigo]
            nombre = next(
                (c.nombre for c in catalogos.values() if c.codigo == codigo), None
            )
            tramos.append(
                TramoDeCobranza(
                    estado_codigo=codigo,
                    estado_nombre=nombre,
                    casos=len(items),
                    monto_registrado=sum((Decimal(o.monto) for o, _ in items if o.monto), CERO),
                    monto_esperado=sum((Decimal(e) for _, e in items if e is not None), CERO),
                    con_monto=sum(1 for o, _ in items if o.monto is not None),
                )
            )
        salida.append(
            ParteDeCobranza(
                tipo=tipo.value,
                rotulo=OBLIGACION_LABELS[tipo],
                casos=len(del_tipo),
                monto_registrado=sum((t.monto_registrado for t in tramos), CERO),
                monto_esperado=sum((t.monto_esperado for t in tramos), CERO),
                tramos=tramos,
            )
        )
    return salida


def obtener_cobranza(db: Session, hoy: date | None = None) -> Cobranza:
    """Todo lo facturable y pagable de los dos mundos, agrupado por parte.

    **No hay un gran total.** Los seis conceptos de negocios son dos niveles de la
    misma plata, así que se totalizan por parte; y la de canjes es de Dataprop, que
    no se suma con la de ViveProp por definición.
    """
    filas = list(db.scalars(select(Obligacion).options(selectinload(Obligacion.avances))))

    hitos = {
        h.id: h
        for h in db.scalars(
            select(NegocioHito).where(NegocioHito.id.in_({f.hito_id for f in filas if f.hito_id}))
        )
    }
    canjes = {
        c.id: c
        for c in db.scalars(
            select(Canje).where(Canje.id.in_({f.canje_id for f in filas if f.canje_id}))
        )
    }
    esperados_hito = {h.id: montos_esperados_de_hito(h) for h in hitos.values()}
    esperados_canje = {c.id: montos_esperados_de_canje(db, c, hoy) for c in canjes.values()}

    de_negocios, de_canjes = [], []
    for f in filas:
        if f.hito_id:
            de_negocios.append((f, esperados_hito[f.hito_id].get(f.tipo)))
        else:
            de_canjes.append((f, esperados_canje[f.canje_id].get(f.tipo)))

    catalogos = _catalogos(db, {f.estado_id for f in filas if f.estado_id})

    total_liquidaciones = db.scalar(
        select(func.count()).select_from(NegocioHito).join(Negocio)
    ) or 0
    total_canjes = db.scalar(select(func.count()).select_from(Canje)) or 0

    return Cobranza(
        negocios=_partes(TIPOS_DE_NEGOCIO, de_negocios, catalogos),
        canjes=_partes(TIPOS_DE_CANJE, de_canjes, catalogos),
        liquidaciones_sin_registrar=total_liquidaciones - len({f.hito_id for f in filas if f.hito_id}),
        canjes_sin_registrar=total_canjes - len({f.canje_id for f in filas if f.canje_id}),
    )
