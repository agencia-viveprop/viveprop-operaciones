export type ModeloNegocio = 'MERCADO_PRIMARIO' | 'SECUNDARIO_CONCENTRADORES' | 'SECUNDARIO_AGENCIA'
export type EstadoNegocio = 'ACTIVO' | 'CERRADO' | 'PERDIDO' | 'DESISTIDO'
export type MonedaTipo = 'CLP' | 'UF' | 'OTRA'

export type Propiedad = {
  id: number
  direccion: string
  unidad: string | null
  comuna: string
  tipo_propiedad_id: number | null
  estado_propiedad_id: number | null
}

export type Hito = {
  id: number
  nombre: string | null
  fecha_inicio: string
  fecha_cierre: string | null
  estado: EstadoNegocio
  etapa: string | null

  valor_negocio: number | null
  moneda: MonedaTipo | null
  fecha_valorizacion: string | null
  uf_snapshot: number | null
  valor_clp_calculado: number | null
  valor_clp_manual: number | null
  motivo_valor_manual: string | null
  /** Sobre esto se calculó la comisión: el manual si existe, si no el calculado. */
  base_comision: number | null

  comision_total: number | null
  comision_broker: number | null
  rebate_concentrador: number | null
  comision_vp_bruta: number | null
  comision_equipo: number | null
  comision_tercero: number | null
  comision_real_vp: number | null

  nombre_tercero: string | null
  motivo_perdida_id: number | null
  motivo_perdida_detalle: string | null
}

export type Movimiento = {
  id: number
  tipo_movimiento: string
  tipo_nombre: string
  etapa_resultante: string | null
  fecha: string
  autor_nombre: string | null
  comentario: string | null
}

export type TipoMovimientoNegocio = {
  codigo: string
  nombre: string
  etapa_resultante: string | null
  orden: number | null
  responsable_default: string | null
}

export type Negocio = {
  id: number
  codigo: string
  modelo: ModeloNegocio
  /** El pipeline E1-E7 es del negocio, no de sus hitos (D-027). */
  etapa: string | null
  propiedad: Propiedad
  alianza_id: number | null
  tipo_operacion_id: number | null
  vendedor_arrendador: string | null
  comprador_arrendatario: string | null
  corredor_agente: string | null
  notas: string | null
  observaciones: string | null
  creado_en: string
  hitos: Hito[]
}

/** Fila del listado: sin los hitos, con sus montos ya sumados. */
export type NegocioResumen = {
  id: number
  codigo: string
  modelo: ModeloNegocio
  etapa: string | null
  direccion: string
  unidad: string | null
  comuna: string
  alianza_id: number | null
  cantidad_hitos: number
  estados: EstadoNegocio[]
  comision_total: number
  comision_real_vp: number
}

export type FiltrosNegocios = {
  estado?: string
  modelo?: string
  alianza_id?: string
  codigo?: string
}

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const detalle = body.detail
    // Los errores de validación de FastAPI vienen como lista de objetos.
    if (Array.isArray(detalle)) {
      throw new Error(detalle.map((d: { msg?: string }) => d.msg ?? '').join(' · '))
    }
    throw new Error(detalle ?? `Error ${res.status}`)
  }
  return res.json()
}

function json(url: string, method: string, payload: unknown) {
  return fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  }).then(parseOrThrow)
}

export function listarNegocios(filtros: FiltrosNegocios = {}): Promise<NegocioResumen[]> {
  const params = new URLSearchParams()
  Object.entries(filtros).forEach(([k, v]) => v && params.set(k, v))
  const qs = params.toString()
  return fetch(`/api/negocios${qs ? `?${qs}` : ''}`, { credentials: 'include' }).then(parseOrThrow)
}

export function obtenerNegocio(id: number): Promise<Negocio> {
  return fetch(`/api/negocios/${id}`, { credentials: 'include' }).then(parseOrThrow)
}

export function crearNegocio(payload: Record<string, unknown>): Promise<Negocio> {
  return json('/api/negocios', 'POST', payload)
}

export function actualizarNegocio(id: number, payload: Record<string, unknown>): Promise<Negocio> {
  return json(`/api/negocios/${id}`, 'PATCH', payload)
}

export function crearHito(negocioId: number, payload: Record<string, unknown>): Promise<Hito> {
  return json(`/api/negocios/${negocioId}/hitos`, 'POST', payload)
}

export function actualizarHito(
  negocioId: number,
  hitoId: number,
  payload: Record<string, unknown>,
): Promise<Hito> {
  return json(`/api/negocios/${negocioId}/hitos/${hitoId}`, 'PATCH', payload)
}

export function buscarPropiedades(q: string): Promise<Propiedad[]> {
  return fetch(`/api/negocios/propiedades?q=${encodeURIComponent(q)}`, {
    credentials: 'include',
  }).then(parseOrThrow)
}

export function listarTiposMovimiento(): Promise<TipoMovimientoNegocio[]> {
  return fetch('/api/negocios/tipos-movimiento', { credentials: 'include' }).then(parseOrThrow)
}

export function listarMovimientos(negocioId: number): Promise<Movimiento[]> {
  return fetch(`/api/negocios/${negocioId}/movimientos`, { credentials: 'include' }).then(parseOrThrow)
}

export function crearMovimiento(
  negocioId: number,
  payload: { tipo_movimiento: string; comentario?: string | null },
): Promise<Movimiento> {
  return json(`/api/negocios/${negocioId}/movimientos`, 'POST', payload)
}

// ------------------------------------------------------------------ reportería

export type Bucket = {
  hitos: number
  negocios: number
  valor_base: number
  comision_total: number
  comision_real_vp: number
  rebate_concentrador: number
}

export type Corte = {
  etiqueta: string
  hitos: number
  comision_total: number
  comision_real_vp: number
}

/**
 * Los tres buckets vienen separados a propósito y no hay un campo `total`:
 * sumar ganado, pipeline y perdido da un número que no significa nada (D-006).
 */
export type ResumenNegocios = {
  ganado: Bucket
  pipeline: Bucket
  potencial_perdido: Bucket
  ganado_por_mes: Corte[]
  ganado_por_alianza: Corte[]
  ganado_por_modelo: Corte[]
  pipeline_por_etapa: Corte[]
  hitos_sin_valorizar: number
}

export function obtenerResumenNegocios(): Promise<ResumenNegocios> {
  return fetch('/api/negocios/reportes/resumen', { credentials: 'include' }).then(parseOrThrow)
}

export type ResumenCargaNegocios = {
  negocios_nuevos: number
  negocios_actualizados: number
  hitos_nuevos: number
  hitos_actualizados: number
  errores: string[]
}

/** Baja la plantilla y la guarda. El navegador de la SPA no puede seguir un
 *  link directo a un endpoint con cookie, así que se pide y se crea el blob. */
export async function descargarPlantillaNegocios(): Promise<void> {
  const res = await fetch('/api/negocios/plantilla', { credentials: 'include' })
  if (!res.ok) throw new Error(`Error ${res.status}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'plantilla-negocios.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

export function importarNegocios(archivo: File): Promise<ResumenCargaNegocios> {
  const formData = new FormData()
  formData.append('archivo', archivo)
  return fetch('/api/negocios/importar', {
    method: 'POST',
    credentials: 'include',
    body: formData,
  }).then(parseOrThrow)
}

export type CorteMes = {
  etiqueta: string
  negocios: number
  comision_real_vp: string
}

export type NegociosPorMes = {
  meses: CorteMes[]
  total_negocios: number
  modelo: string | null
  tipo_operacion: string | null
}

/** Cuántos negocios arrancaron cada mes. Mide lo que entró, no lo que se cobró. */
export function obtenerNegociosPorMes(
  filtros: { modelo?: string | null; tipo_operacion?: string | null } = {},
): Promise<NegociosPorMes> {
  const params = new URLSearchParams()
  Object.entries(filtros).forEach(([k, v]) => v && params.set(k, v))
  const qs = params.toString()
  return fetch(`/api/negocios/reportes/por-mes${qs ? `?${qs}` : ''}`, {
    credentials: 'include',
  }).then(parseOrThrow)
}
