"""Los dominios de correo de la organización, administrables desde la app.

**Qué son y qué no son.** Son la lista de dominios que se aceptan sin preguntar
al crear un usuario. Cualquier otro correo **también se puede usar**, pero pide
que un admin lo autorice explícitamente como externo, y ese acto queda con
nombre y fecha en la ficha del usuario.

No son el control de acceso. La app **nunca manda correos** --no hay SMTP ni
recuperación de clave por mail-- así que una dirección equivocada no le entrega
nada a nadie: la cuenta la crea un admin fijando la clave, y la clave viaja por
fuera. Lo que esta lista evita es el desorden y el dedazo, no la intrusión. Quien
corta un acceso es el switch `activo`, que se chequea en cada request.

**La lista vacía cierra, no abre.** Si un admin borra todos los dominios, todo
correo pasa a requerir autorización explícita. Antes esto vivía en la variable de
entorno `DOMINIOS_EMAIL`, donde vacío significaba «sin restricción»: un campo que
se edita a mano no puede tener un accidente que abra la aplicación en silencio.

**Y no re-valida hacia atrás.** La lista se aplica al crear un usuario o al
cambiarle el correo. Quitar un dominio no le saca el acceso a nadie que ya lo
tenga -- para eso está `activo` (`D-078`).
"""
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.catalogo import Catalogo, TipoCatalogo

TIPO = TipoCatalogo.DOMINIO_ORGANIZACION.value

# `catalogos.codigo` es varchar(40). Alcanza de sobra para un dominio real y deja
# el límite dicho en un solo lugar.
LARGO_MAXIMO = 40

# Un dominio, no una URL ni un correo: etiquetas separadas por puntos, sin
# guiones al principio ni al final de cada etiqueta, y al menos un punto.
FORMA = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$")


class DominioInvalido(ValueError):
    """Lo que se escribió no es un dominio."""


class DominioDuplicado(ValueError):
    """Ese dominio ya está en la lista."""


def normalizar(entrada: str) -> str:
    """Deja el dominio como se guarda, o explica por qué no sirve.

    Acepta que le peguen un correo completo o un `@dominio.cl` y se queda con el
    dominio: es lo que uno tiene a mano cuando está agregando el dominio de
    alguien, y rechazarlo por eso sería un trámite inventado.
    """
    texto = (entrada or "").strip().lower()
    if "@" in texto:
        texto = texto.rsplit("@", 1)[-1].strip()
    texto = texto.strip(".")

    if not texto:
        raise DominioInvalido("Escribe un dominio, por ejemplo viveprop.com.")
    if len(texto) > LARGO_MAXIMO:
        raise DominioInvalido(f"El dominio no puede pasar de {LARGO_MAXIMO} caracteres.")
    if not FORMA.match(texto):
        raise DominioInvalido(
            f"«{texto}» no parece un dominio. Se espera algo como viveprop.com, sin espacios ni tildes."
        )
    return texto


def listar(db: Session) -> list[Catalogo]:
    """Los dominios activos y los desactivados, en su orden.

    Los desactivados vienen igual: la pantalla los muestra apagados, y así se ve
    que alguien los quitó a propósito en vez de que nunca hubieran estado.
    """
    return list(
        db.scalars(
            select(Catalogo).where(Catalogo.tipo == TIPO).order_by(Catalogo.orden, Catalogo.codigo)
        ).all()
    )


def dominios_activos(db: Session) -> set[str]:
    return {c.codigo for c in listar(db) if c.activo}


def es_de_la_organizacion(db: Session, email: str) -> bool:
    """Si ese correo entra sin pedir autorización.

    Con la lista vacía devuelve `False` para todo, que es el fallo cerrado: pide
    autorización explícita en vez de aceptar cualquier cosa.
    """
    dominio = (email or "").rsplit("@", 1)[-1].strip().lower()
    return bool(dominio) and dominio in dominios_activos(db)


def agregar(db: Session, entrada: str, nombre: str | None = None) -> Catalogo:
    dominio = normalizar(entrada)
    existente = db.scalar(
        select(Catalogo).where(Catalogo.tipo == TIPO, Catalogo.codigo == dominio)
    )
    if existente is not None:
        # Reactivar el que estaba apagado, en vez de un 409 que obliga a
        # borrarlo primero para poder volver a agregarlo.
        if existente.activo:
            raise DominioDuplicado(f"«{dominio}» ya está en la lista.")
        existente.activo = True
        if nombre:
            existente.nombre = nombre
        db.commit()
        db.refresh(existente)
        return existente

    ultimo = max((c.orden or 0) for c in listar(db)) if listar(db) else 0
    fila = Catalogo(
        tipo=TIPO,
        codigo=dominio,
        # El nombre es para leer la lista --«Dataprop» al lado de dataprop.cl--.
        # Sin nombre se repite el dominio: la columna no admite nulo y poner un
        # guion sería peor.
        nombre=(nombre or dominio).strip(),
        orden=ultimo + 1,
        activo=True,
    )
    db.add(fila)
    db.commit()
    db.refresh(fila)
    return fila


def desactivar(db: Session, dominio_id: int) -> Catalogo | None:
    """Lo apaga sin borrarlo: la lista es un registro de decisiones.

    Devuelve `None` si ese id no es un dominio, para que el router responda 404
    en vez de apagar una alianza por un id equivocado.
    """
    fila = db.get(Catalogo, dominio_id)
    if fila is None or fila.tipo != TIPO:
        return None
    fila.activo = False
    db.commit()
    db.refresh(fila)
    return fila
