/**
 * La estructura que espera cada archivo de carga masiva.
 *
 * Los dos dominios devuelven la misma forma aunque sus columnas no se parezcan
 * --16 obligatorias que salen de una query de Dataprop contra 32 de una plantilla
 * que se llena a mano--, y eso es lo que deja que una sola pantalla las muestre.
 */

export type ColumnaArchivo = {
  nombre: string
  obligatoria: boolean
  ayuda: string
}

export type GrupoColumnas = {
  nombre: string
  columnas: ColumnaArchivo[]
}

export type ValoresDeColumna = {
  columna: string
  valores: string[]
  nota: string | null
}

export type EstructuraArchivo = {
  titulo: string
  origen: string
  fila: string
  grupos: GrupoColumnas[]
  valores: ValoresDeColumna[]
  notas: string[]
}

async function pedir(url: string): Promise<EstructuraArchivo> {
  const res = await fetch(url, { credentials: 'include' })
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => ({}))
    throw new Error(cuerpo.detail ?? `Error ${res.status}`)
  }
  return res.json()
}

export function obtenerEstructuraCanjes(): Promise<EstructuraArchivo> {
  return pedir('/api/canjes/plantilla/estructura')
}

export function obtenerEstructuraNegocios(): Promise<EstructuraArchivo> {
  return pedir('/api/negocios/plantilla/estructura')
}

export function obtenerEstructuraHistorial(): Promise<EstructuraArchivo> {
  return pedir('/api/negocios/plantilla-historial/estructura')
}
