"""Límite de intentos de login y política de contraseñas.

**El límite corta antes de verificar el hash.** Ese es el punto: cada
verificación Argon2id cuesta ~70 ms de CPU, así que un límite que se evaluara
*después* frenaría la fuerza bruta pero no la saturación. Acá se consulta la
tabla, y si la clave está bloqueada se rechaza sin tocar el hash.

**Se cuenta por email y por IP, y las dos cosas hacen falta.** Por email protege
la cuenta: alguien que conoce un correo y prueba claves. Por IP protege el
servidor: alguien que prueba correos al azar, que después del arreglo de la fuga
de tiempos también consume CPU. Una sola de las dos deja el otro flanco abierto.

**La ventana es un bloqueo, no un descarte de contador.** Después de N fallos la
clave queda bloqueada un rato; pasado ese rato se vuelve a contar de cero. Es más
simple de explicar a quien se queda afuera que una curva exponencial, y para dos
usuarios internos alcanza.

**La política de contraseñas es solo largo mínimo, más una lista corta de las
peores.** No se piden mayúsculas ni símbolos: esas reglas producen `Viveprop2026!`
--que cumple todo y es adivinable-- en vez de contraseñas mejores. El largo es lo
único que correlaciona de verdad con resistencia.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.intento_login import IntentoLogin

# Por email: protege la cuenta. Cinco fallos son suficientes para que alguien que
# se equivoca de verdad no se quede afuera, y pocos para que probar claves no
# sirva.
UMBRAL_EMAIL = 5
# Por IP: mas alto, porque una oficina comparte salida y varias personas pueden
# equivocarse el mismo dia sin ser un ataque.
UMBRAL_IP = 20

BLOQUEO = timedelta(minutes=15)

# Cuanto se guarda una fila sin actividad antes de que la limpieza la borre.
RETENCION = timedelta(days=7)

LARGO_MINIMO = 10

# Las peores, en minuscula y sin espacios. La lista es corta a proposito: no
# pretende ser un diccionario, solo atajar lo que alguien escribe con prisa. Va
# `viveprop` y sus variantes porque es exactamente lo que se elige cuando hay que
# inventar una clave en el momento.
PROHIBIDAS = frozenset({
    "123456", "1234567", "12345678", "123456789", "1234567890",
    "password", "contrasena", "contraseña", "qwerty", "abc123",
    "111111", "000000", "iloveyou", "admin", "administrador",
    "viveprop", "viveprop2026", "viveprop2025", "operaciones",
})


class DemasiadosIntentos(Exception):
    """La clave está bloqueada. Lleva los segundos que faltan."""

    def __init__(self, segundos: int):
        self.segundos = segundos
        super().__init__(f"Demasiados intentos. Probá de nuevo en {segundos} segundos.")


class ClaveDebil(Exception):
    """La contraseña no cumple la política."""


def validar_clave(clave: str) -> None:
    """Lanza `ClaveDebil` si no sirve. No devuelve nada: o pasa o falla.

    Se valida el largo sobre la cadena tal cual, sin recortar espacios: si alguien
    eligió una frase con espacios, esos espacios son parte de su contraseña.
    """
    if len(clave) < LARGO_MINIMO:
        raise ClaveDebil(
            f"La contraseña tiene que tener al menos {LARGO_MINIMO} caracteres."
        )
    if clave.strip().lower().replace(" ", "") in PROHIBIDAS:
        raise ClaveDebil(
            "Esa contraseña es de las más usadas del mundo. Elegí otra."
        )


def _clave_email(email: str) -> str:
    # En minuscula: si no, MAIL@x y mail@x contarian por separado y el limite se
    # esquivaria cambiando el case.
    return f"email:{email.strip().lower()}"


def _clave_ip(ip: str) -> str:
    return f"ip:{ip}"


def _claves(email: str, ip: str | None) -> list[tuple[str, int]]:
    claves = [(_clave_email(email), UMBRAL_EMAIL)]
    if ip:
        claves.append((_clave_ip(ip), UMBRAL_IP))
    return claves


def _filas(db: Session, claves: list[str]) -> dict[str, IntentoLogin]:
    """Las dos filas en una sola consulta.

    El login es un camino caliente y cada consulta es un viaje de red: con dos
    `get` por verificación más dos por registro, un intento gastaba seis viajes.
    Traerlas juntas los reduce a la mitad.
    """
    filas = db.execute(
        select(IntentoLogin).where(IntentoLogin.clave.in_(claves))
    ).scalars().all()
    return {f.clave: f for f in filas}


def verificar(db: Session, email: str, ip: str | None, ahora: datetime | None = None) -> None:
    """Lanza `DemasiadosIntentos` si el email o la IP están bloqueados.

    Se llama **antes** de verificar la contraseña. Si se llamara después, el
    bloqueo evitaría adivinar la clave pero no evitaría el gasto de CPU, que es la
    mitad del problema.
    """
    ahora = ahora or datetime.now(timezone.utc)
    claves = [c for c, _ in _claves(email, ip)]
    for fila in _filas(db, claves).values():
        if fila.bloqueado_hasta is None:
            continue
        hasta = _aware(fila.bloqueado_hasta)
        if hasta > ahora:
            raise DemasiadosIntentos(int((hasta - ahora).total_seconds()) + 1)


def registrar_fallo(db: Session, email: str, ip: str | None, ahora: datetime | None = None) -> None:
    """Suma uno a las dos claves y bloquea la que llegó a su umbral."""
    ahora = ahora or datetime.now(timezone.utc)
    pares = _claves(email, ip)
    existentes = _filas(db, [c for c, _ in pares])
    for clave, umbral in pares:
        fila = existentes.get(clave)
        if fila is None:
            fila = IntentoLogin(clave=clave, fallidos=0)
            db.add(fila)
        # Si venia de un bloqueo ya vencido, el contador arranca de cero: la
        # ventana cumplida perdona lo anterior.
        vencido = fila.bloqueado_hasta is not None and _aware(fila.bloqueado_hasta) <= ahora
        fila.fallidos = 1 if vencido else fila.fallidos + 1
        fila.bloqueado_hasta = ahora + BLOQUEO if fila.fallidos >= umbral else None
        fila.actualizado_en = ahora
    db.commit()


def registrar_exito(db: Session, email: str, ip: str | None) -> None:
    """Borra las filas: entrar bien limpia el historial de esa cuenta y esa IP."""
    claves = [c for c, _ in _claves(email, ip)]
    db.execute(delete(IntentoLogin).where(IntentoLogin.clave.in_(claves)))
    db.commit()


def limpiar_viejos(db: Session, ahora: datetime | None = None) -> int:
    """Borra las filas sin actividad reciente.

    Sin esto la tabla crece con una fila por cada IP que probó una vez y no volvió.
    """
    ahora = ahora or datetime.now(timezone.utc)
    resultado = db.execute(
        delete(IntentoLogin).where(IntentoLogin.actualizado_en < ahora - RETENCION)
    )
    db.commit()
    return resultado.rowcount or 0


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)
