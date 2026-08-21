from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models.catalogo import (
    Catalogo,
    Etapa,
    EstadoNegocio,
    ModeloNegocio,
    TipoCatalogo,
)
from app.models.usuario import Usuario

router = APIRouter(prefix="/catalogos", tags=["catalogos"])


class ItemCatalogo(BaseModel):
    codigo: str
    nombre: str
    orden: int | None = None
    metadatos: dict | None = None


class EtapaOut(BaseModel):
    codigo: str
    nombre: str
    responsable: str
    orden: int


class CatalogosOut(BaseModel):
    """Todo lo que el front necesita para pintar desplegables, en una llamada.

    Los enums viajan junto a los catalogos editables aunque no vivan en la misma
    tabla: al front le da igual de donde salen, y una sola llamada evita que cada
    formulario tenga que orquestar cinco.
    """

    alianzas: list[ItemCatalogo]
    estados_facturacion: list[ItemCatalogo]
    tipos_propiedad: list[ItemCatalogo]
    tipos_operacion: list[ItemCatalogo]
    estados_propiedad: list[ItemCatalogo]
    motivos_perdida: list[ItemCatalogo]
    etapas: list[EtapaOut]
    modelos_negocio: list[ItemCatalogo]
    estados_negocio: list[ItemCatalogo]


NOMBRES_MODELO = {
    ModeloNegocio.MERCADO_PRIMARIO: "Mercado Primario",
    ModeloNegocio.SECUNDARIO_CONCENTRADORES: "Secundario Concentradores",
    ModeloNegocio.SECUNDARIO_AGENCIA: "Secundario Agencia",
}

NOMBRES_ESTADO = {
    EstadoNegocio.ACTIVO: "Activo",
    EstadoNegocio.CERRADO: "Cerrado",
    EstadoNegocio.PERDIDO: "Perdido",
    EstadoNegocio.DESISTIDO: "Desistido",
}


def _items(db: Session, tipo: TipoCatalogo) -> list[ItemCatalogo]:
    filas = db.scalars(
        select(Catalogo)
        .where(Catalogo.tipo == tipo.value, Catalogo.activo.is_(True))
        .order_by(Catalogo.orden, Catalogo.nombre)
    ).all()
    return [
        ItemCatalogo(codigo=f.codigo, nombre=f.nombre, orden=f.orden, metadatos=f.metadatos)
        for f in filas
    ]


def _desde_enum(nombres: dict) -> list[ItemCatalogo]:
    return [
        ItemCatalogo(codigo=miembro.value, nombre=nombre, orden=i + 1)
        for i, (miembro, nombre) in enumerate(nombres.items())
    ]


@router.get("", response_model=CatalogosOut)
def listar_todo(db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    etapas = db.scalars(
        select(Etapa).where(Etapa.activo.is_(True)).order_by(Etapa.orden)
    ).all()

    return CatalogosOut(
        alianzas=_items(db, TipoCatalogo.ALIANZA),
        estados_facturacion=_items(db, TipoCatalogo.ESTADO_FACTURACION),
        tipos_propiedad=_items(db, TipoCatalogo.TIPO_PROPIEDAD),
        tipos_operacion=_items(db, TipoCatalogo.TIPO_OPERACION),
        estados_propiedad=_items(db, TipoCatalogo.ESTADO_PROPIEDAD),
        motivos_perdida=_items(db, TipoCatalogo.MOTIVO_PERDIDA),
        etapas=[
            EtapaOut(codigo=e.codigo, nombre=e.nombre, responsable=e.responsable, orden=e.orden)
            for e in etapas
        ],
        modelos_negocio=_desde_enum(NOMBRES_MODELO),
        estados_negocio=_desde_enum(NOMBRES_ESTADO),
    )


@router.get("/{tipo}", response_model=list[ItemCatalogo])
def listar_tipo(
    tipo: str, db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_user)
):
    try:
        tipo_valido = TipoCatalogo(tipo)
    except ValueError:
        validos = ", ".join(t.value for t in TipoCatalogo)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de catálogo desconocido: '{tipo}'. Los válidos son: {validos}.",
        )
    return _items(db, tipo_valido)
