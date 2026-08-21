from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import (
    auth,
    canjes,
    catalogos,
    health,
    negocios,
    reportes,
    tipos_movimiento,
    uf,
    usuarios,
)

app = FastAPI(title="Viveprop Operaciones")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(usuarios.router, prefix="/api")
app.include_router(canjes.router, prefix="/api")
app.include_router(catalogos.router, prefix="/api")
app.include_router(negocios.router, prefix="/api")
app.include_router(uf.router, prefix="/api")
app.include_router(reportes.router, prefix="/api")
app.include_router(tipos_movimiento.router, prefix="/api")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def resolver_ruta_spa(static_dir: Path, full_path: str) -> Path:
    """Qué archivo servir para una ruta que no matcheó ningún router.

    Está afuera de la ruta y recibe el directorio por parámetro para que se
    pueda probar: `static/` solo existe en el servidor, lo arma el build de
    Render, así que un test contra la app no ejercitaría nada en local.

    **Un `/api/...` sin router es un 404 de API, no una ruta de la SPA.** Antes
    devolvía 200 con el `index.html`, así que un cliente que pega en un endpoint
    mal escrito recibía HTML donde espera JSON y el error aparecía lejos de su
    causa. Verificado en producción el 2026-08-21: `/api/esto-no-existe`
    respondía `200 text/html`.

    **La ruta no se arma con la URL sin revisarla.** `static_dir / full_path` con
    un `full_path` que sube de directorio apuntaría fuera de `static/`, y ahí
    abajo están el código y el `.env`. Se resuelve y se comprueba que quede
    dentro antes de abrir nada.

    Cualquier otra ruta cae en el `index.html`, que es lo que tiene que pasar:
    el ruteo de la SPA es del lado del navegador.
    """
    if full_path == "api" or full_path.startswith("api/"):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Endpoint no encontrado.")

    raiz = static_dir.resolve()
    candidato = (raiz / full_path).resolve()
    if candidato.is_file() and candidato.is_relative_to(raiz):
        return candidato
    return raiz / "index.html"


if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa_catch_all(full_path: str):
        return FileResponse(resolver_ruta_spa(STATIC_DIR, full_path))
