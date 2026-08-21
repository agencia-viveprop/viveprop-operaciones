/** Qué tan lejos llega la serie de UF y si hay que hacer algo. */
export type EstadoSerieUF = {
  primera: string | null
  ultima: string | null
  filas: number
  dias_de_colchon: number | null
  /** `vacia` y `vencida` bloquean valorizar con fecha de hoy; `aviso` es un recordatorio. */
  nivel: 'vacia' | 'vencida' | 'aviso' | 'ok'
  mensaje: string
}

export type ResumenCargaUF = {
  nuevas: number
  actualizadas: number
  sin_cambio: number
  errores: string[]
}

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Error ${res.status}`)
  }
  return res.json()
}

export function obtenerEstadoUF(): Promise<EstadoSerieUF> {
  return fetch('/api/uf/estado', { credentials: 'include' }).then(parseOrThrow)
}

/** Descarga la plantilla con las fechas que faltan ya escritas. */
export async function descargarPlantillaUF(): Promise<void> {
  const res = await fetch('/api/uf/plantilla', { credentials: 'include' })
  if (!res.ok) throw new Error(`Error ${res.status}`)

  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = res.headers.get('content-disposition')?.match(/filename="(.+?)"/)?.[1] ?? 'uf.xlsx'
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  URL.revokeObjectURL(url)
}

export function importarUF(archivo: File): Promise<ResumenCargaUF> {
  const datos = new FormData()
  datos.append('archivo', archivo)
  return fetch('/api/uf/importar', {
    method: 'POST',
    credentials: 'include',
    body: datos,
  }).then(parseOrThrow)
}
