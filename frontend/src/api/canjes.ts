export type CanjeEstado = 'ACTIVO' | 'CANCELADO'
export type CanjeEtapa = 'SIN_ETAPA' | 'EN_REVISION' | 'PROCESO_DE_ACUERDO' | 'EN_OFERTA' | 'EN_NEGOCIO' | 'CERRADO'
export type OperacionTipo = 'VENTA' | 'ARRIENDO' | 'OTRO'
export type MonedaTipo = 'CLP' | 'UF' | 'OTRA'

export type Canje = {
  id: number
  fecha_solicitud: string
  fecha_cierre: string | null
  estado: CanjeEstado
  etapa: CanjeEtapa
  corredor_solicitante_nombre: string | null
  corredor_solicitante_email: string | null
  corredor_propietario_nombre: string | null
  corredor_propietario_email: string | null
  tipo_operacion: OperacionTipo | null
  tipo_inmueble: string | null
  comuna: string | null
  direccion: string | null
  valor_prop: number | null
  moneda_valor: MonedaTipo | null
  link_propiedad: string | null
  valor_negocio: number | null
  valor_negocio_moneda: MonedaTipo | null
  comision_dbrokers: number | null
  comision_dbrokers_moneda: MonedaTipo | null
  notas: string | null
  gestionado_en_app: boolean
}

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Error ${res.status}`)
  }
  return res.json()
}

export function listarCanjes(filtros: { estado?: string; etapa?: string; comuna?: string } = {}): Promise<Canje[]> {
  const params = new URLSearchParams()
  Object.entries(filtros).forEach(([k, v]) => v && params.set(k, v))
  const qs = params.toString()
  return fetch(`/api/canjes${qs ? `?${qs}` : ''}`, { credentials: 'include' }).then(parseOrThrow)
}

export function crearCanje(payload: Record<string, unknown>): Promise<Canje> {
  return fetch('/api/canjes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  }).then(parseOrThrow)
}

export function actualizarCanje(id: number, payload: Record<string, unknown>): Promise<Canje> {
  return fetch(`/api/canjes/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  }).then(parseOrThrow)
}

export type ImportarResumen = {
  nuevas: number
  actualizadas: number
  ignoradas: number
  errores: string[]
}

/**
 * El .xlsx vacío con los 16 encabezados exactos.
 *
 * No es para llenarlo a mano --el archivo sale de la query contra Dataprop-- sino
 * para comparar encabezados cuando la carga falla y no se entiende por qué.
 */
export async function descargarPlantillaCanjes(): Promise<void> {
  const res = await fetch('/api/canjes/plantilla', { credentials: 'include' })
  if (!res.ok) throw new Error(`Error ${res.status}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'plantilla-canjes.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

export function importarCanjes(archivo: File): Promise<ImportarResumen> {
  const formData = new FormData()
  formData.append('archivo', archivo)
  return fetch('/api/canjes/importar', {
    method: 'POST',
    credentials: 'include',
    body: formData,
  }).then(parseOrThrow)
}

// -------------------------------------------------------------- bandeja diaria

/**
 * `sin_gestion` es un nivel aparte y no "crítico": nunca tocado y abandonado
 * tres días son problemas distintos. Ver el servicio del sprint 20.
 */
export type NivelSemaforo = 'sin_gestion' | 'critico' | 'advertencia' | 'al_dia'

export type FilaBandeja = {
  canje_id: number
  fecha_solicitud: string
  etapa: CanjeEtapa
  corredor_solicitante_nombre: string | null
  corredor_propietario_nombre: string | null
  comuna: string | null
  direccion: string | null
  nivel: NivelSemaforo
  horas_sin_gestion: number | null
  ultimo_movimiento: string | null
  ultimo_movimiento_nombre: string | null
}

export type Bandeja = {
  resumen: { sin_gestion: number; critico: number; advertencia: number; al_dia: number }
  filas: FilaBandeja[]
  umbral_critico_horas: number
  umbral_advertencia_horas: number
}

export function obtenerBandeja(): Promise<Bandeja> {
  return fetch('/api/canjes/bandeja', { credentials: 'include' }).then(parseOrThrow)
}
