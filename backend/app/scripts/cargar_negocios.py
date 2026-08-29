"""Carga los 19 negocios historicos desde la hoja NEGOCIOS del Excel.

Uso:
    python -m app.scripts.cargar_negocios <ruta_al_xlsx> [--reemplazar]

**Migra fiel, no recalcula.** Los montos que quedan en la base son los del
Excel, no los del motor. Recalcular cambiaria en silencio los numeros de siete
negocios cerrados con plata ya facturada, y eso no se hace en una migracion.

El motor si se ejecuta, pero solo para **comparar**: al final se imprime un
informe con cada diferencia. Para los 18 negocios consistentes deberia dar cero;
VVP-2 va a aparecer con su descuadre de 903.803 (D-026).

Lo mismo con la UF: se preserva la columna AB en vez de buscarla en la serie. La
de VVP-3 PROMESA (39.707,30) no existe en ninguna fecha, asi que recalcularla
cambiaria su valorizacion.
"""
import sys
from decimal import Decimal

import openpyxl
from openpyxl.utils import column_index_from_string as ci
from sqlalchemy import delete, select

from app.db import SessionLocal, engine
from app.models.canje import MonedaTipo
from app.models.catalogo import Catalogo, EstadoNegocio, ModeloNegocio
from app.models.obligacion import Obligacion, TipoObligacion
from app.models.negocio import (
    Negocio,
    NegocioHito,
    Obligacion,
    Propiedad,
)
from app.services import comisiones as motor
from app.services.negocios import obtener_o_crear_propiedad

FILA_PRIMERA, FILA_ULTIMA = 4, 23

MODELOS = {
    "Mercado Primario": ModeloNegocio.MERCADO_PRIMARIO,
    "Secundario Concentradores": ModeloNegocio.SECUNDARIO_CONCENTRADORES,
    "Secundario Agencia": ModeloNegocio.SECUNDARIO_AGENCIA,
}
ESTADOS = {
    "Activo": EstadoNegocio.ACTIVO,
    "Cerrado": EstadoNegocio.CERRADO,
    "Perdido": EstadoNegocio.PERDIDO,
    "Desistido": EstadoNegocio.DESISTIDO,
}
MONEDAS = {"UF": MonedaTipo.UF, "CLP": MonedaTipo.CLP}

# columna del Excel -> campo del hito
TASAS = {
    "AD": "pct_lado_vendedor",
    "AE": "pct_lado_comprador",
    "AG": "pct_rebate_concentrador",
    "AH": "pct_broker_vendedor",
    "AI": "pct_broker_comprador",
    "AJ": "pct_vp_vendedor",
    "AK": "pct_vp_comprador",
    "AL": "pct_equipo",
    "AM": "pct_tercero",
}
MONTOS = {
    "AF": "comision_total",
    "AO": "comision_broker",
    "AP": "rebate_concentrador",
    "AQ": "comision_vp_bruta",
    "AR": "comision_equipo",
    "AS": "comision_tercero",
    "AT": "comision_real_vp",
}
# columna del Excel -> tipo de obligacion
OBLIGACIONES = {
    "AX": TipoObligacion.PAGO_PARTNER_COMERCIAL,
    "AY": TipoObligacion.FACT_CORREDOR_VP,
    "AZ": TipoObligacion.FACT_CAPTADOR_ALIANZA,
    "BA": TipoObligacion.PAGO_EQUIPO_VP,
    "BC": TipoObligacion.FACT_COMISION_TOTAL,
    "BD": TipoObligacion.PAGO_COMISION_REAL_VP,
}

CENTAVO = Decimal("0.01")


def _texto(v):
    if v is None:
        return None
    t = str(v).replace("\n", " ").strip()
    return t or None


def _dec(v):
    return None if v is None or v == "" else Decimal(str(v))


def _fecha(v):
    return v.date() if hasattr(v, "date") else v


class Cargador:
    def __init__(self, db, hoja):
        self.db = db
        self.hoja = hoja
        self.catalogos = self._indexar_catalogos()
        self.diferencias: list[str] = []
        self.avisos: list[str] = []

    def _indexar_catalogos(self) -> dict:
        indice = {}
        for fila in self.db.scalars(select(Catalogo)).all():
            indice[(fila.tipo, fila.nombre.lower())] = fila.id
        return indice

    def _catalogo(self, tipo: str, nombre, contexto: str):
        nombre = _texto(nombre)
        if nombre is None:
            return None
        clave = (tipo, nombre.lower())
        if clave not in self.catalogos:
            self.avisos.append(f"{contexto}: no hay catálogo '{tipo}' llamado '{nombre}'")
            return None
        return self.catalogos[clave]

    def _g(self, fila: int, col: str):
        return self.hoja.cell(fila, ci(col)).value

    # ------------------------------------------------------------------ grupos

    def agrupar(self) -> dict[str, list[int]]:
        """Agrupa filas por ID_Base. VVP-3 tiene dos; el resto una.

        El padre `VVP-3` no existe como fila en el Excel: se crea acá.
        """
        grupos: dict[str, list[int]] = {}
        for fila in range(FILA_PRIMERA, FILA_ULTIMA + 1):
            if self._g(fila, "A") is None:
                continue
            base = _texto(self._g(fila, "B"))
            grupos.setdefault(base, []).append(fila)
        return grupos

    # ------------------------------------------------------------------- carga

    def cargar_negocio(self, codigo: str, filas: list[int]) -> Negocio:
        primera = filas[0]

        propiedad = obtener_o_crear_propiedad(
            self.db,
            {
                "direccion": _texto(self._g(primera, "G")),
                "unidad": _texto(self._g(primera, "H")),
                "comuna": _texto(self._g(primera, "I")),
                "tipo_propiedad_id": self._catalogo("tipo_propiedad", self._g(primera, "J"), codigo),
                "estado_propiedad_id": self._catalogo("estado_propiedad", self._g(primera, "L"), codigo),
            },
        )

        negocio = Negocio(
            codigo=codigo,
            modelo=MODELOS[_texto(self._g(primera, "E"))],
            propiedad=propiedad,
            alianza_id=self._catalogo("alianza", self._g(primera, "F"), codigo),
            tipo_operacion_id=self._catalogo("tipo_operacion", self._g(primera, "K"), codigo),
            vendedor_arrendador=_texto(self._g(primera, "M")),
            comprador_arrendatario=_texto(self._g(primera, "N")),
            corredor_agente=_texto(self._g(primera, "O")),
            observaciones=" | ".join(
                filter(None, (_texto(self._g(f, "AW")) for f in filas))
            ) or None,
        )
        self.db.add(negocio)

        for fila in filas:
            negocio.hitos.append(self.cargar_hito(negocio, codigo, fila))

        return negocio

    def cargar_hito(self, negocio: Negocio, codigo_base: str, fila: int) -> NegocioHito:
        id_negocio = _texto(self._g(fila, "A"))
        # 'VVP-3 PROMESA' con base 'VVP-3' -> nombre 'PROMESA'. Si coinciden, el
        # negocio tiene un solo hito y va sin nombre.
        nombre = id_negocio[len(codigo_base):].strip() or None if id_negocio != codigo_base else None

        hito = NegocioHito(
            nombre=nombre,
            fecha_inicio=_fecha(self._g(fila, "C")),
            fecha_cierre=_fecha(self._g(fila, "AU")),
            estado=ESTADOS[_texto(self._g(fila, "D"))],
            etapa=_texto(self._g(fila, "P")),
            valor_negocio=_dec(self._g(fila, "Y")),
            moneda=MONEDAS.get(_texto(self._g(fila, "Z"))),
            fecha_valorizacion=_fecha(self._g(fila, "AA")),
            # Se preserva la UF del Excel en vez de buscarla en la serie: la de
            # VVP-3 PROMESA no existe en ninguna fecha.
            uf_snapshot=_dec(self._g(fila, "AB")),
            valor_clp_calculado=_dec(self._g(fila, "AC")),
            nombre_tercero=_texto(self._g(fila, "AN")),
        )
        for col, campo in TASAS.items():
            setattr(hito, campo, _dec(self._g(fila, col)))
        for col, campo in MONTOS.items():
            valor = _dec(self._g(fila, col))
            setattr(hito, campo, valor.quantize(CENTAVO) if valor is not None else None)

        self.verificar(hito, negocio.modelo.value, id_negocio)
        self.cargar_obligaciones(hito, fila, id_negocio)
        return hito

    def cargar_obligaciones(self, hito: NegocioHito, fila: int, contexto: str) -> None:
        for col, tipo in OBLIGACIONES.items():
            estado_id = self._catalogo("estado_facturacion", self._g(fila, col), contexto)
            if estado_id is None:
                continue
            hito.obligaciones.append(Obligacion(tipo=tipo, estado_id=estado_id))

    # ------------------------------------------------------------ verificacion

    def verificar(self, hito: NegocioHito, modelo: str, contexto: str) -> None:
        """Corre el motor y anota las diferencias, sin sobreescribir nada."""
        base = hito.base_comision
        if base is None:
            return
        cero = Decimal("0")
        calculado = motor.calcular(
            modelo=modelo,
            estado=hito.estado.value,
            base=base,
            **{campo: getattr(hito, campo) or cero for campo in TASAS.values()},
        )
        for campo in MONTOS.values():
            del_excel = getattr(hito, campo)
            del_motor = getattr(calculado, campo).quantize(CENTAVO)
            if del_excel is None:
                continue
            # 1 peso de tolerancia: el Excel guarda comision_total redondeada.
            if abs(del_excel - del_motor) > Decimal("1"):
                self.diferencias.append(
                    f"  {contexto:<18}{campo:<22} excel={del_excel:>16,.2f}  "
                    f"motor={del_motor:>16,.2f}  dif={del_excel - del_motor:>14,.2f}"
                )


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    ruta = sys.argv[1]
    reemplazar = "--reemplazar" in sys.argv

    hoja = openpyxl.load_workbook(ruta, data_only=True)["NEGOCIOS"]

    with SessionLocal() as db:
        existentes = db.scalar(select(Negocio.codigo).limit(1))
        if existentes is not None:
            if not reemplazar:
                print(
                    f"Ya hay negocios cargados (por ejemplo '{existentes}').\n"
                    "Usar --reemplazar para borrarlos y volver a cargar."
                )
                raise SystemExit(1)
            db.execute(delete(Negocio))
            db.commit()
            print("Negocios anteriores borrados.")

        cargador = Cargador(db, hoja)
        grupos = cargador.agrupar()
        print(f"Cargando en {engine.url.host}")
        print(f"{len(grupos)} negocios agrupados desde {sum(len(f) for f in grupos.values())} filas\n")

        for codigo, filas in grupos.items():
            negocio = cargador.cargar_negocio(codigo, filas)
            hitos = ", ".join(h.nombre or "(único)" for h in negocio.hitos)
            print(f"  {codigo:<10} {negocio.modelo.value:<28} hitos: {hitos}")

        db.commit()

        print(f"\nCargados: {db.scalar(select(Negocio.id).limit(1)) is not None}")
        for etiqueta, consulta in (
            ("negocios", select(Negocio)),
            ("hitos", select(NegocioHito)),
            ("propiedades", select(Propiedad)),
            ("obligaciones", select(Obligacion)),
        ):
            print(f"  {etiqueta:<14}{len(db.scalars(consulta).all())}")

    print("\n" + "=" * 78)
    if cargador.avisos:
        print("AVISOS")
        for a in cargador.avisos:
            print("  " + a)
        print()
    if cargador.diferencias:
        print(f"DIFERENCIAS ENTRE EL EXCEL Y EL MOTOR ({len(cargador.diferencias)})")
        print("Se guardaron los valores del Excel. Cada linea es algo a revisar.\n")
        for d in cargador.diferencias:
            print(d)
    else:
        print("El motor reproduce el Excel al peso en los 19 negocios.")
    print("=" * 78)


if __name__ == "__main__":
    main()
