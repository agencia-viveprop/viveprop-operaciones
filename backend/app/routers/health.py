"""Dos chequeos distintos, a propósito separados.

`/health` dice que **el proceso está vivo**: responde sin tocar nada externo. Es
el que mira Render, y por eso no consulta la base. Neon suspende la rama cuando
no hay tráfico y despertarla toma unos segundos; si el chequeo de Render
dependiera de eso, un despertar lento se leería como servicio caído y Render
reiniciaría el proceso sin que hubiera nada roto.

`/health` también dice **qué commit está corriendo**. Suena a detalle y no lo es:
tres veces en el mismo día hubo que adivinar si lo que se acababa de subir era lo
que el servidor servía, y dos de esas la respuesta fue "no". Cuando el deploy no
cambia el frontend, el hash del bundle no sirve para distinguirlo, y no queda
ninguna señal. Ahora sí.

El SHA sale de `RENDER_GIT_COMMIT`, que Render pone solo en el ambiente. Se
expone sin sesión, igual que el resto del endpoint: en un repositorio privado un
SHA no abre ninguna puerta, y poder verificar un despliegue en un segundo vale
mucho más que esconderlo.

`/health/db` dice que **la base responde**, y es para diagnosticar. Cuando la app
carga pero ninguna pantalla trae datos, esta es la que distingue "se cayó el
servicio" de "se cayó la base", que fue exactamente la duda del 503 del
2026-08-20. Devuelve 200 con el detalle o 503 si la consulta falla.
"""
import os

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import get_db

router = APIRouter(tags=["health"])

# Render lo define en cada deploy. En local no existe, y ahí "local" es la
# respuesta correcta: no hay commit desplegado que reportar.
COMMIT = (os.environ.get("RENDER_GIT_COMMIT") or "local")[:7]


@router.get("/health")
def health():
    return {"status": "ok", "commit": COMMIT}


@router.get("/health/db")
def health_db(response: Response, db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as e:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        # El tipo de excepción sin el mensaje: el detalle de una falla de
        # conexión trae el host y a veces el usuario de la base, y este endpoint
        # no pide sesión.
        return {"status": "error", "base": type(e).__name__}
    return {"status": "ok", "base": "ok"}
