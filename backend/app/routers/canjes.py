from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Response, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import String, cast, select
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_role
from app.db import get_db
from app.models.canje import (
    Canje,
    CanjeEstado,
    CanjeEtapa,
    CorredorCanje,
    MonedaTipo,
    OperacionTipo,
)
from app.models.movimiento import EntityType, Movimiento, TipoMovimiento
from app.models.usuario import RolUsuario, Usuario
from app.services.bandeja_canjes import Bandeja, obtener_bandeja
from app.services.canjes_activos import ListadoCanjesActivos, obtener_listado
from app.services.plata_canjes import PlataCanjes, obtener_plata_canjes
from app.services.uf import UFNoDisponible
from app.services.estructura_archivo import EstructuraArchivo
from app.services.obligaciones import (
    ObligacionError,
    ObligacionOut,
    obligaciones_del_canje,
    registrar_avance,
)
from app.services.limpieza_canjes import borrar_canje
from app.services.importar_canjes import ImportarCanjesResumen, importar_canjes
from app.services.movimientos import (
    MovimientoError,
    crear_movimiento_canje,
    eliminar_movimiento_canje,
    registrar_cambio_de_etapa,
)
from app.services.plantilla_canjes import estructura_importacion, generar_plantilla
from app.services.reportes_canjes import ResumenCanjes, obtener_resumen_canjes

router = APIRouter(prefix="/canjes", tags=["canjes"])

XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class CanjeOut(BaseModel):
    id: int
    fecha_solicitud: datetime
    fecha_cierre: datetime | None
    estado: CanjeEstado
    etapa: CanjeEtapa
    corredor_solicitante_nombre: str | None
    corredor_solicitante_email: str | None
    corredor_propietario_nombre: str | None
    corredor_propietario_email: str | None
    tipo_operacion: OperacionTipo | None
    tipo_inmueble: str | None
    comuna: str | None
    direccion: str | None
    valor_prop: float | None
    moneda_valor: MonedaTipo | None
    link_propiedad: str | None
    valor_negocio: float | None
    valor_negocio_moneda: MonedaTipo | None
    comision_dataprop: float | None
    comision_dataprop_moneda: MonedaTipo | None
    notas: str | None
    gestionado_en_app: bool

    model_config = {"from_attributes": True}


class CanjeCreate(BaseModel):
    id: int
    fecha_solicitud: datetime
    estado: CanjeEstado = CanjeEstado.ACTIVO
    etapa: CanjeEtapa = CanjeEtapa.EN_REVISION
    corredor_solicitante_nombre: str | None = None
    corredor_solicitante_email: str | None = None
    corredor_propietario_nombre: str | None = None
    corredor_propietario_email: str | None = None
    tipo_operacion: OperacionTipo | None = None
    tipo_inmueble: str | None = None
    comuna: str | None = None
    direccion: str | None = None
    valor_prop: float | None = None
    moneda_valor: MonedaTipo | None = None
    link_propiedad: str | None = None
    valor_negocio: float | None = None
    valor_negocio_moneda: MonedaTipo | None = None
    comision_dataprop: float | None = None
    comision_dataprop_moneda: MonedaTipo | None = None
    notas: str | None = None


class CanjeUpdate(BaseModel):
    fecha_cierre: datetime | None = None
    estado: CanjeEstado | None = None
    etapa: CanjeEtapa | None = None
    corredor_solicitante_nombre: str | None = None
    corredor_solicitante_email: str | None = None
    corredor_propietario_nombre: str | None = None
    corredor_propietario_email: str | None = None
    tipo_operacion: OperacionTipo | None = None
    tipo_inmueble: str | None = None
    comuna: str | None = None
    direccion: str | None = None
    valor_prop: float | None = None
    moneda_valor: MonedaTipo | None = None
    link_propiedad: str | None = None
    valor_negocio: float | None = None
    valor_negocio_moneda: MonedaTipo | None = None
    comision_dataprop: float | None = None
    comision_dataprop_moneda: MonedaTipo | None = None
    notas: str | None = None


# Va antes de "/{canje_id}": FastAPI resuelve por orden de registro, y si esta
# ruta quedara despues, "bandeja" se intentaria parsear como un id.
@router.get("/bandeja", response_model=Bandeja)
def bandeja(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    """Que canje hay que tocar hoy, ordenado por urgencia (sprint 20)."""
    return obtener_bandeja(db)


@router.get("/reportes/activos", response_model=ListadoCanjesActivos)
def reporte_activos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Los canjes abiertos, con su estado de gestión y su historial completo.

    Va antes de `/{canje_id}` en el archivo: FastAPI resuelve por orden y
    `activos` calzaría con el parámetro de ruta.
    """
    return obtener_listado(db)


@router.get("/reportes/plata", response_model=PlataCanjes)
def reporte_plata(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """La comisión de Dataprop y los plazos del Centro de Canje.

    **Es plata de Dataprop, no de ViveProp**, y la pantalla la rotula como tal.
    """
    try:
        return obtener_plata_canjes(db)
    except UFNoDisponible as exc:
        # Sin UF de hoy no se puede valorizar nada, y decirlo es mejor que devolver
        # ceros que parecen datos.
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc))


@router.get("/reportes/resumen", response_model=ResumenCanjes)
def reportes_resumen(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    return obtener_resumen_canjes(db)


# Las dos van antes de "/{canje_id}", por el mismo motivo que "/bandeja".
@router.get("/plantilla/estructura", response_model=EstructuraArchivo)
def estructura_del_archivo(usuario: Usuario = Depends(require_role(RolUsuario.operaciones))):
    """Qué columnas espera el export de Dataprop, para verlo antes de subir nada."""
    return estructura_importacion()


@router.get("/plantilla")
def descargar_plantilla(usuario: Usuario = Depends(require_role(RolUsuario.operaciones))):
    """El .xlsx vacío con los 16 encabezados exactos.

    No es para llenarlo a mano --el archivo sale de Dataprop-- sino para comparar
    encabezados cuando la carga falla y no se entiende por qué.
    """
    return Response(
        content=generar_plantilla(),
        media_type=XLSX,
        headers={"Content-Disposition": 'attachment; filename="plantilla-canjes.xlsx"'},
    )


@router.get("", response_model=list[CanjeOut])
def listar(
    estado: CanjeEstado | None = None,
    etapa: CanjeEtapa | None = None,
    comuna: str | None = None,
    # **Cada rol filtra su propia columna.** Un corredor puede ser solicitante en
    # un canje y propietario en otro --Jorge Román pide el 360 y Databrokers tiene
    # el 361-- asi que un filtro unico sobre "el corredor" mezclaria dos preguntas
    # distintas: con quien estoy trabajando y de quien es la propiedad.
    solicitante: str | None = None,
    propietario: str | None = None,
    numero: str | None = Query(
        None,
        description=(
            "N° de solicitud, el mismo ID_CANJE de Dataprop. Busca por prefijo: "
            "«36» trae los 36x y «364» trae ese. Acepta que venga con «#»."
        ),
    ),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    query = select(Canje)
    if estado is not None:
        query = query.where(Canje.estado == estado)
    if etapa is not None:
        query = query.where(Canje.etapa == etapa)
    if comuna:
        query = query.where(Canje.comuna.ilike(f"%{comuna}%"))
    if solicitante:
        query = query.where(Canje.corredor_solicitante_nombre.ilike(f"%{solicitante}%"))
    if propietario:
        query = query.where(Canje.corredor_propietario_nombre.ilike(f"%{propietario}%"))
    if numero:
        # **Por prefijo y no por igualdad.** Teclear un número incompleto no puede
        # devolver una lista vacía: mientras se escribe «364», el «3» y el «36»
        # tienen que mostrar algo o la pantalla parpadea en vacío y se lee como
        # que el canje no existe.
        #
        # Se filtra la entrada a dígitos en vez de rechazarla: la app muestra las
        # referencias como «#364» --así salen en los reportes-- así que pegar eso
        # tiene que funcionar. Si no queda ningún dígito, el filtro no aplica.
        digitos = "".join(c for c in numero if c.isdigit())
        if digitos:
            # `cast` porque `id` es `bigint`: sin él no hay `like`. Con 303 filas
            # el índice que se pierde no cambia nada medible.
            query = query.where(cast(Canje.id, String).like(f"{digitos}%"))
    query = query.order_by(Canje.fecha_solicitud.desc())
    return db.scalars(query).all()


class OpcionesDeFiltro(BaseModel):
    """Los valores que existen, para que los filtros sugieran en vez de adivinar.

    Los corredores van **separados por rol** porque los filtros son dos: ofrecer
    en «solicitante» a alguien que solo aparece como propietario daria una
    sugerencia que no devuelve nada.

    Las tres listas viajan juntas en una sola respuesta. Son listas cortas del
    mismo origen y se piden todas al abrir la pantalla: tres endpoints serian tres
    viajes para el mismo momento.
    """

    solicitantes: list[str]
    propietarios: list[str]
    comunas: list[str]


@router.get("/filtros", response_model=OpcionesDeFiltro)
def opciones_de_filtro(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    """Los valores distintos de cada filtro, ordenados.

    **Las listas son el universo completo y no dependen de los filtros
    aplicados.** Si salieran del listado ya filtrado, elegir un corredor haria
    desaparecer al resto de las opciones y el filtro se volveria un callejon: para
    cambiar de corredor habria que limpiar primero.

    Son 106 solicitantes, 134 propietarios y 43 comunas en produccion, asi que se
    manda todo y el campo filtra en el navegador mientras se escribe. Paginar o
    consultar por tecla seria resolver un problema que no existe.
    """
    def _distintos(columna):
        return [
            n for (n,) in db.execute(
                select(columna).where(columna.is_not(None), columna != "")
                .distinct().order_by(columna)
            ).all()
        ]

    return OpcionesDeFiltro(
        solicitantes=_distintos(Canje.corredor_solicitante_nombre),
        propietarios=_distintos(Canje.corredor_propietario_nombre),
        comunas=_distintos(Canje.comuna),
    )


@router.get("/{canje_id}", response_model=CanjeOut)
def obtener(canje_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    canje = db.get(Canje, canje_id)
    if canje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canje no encontrado")
    return canje


@router.post("", response_model=CanjeOut, status_code=status.HTTP_201_CREATED)
def crear(payload: CanjeCreate, db: Session = Depends(get_db), usuario: Usuario = Depends(require_role(RolUsuario.operaciones))):
    if db.get(Canje, payload.id) is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un canje con ese ID")

    canje = Canje(**payload.model_dump(), gestionado_en_app=True)
    db.add(canje)
    db.commit()
    db.refresh(canje)
    return canje


@router.patch("/{canje_id}", response_model=CanjeOut)
def actualizar(
    canje_id: int,
    payload: CanjeUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    canje = db.get(Canje, canje_id)
    if canje is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canje no encontrado")

    cambios = payload.model_dump(exclude_unset=True)

    # Se lee antes de asignar: después el objeto ya tiene la etapa nueva.
    etapa_anterior = canje.etapa
    for campo, valor in cambios.items():
        setattr(canje, campo, valor)
    canje.gestionado_en_app = True

    # Un cambio de etapa desde la ficha deja rastro en la bitácora. Sin esto, la
    # ficha y la línea de tiempo podían decir cosas distintas, y el cambio no
    # tenía fecha ni autor.
    if "etapa" in cambios and canje.etapa != etapa_anterior:
        registrar_cambio_de_etapa(db, canje, etapa_anterior, canje.etapa, usuario.id)

    db.commit()
    db.refresh(canje)
    return canje


@router.post("/importar", response_model=ImportarCanjesResumen)
async def importar(
    archivo: UploadFile,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    if not archivo.filename or not archivo.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El archivo debe ser un .xlsx")

    contenido = await archivo.read()
    try:
        return importar_canjes(db, contenido)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


class MovimientoOut(BaseModel):
    id: int
    tipo_movimiento: str
    tipo_nombre: str
    etapa_resultante: str | None
    fecha: datetime
    autor_nombre: str | None
    comentario: str | None
    # Cuándo se prometió volver a mirar el canje. El del movimiento más reciente
    # es el que manda en «Qué me toca hoy».
    proximo_seguimiento: date | None
    # Sobre cuál de los dos corredores se hizo la gestión. Nulo en los migrados.
    corredor: str | None


class MovimientoCreate(BaseModel):
    tipo_movimiento: str
    comentario: str | None = None
    fecha: datetime | None = None
    # Opcional. Sin él, el servicio agenda dos días corridos hacia adelante,
    # corridos al siguiente hábil si caen fin de semana.
    proximo_seguimiento: date | None = None
    # Dónde queda el canje. Opcional en la API para no romper a quien llame sin
    # ella --se cae al `etapa_resultante` del tipo, como antes--, pero la pantalla
    # la pide siempre: el tipo dice qué se hizo y la etapa dónde quedó.
    etapa: CanjeEtapa | None = None
    # Sobre cuál de los dos corredores se hizo la gestión. Optativo a propósito:
    # hay movimientos que no son sobre ninguno --una cancelación, un comentario
    # general-- y forzarlo obligaría a poner un dato falso en esos casos.
    corredor: CorredorCanje | None = None


def _a_movimiento_out(db: Session, m: Movimiento) -> MovimientoOut:
    tipo = db.get(TipoMovimiento, m.tipo_movimiento)
    autor = db.get(Usuario, m.autor_id) if m.autor_id else None
    return MovimientoOut(
        id=m.id,
        tipo_movimiento=m.tipo_movimiento,
        tipo_nombre=tipo.nombre if tipo else m.tipo_movimiento,
        etapa_resultante=m.etapa_resultante,
        fecha=m.fecha,
        autor_nombre=autor.nombre if autor else None,
        comentario=m.comentario,
        proximo_seguimiento=m.proximo_seguimiento,
        corredor=m.corredor,
    )


@router.get("/{canje_id}/movimientos", response_model=list[MovimientoOut])
def listar_movimientos(canje_id: int, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    if db.get(Canje, canje_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Canje no encontrado")
    movimientos = db.scalars(
        select(Movimiento)
        .where(Movimiento.entity_type == EntityType.canje, Movimiento.entity_id == canje_id)
        .order_by(Movimiento.fecha.desc())
    ).all()
    return [_a_movimiento_out(db, m) for m in movimientos]


@router.post("/{canje_id}/movimientos", response_model=MovimientoOut, status_code=status.HTTP_201_CREATED)
def crear_movimiento(
    canje_id: int,
    payload: MovimientoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    try:
        movimiento = crear_movimiento_canje(
            db,
            canje_id,
            payload.tipo_movimiento,
            usuario.id,
            payload.comentario,
            payload.fecha,
            payload.proximo_seguimiento,
            payload.etapa,
            payload.corredor,
        )
    except MovimientoError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return _a_movimiento_out(db, movimiento)


@router.delete(
    "/{canje_id}/movimientos/{movimiento_id}", status_code=status.HTTP_204_NO_CONTENT
)
def eliminar_movimiento(
    canje_id: int,
    movimiento_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    """Borra un movimiento mal registrado y recalcula lo que dependía de él.

    Lo puede hacer quien los registra: corregir un tipeo propio no debería
    necesitar a otra persona. La etapa se vuelve a derivar de lo que queda y, si
    el borrado era la cancelación, el canje vuelve a activo.
    """
    try:
        eliminar_movimiento_canje(db, canje_id, movimiento_id)
    except MovimientoError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


class AvanceCanjeIn(BaseModel):
    """Lo mismo que en negocios: estado, monto y fecha, los tres juntos."""

    tipo: str
    estado_id: int
    monto: Decimal | None = None
    fecha: date | None = None


def _canje_de(db: Session, canje_id: int) -> Canje:
    canje = db.get(Canje, canje_id)
    if canje is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Canje no encontrado")
    return canje


@router.get("/{canje_id}/obligaciones", response_model=list[ObligacionOut])
def listar_obligaciones(
    canje_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    """Las dos facturas del canje, una por corredor.

    **Es plata de Dataprop.** ViveProp opera el Centro de Canje a nombre de
    Dataprop y no percibe nada de él; acá se registra el seguimiento, no un ingreso
    propio.
    """
    return obligaciones_del_canje(db, _canje_de(db, canje_id))


@router.post("/{canje_id}/obligaciones", response_model=list[ObligacionOut])
def registrar_obligacion(
    canje_id: int,
    payload: AvanceCanjeIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.operaciones)),
):
    canje = _canje_de(db, canje_id)
    try:
        registrar_avance(
            db,
            canje=canje,
            tipo=payload.tipo,
            estado_id=payload.estado_id,
            monto=payload.monto,
            fecha=payload.fecha,
            autor_id=usuario.id,
        )
        db.commit()
    except ObligacionError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return obligaciones_del_canje(db, canje)


@router.delete("/{canje_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    canje_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_role(RolUsuario.admin)),
):
    """Borra un canje con sus movimientos y sus obligaciones. **Irreversible.**

    **Solo admin**, y es la única operación de la app que destruye datos sin
    dejar rastro: cancelar deja el canje con su línea de tiempo, esto lo saca de
    la base. El rol más alto es la guarda barata para algo que no tiene deshacer.

    **No tiene botón en la pantalla, a propósito.** Existe para que el script de
    limpieza pueda correr contra un despliegue con una cookie de sesión en vez de
    con el string de conexión de la base --una cookie vence, se revoca cerrando
    sesión y no da más permisos que los de su usuario, el mismo criterio de
    `limpiar_canjes.py`--. Un botón de borrado definitivo al lado del de editar es
    un accidente esperando (`D-096`).
    """
    canje = db.get(Canje, canje_id)
    if canje is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Canje no encontrado")
    borrar_canje(db, canje)
    db.commit()
