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
from app.services.vista_directorio import VistaDirectorio, obtener_vista_directorio
from app.services.reporte_semanal import (
    DIAS_ESTANCADO_DEFECTO,
    ReporteSemanal,
    obtener_reporte_semanal,
)

router = APIRouter(prefix="/reportes", tags=["reportes"])

MAX_DIAS = 366


@router.get("/semanal", response_model=ReporteSemanal)
def semanal(
    desde: date | None = Query(None, description="Inicio del período. Por defecto, el lunes de esta semana."),
    hasta: date | None = Query(None, description="Fin del período, incluido."),
    dias_estancado: int = Query(
        DIAS_ESTANCADO_DEFECTO,
        ge=1,
        le=365,
        description="Días sin movimiento para considerar algo estancado.",
    ),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Qué se cerró, qué avanzó, qué se cayó y qué está estancado.

    El período es libre y no solo semanal: el nombre viene del uso previsto, pero
    sirve igual para una quincena o un mes.
    """
    if (desde is None) != (hasta is None):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Hay que indicar 'desde' y 'hasta' juntos, o ninguno de los dos.",
        )
    if desde is not None and hasta is not None:
        if hasta < desde:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"'hasta' ({hasta}) es anterior a 'desde' ({desde}).",
            )
        if (hasta - desde).days > MAX_DIAS:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"El período no puede pasar de {MAX_DIAS} días.",
            )

    return obtener_reporte_semanal(db, desde, hasta, dias_estancado)


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
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """La vista ejecutiva: cuánto entró, de dónde, qué hay por delante.

    La proyección va como **rango** y con el `n` visible. Con 17 negocios
    resueltos, la tasa de conversión tiene un intervalo de confianza de casi 50
    puntos: dar una cifra puntual sería darle al directorio falsa precisión sobre
    una decisión de plata.
    """
    return obtener_vista_directorio(db)
