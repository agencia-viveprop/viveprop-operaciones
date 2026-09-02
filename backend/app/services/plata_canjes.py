"""La plata y los plazos del Centro de Canje.

**Es plata de Dataprop, no de ViveProp**, y por eso todo lo que sale de acá va
rotulado como tal y nunca se suma con la de negocios. ViveProp opera el programa a
nombre de Dataprop y no percibe nada de él.

**Tres cifras, y las tres significan cosas distintas.**

| Cuál | De dónde sale | Qué es |
|---|---|---|
| Cobrada | el campo manual de los cerrados | un hecho |
| Potencial | la regla, sobre los activos | una estimación |
| No concretada | la regla, sobre los cancelados | lo que no se llegó a cobrar |

La cobrada **no se calcula: se registra.** Cuando un canje cierra, la comisión se
negocia y se factura, así que es un dato que alguien escribe. Las otras dos salen
del motor, porque son proyecciones sobre canjes que todavía no generaron nada.

**Cada caso usa la UF que le corresponde**, y no la de hoy para todos:

- **Activos** → la de hoy. Es un potencial: vale lo que valdría si cerrara ahora.
- **Cerrados** → la del cierre. Ahí es cuando la comisión se gana.
- **Cancelados** → la de la fecha de solicitud. Ese valor de propiedad se registró
  en ese momento, y ponerle la UF de hoy a un canje que se cayó en 2023 sería
  valorizarlo con una unidad que nunca tuvo.

La UF sale de `valor_uf`, el mismo helper que usa el motor de negocios, que **falla
si no hay UF para esa fecha** en vez de agarrar el último valor de la serie. Eso no
es paranoia: una consulta armada al momento tomó la UF del 09-09-2026 --futura,
porque la serie se publica adelantada-- y el error solo se vio porque el usuario
preguntó qué fecha se había usado.

**Los plazos miden dos cosas y ninguna es "cuánto tarda en cerrar".**

Hoy no hay ningún canje cerrado, así que ese número no existe. Lo que sí se puede
medir es cuánto sobrevive un canje antes de caerse, y cuánto llevan abiertos los
que siguen vivos. Se informan separados y nombrados por lo que son: llamar
"duración" a la mediana de las cancelaciones sería publicar el tiempo que tardan en
morir como si fuera el que tardan en cerrar.
"""
from datetime import date, datetime, timezone
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.canje import Canje, CanjeEstado
from app.services.comisiones_canjes import ComisionCanje, calcular
from app.services.uf import UFNoDisponible, valor_uf

CERO = Decimal("0")


class BolsaDeCanjes(BaseModel):
    """Un grupo de canjes con su plata. Los conteos dicen sobre qué se calculó."""

    canjes: int
    # De cuántos se pudo calcular la comisión. Menor que `canjes` cuando falta el
    # valor, la moneda o la operación: sin eso no hay comisión, y contarlos como
    # cero bajaría los promedios con datos que no existen.
    con_monto: int
    valor_propiedades: Decimal
    comision_corredores: Decimal
    comision_dataprop: Decimal


class PlazosCanjes(BaseModel):
    """Cuántos días, sobre las poblaciones que sí se pueden medir.

    `None` cuando no hay casos. No cero: son cosas distintas.
    """

    # Los que se cayeron y tienen fecha de término: cuánto sobrevivieron.
    sobrevivencia_n: int
    sobrevivencia_mediana: int | None
    sobrevivencia_min: int | None
    sobrevivencia_max: int | None
    # Los que siguen abiertos: cuánto llevan.
    edad_n: int
    edad_mediana: int | None
    edad_min: int | None
    edad_max: int | None
    # Los cancelados sin fecha de término. Su duración es desconocida y por eso no
    # entran en ninguna de las dos medianas; se dice cuántos son para que no
    # parezca que la muestra es más grande de lo que es.
    sin_fecha_de_termino: int


class PlataCanjes(BaseModel):
    cobrada: BolsaDeCanjes
    potencial: BolsaDeCanjes
    no_concretada: BolsaDeCanjes
    plazos: PlazosCanjes
    # La UF con la que se valorizó lo potencial, para que el número sea auditable.
    uf_de_hoy: Decimal
    fecha_uf: date


def _mediana(valores: list[int]) -> int | None:
    """La mediana y no el promedio: con esta dispersión un caso raro la corre.

    Sobre los cancelados va de 1 a 44 días, así que el promedio se deja mover por
    la cola larga y la mediana no.
    """
    if not valores:
        return None
    ordenados = sorted(valores)
    n = len(ordenados)
    if n % 2:
        return ordenados[n // 2]
    return (ordenados[n // 2 - 1] + ordenados[n // 2]) // 2


def _dias(desde: datetime | date, hasta: date) -> int:
    if isinstance(desde, datetime):
        desde = desde.astimezone(timezone.utc).date() if desde.tzinfo else desde.date()
    return (hasta - desde).days


def uf_del_canje(
    db: Session, canje: Canje, hoy: date, cache: dict[date, Decimal] | None = None
) -> Decimal | None:
    """Con qué UF se valoriza este canje. Ver el docstring del módulo.

    **`cache`, cuando se pasa, es la serie completa** --lo que devuelve
    `uf.serie_completa`-- y se resuelve solo contra él, sin consultar. Una fecha
    ausente significa "no hay UF para ese día", que es lo mismo que responde
    `valor_uf` fallando. La política de **qué** fecha usar no cambia; lo que se
    evita es preguntar de a una (`D-098`).

    Es público porque la política es una sola y la usa también la facturación de
    canjes: cada caso con la UF que le corresponde, y no la de hoy para todos.
    Duplicarla ahí ya salió mal una vez --un canje cancelado en 2022 valorizado
    con la UF de hoy daba una comisión de miles de millones-- porque su valor
    viene mal etiquetado en el Excel de origen.
    """
    if canje.estado == CanjeEstado.ACTIVO:
        cuando = hoy
    elif canje.estado == CanjeEstado.CERRADO:
        cuando = _fecha(canje.fecha_cierre) or hoy
    else:
        cuando = _fecha(canje.fecha_solicitud) or hoy
    if cache is not None:
        return cache.get(cuando)
    try:
        return valor_uf(db, cuando)
    except UFNoDisponible:
        # Un canje de 2022 puede quedar fuera de la serie cargada. Se informa como
        # "sin monto" en vez de valorizarse con una UF inventada.
        return None


def _fecha(valor) -> date | None:
    if valor is None:
        return None
    return valor.date() if isinstance(valor, datetime) else valor


def _bolsa(items: list[tuple[Canje, ComisionCanje | None]]) -> BolsaDeCanjes:
    con_monto = [c for _, c in items if c is not None]
    return BolsaDeCanjes(
        canjes=len(items),
        con_monto=len(con_monto),
        valor_propiedades=sum((c.valor_clp for c in con_monto), CERO),
        comision_corredores=sum((c.comision_corredores for c in con_monto), CERO),
        comision_dataprop=sum((c.comision_dataprop for c in con_monto), CERO),
    )


def _bolsa_cobrada(cerrados: list[Canje]) -> BolsaDeCanjes:
    """La de los cerrados sale del campo manual, no de la regla.

    Un canje cerrado tiene una comisión que se negoció y se facturó: es un hecho
    que se registra, no una estimación que se deriva. Si el campo está vacío, ese
    canje cuenta en `canjes` pero no en `con_monto` -- cerró y todavía no se
    registró cuánto se cobró, que es una situación real y distinta de cobrar cero.
    """
    montos = [Decimal(c.comision_dataprop) for c in cerrados if c.comision_dataprop]
    return BolsaDeCanjes(
        canjes=len(cerrados),
        con_monto=len(montos),
        # El valor de las propiedades y la comisión de los corredores no se
        # informan acá: lo que importa de un canje cerrado es lo que se cobró.
        valor_propiedades=CERO,
        comision_corredores=CERO,
        comision_dataprop=sum(montos, CERO),
    )


def obtener_plata_canjes(db: Session, hoy: date | None = None) -> PlataCanjes:
    hoy = hoy or datetime.now(timezone.utc).date()
    canjes = list(db.scalars(select(Canje)).all())

    por_estado: dict[CanjeEstado, list[Canje]] = {e: [] for e in CanjeEstado}
    for c in canjes:
        por_estado[c.estado].append(c)

    def calculados(estado: CanjeEstado) -> list[tuple[Canje, ComisionCanje | None]]:
        salida = []
        for c in por_estado[estado]:
            uf = uf_del_canje(db, c, hoy)
            salida.append(
                (c, calcular(c.tipo_operacion, c.valor_prop, c.moneda_valor, uf) if uf else None)
            )
        return salida

    # Los plazos, sobre las dos poblaciones que se pueden medir.
    sobrevivencia, edades, sin_termino = [], [], 0
    for c in canjes:
        solicitud = _fecha(c.fecha_solicitud)
        if solicitud is None:
            continue
        if c.estado == CanjeEstado.ACTIVO:
            edades.append(_dias(solicitud, hoy))
            continue
        termino = _fecha(c.fecha_cierre)
        if termino is None:
            sin_termino += 1
            continue
        dias = (termino - solicitud).days
        # Una duración de cero día no se distingue de "las dos fechas son la misma
        # porque el origen traía una sola". Se cuenta como desconocida.
        if dias <= 0:
            sin_termino += 1
        else:
            sobrevivencia.append(dias)

    uf_hoy = valor_uf(db, hoy)

    return PlataCanjes(
        cobrada=_bolsa_cobrada(por_estado[CanjeEstado.CERRADO]),
        potencial=_bolsa(calculados(CanjeEstado.ACTIVO)),
        no_concretada=_bolsa(calculados(CanjeEstado.CANCELADO)),
        plazos=PlazosCanjes(
            sobrevivencia_n=len(sobrevivencia),
            sobrevivencia_mediana=_mediana(sobrevivencia),
            sobrevivencia_min=min(sobrevivencia) if sobrevivencia else None,
            sobrevivencia_max=max(sobrevivencia) if sobrevivencia else None,
            edad_n=len(edades),
            edad_mediana=_mediana(edades),
            edad_min=min(edades) if edades else None,
            edad_max=max(edades) if edades else None,
            sin_fecha_de_termino=sin_termino,
        ),
        uf_de_hoy=uf_hoy,
        fecha_uf=hoy,
    )
