"""Tareas de fondo del propio web service.

**Por qué acá y no un Cron Job de Render.** Un Cron Job es un servicio aparte
que se cobra aparte, y esto se ejecuta para algo que el SII publica una vez al
mes. Una tarea dentro del proceso que ya está corriendo no cuesta nada y no
agrega infraestructura que mantener.

**Corre sin miedo a repetirse.** La escritura es un upsert por fecha, así que
ejecutarla dos veces no duplica ni cambia nada. Eso es lo que hace que sea
seguro tenerla acá: si algún día hay más de una instancia, cada una la corre y
el resultado es el mismo.

**Nunca tumba la aplicación.** Si el SII no responde, o cambió el formato, la
tarea lo registra y sigue durmiendo. La app funciona igual: la UF que ya está
cargada alcanza para valorizar, y la carga manual de la plantilla sigue ahí.
"""
import asyncio
import logging
from datetime import datetime, timezone

from app.db import SessionLocal
from app.services.importar_uf import estado_serie
from app.services.uf_sii import SIINoDisponible, actualizar_desde_sii

log = logging.getLogger(__name__)

INTERVALO = 60 * 60 * 24  # una vez al día
ESPERA_INICIAL = 30  # segundos: deja que el arranque termine antes de salir a la red

# Se descarga cuando quedan menos de estos días de serie por delante. El SII
# publica hasta el 9 del mes siguiente, así que con 20 días de colchón el chequeo
# encuentra el mes nuevo poco después de que se publica, sin pedir la página
# todos los días para nada.
COLCHON_MINIMO = 20


def _hace_falta(db) -> bool:
    estado = estado_serie(db, datetime.now(timezone.utc).date())
    if estado.dias_de_colchon is None:
        return True  # serie vacía
    return estado.dias_de_colchon < COLCHON_MINIMO


def actualizar_uf_si_hace_falta() -> None:
    """Un ciclo del chequeo. Síncrono y sin excepciones hacia afuera."""
    try:
        with SessionLocal() as db:
            if not _hace_falta(db):
                return
            resumen = actualizar_desde_sii(db, datetime.now(timezone.utc).date())
    except SIINoDisponible as exc:
        # Aviso, no error: es una falla de un tercero y hay salida manual.
        log.warning("UF: no se pudo actualizar desde el SII (%s)", exc)
        return
    except Exception:
        log.exception("UF: falla inesperada al actualizar desde el SII")
        return

    log.info(
        "UF: %s nuevas, %s actualizadas, serie hasta %s",
        resumen.carga.nuevas,
        resumen.carga.actualizadas,
        resumen.ultima,
    )


async def ciclo_uf() -> None:
    """Chequea la UF cada día hasta que se cancele.

    El trabajo va en un hilo porque `httpx.get` y SQLAlchemy son síncronos:
    llamarlos directo acá bloquearía el event loop y con él todas las
    peticiones que estén en vuelo.
    """
    await asyncio.sleep(ESPERA_INICIAL)
    while True:
        await asyncio.to_thread(actualizar_uf_si_hace_falta)
        await asyncio.sleep(INTERVALO)
