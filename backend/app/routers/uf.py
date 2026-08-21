from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.db import get_db
from app.models.usuario import RolUsuario, Usuario
from app.services.importar_uf import (
    EstadoSerie,
    ResumenCargaUF,
    cargar_desde_xlsx,
    estado_serie,
    generar_plantilla,
)

router = APIRouter(prefix="/uf", tags=["uf"])

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _hoy() -> date:
    return datetime.now(timezone.utc).date()


@router.get("/estado", response_model=EstadoSerie)
def obtener_estado(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    """Hasta dónde llega la serie y si hay que hacer algo.

    Lo consume el mantenedor y también el dashboard, que muestra la alerta
    cuando la serie está vencida (D-008).
    """
    return estado_serie(db, _hoy())


@router.get("/plantilla")
def descargar_plantilla(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    """El .xlsx con las fechas que faltan ya escritas y el valor en blanco."""
    contenido = generar_plantilla(db, _hoy())
    nombre = f"uf-{_hoy().isoformat()}.xlsx"
    return Response(
        content=contenido,
        media_type=XLSX,
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )


@router.post("/importar", response_model=ResumenCargaUF)
async def importar(
    archivo: UploadFile,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    if not archivo.filename or not archivo.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El archivo debe ser un .xlsx")

    contenido = await archivo.read()
    try:
        return cargar_desde_xlsx(db, contenido)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
