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
