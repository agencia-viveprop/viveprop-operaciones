export type ItemCatalogo = {
  /** Nulo en los grupos que salen de un enum (modelo, estado): no son filas de tabla. */
  id: number | null
  codigo: string
  nombre: string
  orden: number | null
  metadatos: Record<string, string> | null
}

export type EtapaCatalogo = {
  codigo: string
  nombre: string
  responsable: string
  orden: number
}

export type Catalogos = {
  alianzas: ItemCatalogo[]
  estados_facturacion: ItemCatalogo[]
  tipos_propiedad: ItemCatalogo[]
  tipos_operacion: ItemCatalogo[]
  estados_propiedad: ItemCatalogo[]
  motivos_perdida: ItemCatalogo[]
  etapas: EtapaCatalogo[]
  modelos_negocio: ItemCatalogo[]
  estados_negocio: ItemCatalogo[]
}

/** Los nueve grupos en una llamada: ningún formulario orquesta cinco peticiones. */
export function obtenerCatalogos(): Promise<Catalogos> {
  return fetch('/api/catalogos', { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error(`Error ${res.status}`)
    return res.json()
  })
}
