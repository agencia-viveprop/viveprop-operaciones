"""Reportes que cruzan los dos dominios.

Va en su propio router porque no pertenece ni a canjes ni a negocios: los
reportes de periodo miran los dos. Los reportes de un solo dominio siguen en el
router de ese dominio, como `GET /api/negocios/reportes/resumen`.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.usuario import Usuario
from app.services.reporte_mensual import (
    VENTANA_DEFECTO,
    VENTANAS_VALIDAS,
    ReporteMensual,
    obtener_reporte_mensual,
)
from app.services.obligaciones import Cobranza, obtener_cobranza
from app.services.vista_directorio import VistaDirectorio, obtener_vista_directorio
from app.services.reporte_semanal import (
    MESES_DEFECTO,
    MESES_VALIDOS,
    ReporteSemanal,
    obtener_reporte_semanal,
)

router = APIRouter(prefix="/reportes", tags=["reportes"])

MAX_DIAS = 366


@router.get("/semanal", response_model=ReporteSemanal)
def semanal(
    anio: int | None = Query(None, ge=2022, le=2100, description="Año. Por defecto, el actual."),
    mes: int | None = Query(None, ge=1, le=12, description="Mes. Por defecto, el actual."),
    meses: int = Query(
        MESES_DEFECTO,
        description=(
            "Cuántos meses comparar, contando el elegido. Uno es «solo este mes, sin "
            f"comparación»; el tope es {max(MESES_VALIDOS)}."
        ),
    ),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Cómo se movió el mes, semana a semana, contra los meses anteriores.

    **El eje es la semana del mes.** Los parámetros cambiaron: antes eran
    `desde`/`hasta`/`dias_estancado` y medían una ventana de semanas corridas, que
    no permitía comparar nada con los meses previos (`D-098`).
    """
    if (anio is None) != (mes is None):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Hay que indicar 'anio' y 'mes' juntos, o ninguno de los dos.",
        )
    if meses not in MESES_VALIDOS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Los meses a comparar tienen que ser uno de {list(MESES_VALIDOS)}.",
        )
    return obtener_reporte_semanal(db, anio, mes, meses)


@router.get("/mensual", response_model=ReporteMensual)
def mensual(
    anio: int | None = Query(None, ge=2022, le=2100, description="Año. Por defecto, el actual."),
    mes: int | None = Query(None, ge=1, le=12, description="Mes. Por defecto, el actual."),
    ventana: int = Query(
        VENTANA_DEFECTO,
        description=f"Largo de la ventana móvil, en meses. Uno de {list(VENTANAS_VALIDAS)}.",
    ),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Una ventana móvil contra la anterior, más el año corrido contra el pasado.

    El mes calendario va como detalle y no como titular: en un negocio donde los
    procesos duran de un mes a varios, un mes en cero no es un mes malo, y la
    comparación mes contra mes mide ruido. Sobre los datos reales, 4 de 11 meses
    estuvieron vacíos.
    """
    if (anio is None) != (mes is None):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Hay que indicar 'anio' y 'mes' juntos, o ninguno de los dos.",
        )
    if ventana not in VENTANAS_VALIDAS:
        # 422 y no 400: es un valor fuera del conjunto permitido, igual que lo
        # que devolvería la validación del propio Query si fuera un enum.
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"La ventana tiene que ser una de {list(VENTANAS_VALIDAS)}.",
        )
    return obtener_reporte_mensual(db, anio, mes, ventana)


@router.get("/directorio", response_model=VistaDirectorio)
def directorio(
    ventana: int = Query(
        VENTANA_DEFECTO, description=f"Meses de la ventana móvil: {list(VENTANAS_VALIDAS)}"
    ),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """La vista ejecutiva, separada por dominio: cuánto entró, de dónde, qué viene.

    La proyección va como **rango** y con el `n` visible. Con 17 negocios
    resueltos, la tasa de conversión tiene un intervalo de confianza de casi 50
    puntos: dar una cifra puntual sería darle al directorio falsa precisión sobre
    una decisión de plata.

    **La ventana solo alcanza lo temporal** --la ventana móvil, la serie, la
    tendencia y los conteos de canjes del período--. Los buckets, la tasa de
    cierre, el ticket y la proyección siguen siendo históricos: un negocio abierto
    no pertenece a un mes, y una tasa sobre uno o dos casos resueltos no es una tasa.
    """
    if ventana not in VENTANAS_VALIDAS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"La ventana tiene que ser una de {list(VENTANAS_VALIDAS)}.",
        )
    return obtener_vista_directorio(db, ventana=ventana)


@router.get("/cobranza", response_model=Cobranza)
def cobranza(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Todo lo facturable y pagable de los dos mundos, agrupado por parte.

    Va acá y no en el router de negocios porque cruza los dos dominios, como el
    reporte semanal. **No hay un gran total**: los seis conceptos de negocios son
    dos niveles de la misma plata --la comisión total se reparte, y lo que le queda
    a ViveProp se reparte otra vez-- así que sumarlos contaría lo mismo dos veces;
    y la de canjes es de Dataprop, que no se suma con la de ViveProp por definición.
    """
    return obtener_cobranza(db)
