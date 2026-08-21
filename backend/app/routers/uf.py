from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, status
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
from app.services.uf_sii import (
    ANIO_MINIMO,
    ResumenSII,
    SIINoDisponible,
    actualizar_desde_sii,
    cargar_historia,
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
    usuario: Usuario = Depends(require_role(RolUsuario.admin)),
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
    usuario: Usuario = Depends(require_role(RolUsuario.admin)),
):
    if not archivo.filename or not archivo.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El archivo debe ser un .xlsx")

    contenido = await archivo.read()
    try:
        return cargar_desde_xlsx(db, contenido)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))


@router.post("/actualizar-desde-sii", response_model=ResumenSII)
def actualizar_desde_sii_endpoint(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.admin)),
):
    """Trae la serie que publica el SII y la guarda.

    Existe además de la tarea de fondo para no tener que esperar el tick: el
    caso típico es que el SII acabe de publicar el mes y alguien lo necesite ya.

    Un 502 y no un 500 cuando el SII no responde: la falla es de un tercero, no
    nuestra, y quien lo lea tiene que poder distinguirlo para saber que la salida
    es cargar la plantilla a mano.
    """
    try:
        return actualizar_desde_sii(db, _hoy())
    except SIINoDisponible as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc


@router.post("/cargar-historia", response_model=ResumenSII)
def cargar_historia_endpoint(
    desde_anio: int = Query(ANIO_MINIMO, ge=ANIO_MINIMO, description="Primer año a traer."),
    hasta_anio: int | None = Query(None, description="Último año. Por defecto, el actual."),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.admin)),
):
    """Trae varios años del SII de una vez, para rellenar una serie incompleta.

    Separado de la actualización diaria porque son dos operaciones distintas:
    esta baja cinco páginas y es deliberada, la otra baja una y corre sola.

    Trae **años completos**, así que desde 2022 incluye los meses previos al
    primer canje. Es más simple que un corte a mitad de año y evita que un
    negocio con fecha de mediados de 2022 se quede sin poder valorizarse.
    """
    try:
        return cargar_historia(db, _hoy(), desde_anio, hasta_anio)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except SIINoDisponible as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc)) from exc
