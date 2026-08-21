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
