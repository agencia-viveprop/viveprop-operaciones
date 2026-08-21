"""Los 19 negocios del Excel, como casos de regresion del motor de comisiones.

GENERADO desde la hoja NEGOCIOS de GESTION_OPERACIONES_VIVEPROP.xlsx. No se
edita a mano: el archivo original esta en .gitignore, asi que estos son los
unicos datos historicos versionados y son la referencia del sprint 7.

`base` es la columna AC (valor en UF por la UF del momento). `base_manual` esta
poblada solo cuando la comision no se calculo sobre AC, que es el caso de
VVP-2 -- ver D-017.

Los montos esperados salen de las columnas AF, AO, AP, AQ, AR, AS y AT. Ojo: la
planilla guarda `comision_total` redondeada al peso y las demas con todos sus
decimales, asi que los tests comparan con tolerancias distintas.
"""
from dataclasses import dataclass, field
from decimal import Decimal as D


@dataclass(frozen=True)
class Caso:
    codigo: str
    modelo: str
    estado: str
    base: D
    base_manual: D | None
    tasas: dict
    esperado: dict

    @property
    def base_comision(self) -> D:
        return self.base_manual if self.base_manual is not None else self.base


HISTORICOS = [
    Caso(
        codigo='VVP-1',
        modelo='MERCADO_PRIMARIO',
        estado='CERRADO',
        base=D("132739562.16"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.04"), "pct_lado_comprador": D("0"), "pct_rebate_concentrador": D("0"), "pct_broker_vendedor": D("0.0252001208200461"), "pct_broker_comprador": D("0"), "pct_vp_vendedor": D("0.0147998791799539"), "pct_vp_comprador": D("0"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("5309582"), "comision_broker": D("3345053.0040320195"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("1964529.4823679803"), "comision_equipo": D("196452.94823679805"), "comision_tercero": D("0"), "comision_real_vp": D("1768076.5341311824")},
    ),
    Caso(
        codigo='VVP-2',
        modelo='MERCADO_PRIMARIO',
        estado='CERRADO',
        base=D("104100248.32"),
        base_manual=D(81505175),
        tasas={"pct_lado_vendedor": D("0.04"), "pct_lado_comprador": D("0"), "pct_rebate_concentrador": D("0"), "pct_broker_vendedor": D("0.0252001208200461"), "pct_broker_comprador": D("0"), "pct_vp_vendedor": D("0.0147998791799539"), "pct_vp_comprador": D("0"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("3260207"), "comision_broker": D("2623338.8351364015"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("1540671.0977835986"), "comision_equipo": D("154067.10977835985"), "comision_tercero": D("0"), "comision_real_vp": D("1386603.9880052388")},
    ),
    Caso(
        codigo='VVP-3 PROMESA',
        modelo='MERCADO_PRIMARIO',
        estado='CERRADO',
        base=D("241755513.61"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.02"), "pct_lado_comprador": D("0"), "pct_rebate_concentrador": D("0"), "pct_broker_vendedor": D("0.01"), "pct_broker_comprador": D("0"), "pct_vp_vendedor": D("0.01"), "pct_vp_comprador": D("0"), "pct_equipo": D("0.1"), "pct_tercero": D("0.03")},
        esperado={"comision_total": D("4835110"), "comision_broker": D("2417555.13612"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("2417555.13612"), "comision_equipo": D("234502.84820364002"), "comision_tercero": D("72526.65408359999"), "comision_real_vp": D("2110525.63383276")},
    ),
    Caso(
        codigo='VVP-3 ESCRITURA',
        modelo='MERCADO_PRIMARIO',
        estado='CERRADO',
        base=D("242262863.32"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.01"), "pct_lado_comprador": D("0"), "pct_rebate_concentrador": D("0"), "pct_broker_vendedor": D("0.005"), "pct_broker_comprador": D("0"), "pct_vp_vendedor": D("0.005"), "pct_vp_comprador": D("0"), "pct_equipo": D("0.1"), "pct_tercero": D("0.03")},
        esperado={"comision_total": D("2422629"), "comision_broker": D("1211314.316586"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("1211314.316586"), "comision_equipo": D("117497.488708842"), "comision_tercero": D("36339.42949757999"), "comision_real_vp": D("1057477.3983795778")},
    ),
    Caso(
        codigo='VVP-4',
        modelo='SECUNDARIO_CONCENTRADORES',
        estado='PERDIDO',
        base=D("42914480.40"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.02"), "pct_lado_comprador": D("0.02"), "pct_rebate_concentrador": D("0.12"), "pct_broker_vendedor": D("0"), "pct_broker_comprador": D("0.012"), "pct_vp_vendedor": D("0.008"), "pct_vp_comprador": D("0.008"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("858290"), "comision_broker": D("514973.7648"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("343315.8432"), "comision_equipo": D("34331.58432"), "comision_tercero": D("0"), "comision_real_vp": D("308984.25888")},
    ),
    Caso(
        codigo='VVP-6',
        modelo='SECUNDARIO_CONCENTRADORES',
        estado='PERDIDO',
        base=D("70577298.72"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.02"), "pct_lado_comprador": D("0.02"), "pct_rebate_concentrador": D("0.12"), "pct_broker_vendedor": D("0"), "pct_broker_comprador": D("0.012"), "pct_vp_vendedor": D("0.008"), "pct_vp_comprador": D("0.008"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("1411546"), "comision_broker": D("846927.58464"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("564618.38976"), "comision_equipo": D("56461.83897600001"), "comision_tercero": D("0"), "comision_real_vp": D("508156.550784")},
    ),
    Caso(
        codigo='VVP-7',
        modelo='SECUNDARIO_CONCENTRADORES',
        estado='PERDIDO',
        base=D("62818714.40"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.02"), "pct_lado_comprador": D("0.02"), "pct_rebate_concentrador": D("0.12"), "pct_broker_vendedor": D("0"), "pct_broker_comprador": D("0.012"), "pct_vp_vendedor": D("0.008"), "pct_vp_comprador": D("0.008"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("1256374"), "comision_broker": D("753824.5728"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("502549.7152"), "comision_equipo": D("50254.97152"), "comision_tercero": D("0"), "comision_real_vp": D("452294.74367999996")},
    ),
    Caso(
        codigo='VVP-8',
        modelo='SECUNDARIO_CONCENTRADORES',
        estado='PERDIDO',
        base=D("74152306.75"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.02"), "pct_lado_comprador": D("0.02"), "pct_rebate_concentrador": D("0.12"), "pct_broker_vendedor": D("0"), "pct_broker_comprador": D("0.012"), "pct_vp_vendedor": D("0.008"), "pct_vp_comprador": D("0.008"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("1483046"), "comision_broker": D("889827.681"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("593218.454"), "comision_equipo": D("59321.845400000006"), "comision_tercero": D("0"), "comision_real_vp": D("533896.6086")},
    ),
    Caso(
        codigo='VVP-9',
        modelo='SECUNDARIO_CONCENTRADORES',
        estado='PERDIDO',
        base=D("50052797.06"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.02"), "pct_lado_comprador": D("0.02"), "pct_rebate_concentrador": D("0.12"), "pct_broker_vendedor": D("0"), "pct_broker_comprador": D("0.012"), "pct_vp_vendedor": D("0.008"), "pct_vp_comprador": D("0.008"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("1001056"), "comision_broker": D("600633.564672"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("400422.376448"), "comision_equipo": D("40042.23764480001"), "comision_tercero": D("0"), "comision_real_vp": D("360380.13880320004")},
    ),
    Caso(
        codigo='VVP-10',
        modelo='SECUNDARIO_CONCENTRADORES',
        estado='PERDIDO',
        base=D("92165688.80"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.02"), "pct_lado_comprador": D("0.02"), "pct_rebate_concentrador": D("0.12"), "pct_broker_vendedor": D("0"), "pct_broker_comprador": D("0.012"), "pct_vp_vendedor": D("0.008"), "pct_vp_comprador": D("0.008"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("1843314"), "comision_broker": D("1105988.2656"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("737325.5104"), "comision_equipo": D("73732.55104"), "comision_tercero": D("0"), "comision_real_vp": D("663592.95936")},
    ),
    Caso(
        codigo='VVP-11',
        modelo='SECUNDARIO_CONCENTRADORES',
        estado='PERDIDO',
        base=D("70531637.76"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.02"), "pct_lado_comprador": D("0.02"), "pct_rebate_concentrador": D("0.12"), "pct_broker_vendedor": D("0"), "pct_broker_comprador": D("0.012"), "pct_vp_vendedor": D("0.008"), "pct_vp_comprador": D("0.008"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("1410633"), "comision_broker": D("846379.65312"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("564253.1020800001"), "comision_equipo": D("56425.31020800001"), "comision_tercero": D("0"), "comision_real_vp": D("507827.7918720001")},
    ),
    Caso(
        codigo='VVP-12',
        modelo='SECUNDARIO_CONCENTRADORES',
        estado='PERDIDO',
        base=D("79407000.00"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.02"), "pct_lado_comprador": D("0.02"), "pct_rebate_concentrador": D("0.12"), "pct_broker_vendedor": D("0"), "pct_broker_comprador": D("0.012"), "pct_vp_vendedor": D("0.008"), "pct_vp_comprador": D("0.008"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("1588140"), "comision_broker": D("952884"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("635256"), "comision_equipo": D("63525.600000000006"), "comision_tercero": D("0"), "comision_real_vp": D("571730.4")},
    ),
    Caso(
        codigo='VVP-13',
        modelo='SECUNDARIO_CONCENTRADORES',
        estado='PERDIDO',
        base=D("43004530.80"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.02"), "pct_lado_comprador": D("0.02"), "pct_rebate_concentrador": D("0.12"), "pct_broker_vendedor": D("0"), "pct_broker_comprador": D("0.012"), "pct_vp_vendedor": D("0.008"), "pct_vp_comprador": D("0.008"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("860091"), "comision_broker": D("516054.3696000001"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("344036.24640000006"), "comision_equipo": D("34403.62464000001"), "comision_tercero": D("0"), "comision_real_vp": D("309632.62176000007")},
    ),
    Caso(
        codigo='VVP-14',
        modelo='SECUNDARIO_CONCENTRADORES',
        estado='PERDIDO',
        base=D("74304807.80"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.02"), "pct_lado_comprador": D("0.02"), "pct_rebate_concentrador": D("0.12"), "pct_broker_vendedor": D("0"), "pct_broker_comprador": D("0.012"), "pct_vp_vendedor": D("0.008"), "pct_vp_comprador": D("0.008"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("1486096"), "comision_broker": D("891657.6936"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("594438.4624"), "comision_equipo": D("59443.84624"), "comision_tercero": D("0"), "comision_real_vp": D("534994.61616")},
    ),
    Caso(
        codigo='VVP-15',
        modelo='SECUNDARIO_CONCENTRADORES',
        estado='ACTIVO',
        base=D("51450005.38"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.02"), "pct_lado_comprador": D("0.02"), "pct_rebate_concentrador": D("0.12"), "pct_broker_vendedor": D("0"), "pct_broker_comprador": D("0"), "pct_vp_vendedor": D("0"), "pct_vp_comprador": D("0.02"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("1029000"), "comision_broker": D("0"), "rebate_concentrador": D("123480.0129024"), "comision_vp_bruta": D("1029000.1075200001"), "comision_equipo": D("102900.01075200002"), "comision_tercero": D("0"), "comision_real_vp": D("1049580.1096704002")},
    ),
    Caso(
        codigo='VVP-16',
        modelo='SECUNDARIO_CONCENTRADORES',
        estado='CERRADO',
        base=D("43025295.00"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.04"), "pct_lado_comprador": D("0.02"), "pct_rebate_concentrador": D("0.12"), "pct_broker_vendedor": D("0"), "pct_broker_comprador": D("0.012"), "pct_vp_vendedor": D("0"), "pct_vp_comprador": D("0.008"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("860506"), "comision_broker": D("516303.54000000004"), "rebate_concentrador": D("206521.416"), "comision_vp_bruta": D("344202.36"), "comision_equipo": D("34420.236"), "comision_tercero": D("0"), "comision_real_vp": D("516303.54")},
    ),
    Caso(
        codigo='VVP-17',
        modelo='SECUNDARIO_CONCENTRADORES',
        estado='ACTIVO',
        base=D("80697078.00"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.02"), "pct_lado_comprador": D("0.02"), "pct_rebate_concentrador": D("0.12"), "pct_broker_vendedor": D("0"), "pct_broker_comprador": D("0.012"), "pct_vp_vendedor": D("0"), "pct_vp_comprador": D("0.008"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("1613942"), "comision_broker": D("968364.936"), "rebate_concentrador": D("193672.9872"), "comision_vp_bruta": D("645576.6240000001"), "comision_equipo": D("64557.66240000001"), "comision_tercero": D("0"), "comision_real_vp": D("774691.9488")},
    ),
    Caso(
        codigo='VVP-18',
        modelo='SECUNDARIO_AGENCIA',
        estado='CERRADO',
        base=D("1215785.00"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.5"), "pct_lado_comprador": D("0.5"), "pct_rebate_concentrador": D("0"), "pct_broker_vendedor": D("0.4"), "pct_broker_comprador": D("0"), "pct_vp_vendedor": D("0.6"), "pct_vp_comprador": D("0"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("1215785"), "comision_broker": D("486314"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("729471"), "comision_equipo": D("72947.1"), "comision_tercero": D("0"), "comision_real_vp": D("656523.9")},
    ),
    Caso(
        codigo='VVP-19',
        modelo='SECUNDARIO_AGENCIA',
        estado='CERRADO',
        base=D("1096945.74"),
        base_manual=None,
        tasas={"pct_lado_vendedor": D("0.5"), "pct_lado_comprador": D("0.5"), "pct_rebate_concentrador": D("0"), "pct_broker_vendedor": D("0.4"), "pct_broker_comprador": D("0"), "pct_vp_vendedor": D("0.6"), "pct_vp_comprador": D("0"), "pct_equipo": D("0.1"), "pct_tercero": D("0")},
        esperado={"comision_total": D("1096946"), "comision_broker": D("438778.29600000003"), "rebate_concentrador": D("0"), "comision_vp_bruta": D("658167.444"), "comision_equipo": D("65816.74440000001"), "comision_tercero": D("0"), "comision_real_vp": D("592350.6996")},
    ),
]
