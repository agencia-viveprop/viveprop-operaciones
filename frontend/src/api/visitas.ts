export type Visita = {
  id: number
  propiedad: string
  direccion: string | null
  tipo: string | null
  mercado: string | null
  cliente: string | null
  rut: string | null
  objetivo_compra: string | null
  fecha_solicitada: string | null
  etapa: string | null
  solicitada_el: string | null
}

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Error ${res.status}`)
  }
  return res.json()
}

export const CLAVE_VISITAS = ['visitas']

export function listarVisitas(): Promise<Visita[]> {
  return fetch('/api/visitas', { credentials: 'include' }).then(parseOrThrow)
}

export type ResumenCargaVisitas = {
  nuevas: number
  errores: string[]
}

export function importarVisitas(archivo: File): Promise<ResumenCargaVisitas> {
  const formData = new FormData()
  formData.append('archivo', archivo)
  return fetch('/api/visitas/importar', {
    method: 'POST',
    credentials: 'include',
    body: formData,
  }).then(parseOrThrow)
}

/** Baja la plantilla y la guarda. El navegador de la SPA no puede seguir un
 *  link directo a un endpoint con cookie, así que se pide y se crea el blob. */
export async function descargarPlantillaVisitas(): Promise<void> {
  const res = await fetch('/api/visitas/plantilla', { credentials: 'include' })
  if (!res.ok) throw new Error(`Error ${res.status}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'plantilla-visitas.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

export async function eliminarVisita(id: number): Promise<void> {
  const res = await fetch(`/api/visitas/${id}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Error ${res.status}`)
  }
}
