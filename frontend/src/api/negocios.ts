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

  /** Las tasas son la **entrada** del cálculo, no el resultado. El formulario de
   *  edición las necesita: sin ellas, abrir un hito y guardar las mandaría en
   *  nulo y borraría la base sobre la que se calculó la comisión. */
  pct_lado_vendedor: string | null
  pct_lado_comprador: string | null
  pct_rebate_concentrador: string | null
  pct_broker_vendedor: string | null
  pct_broker_comprador: string | null
  pct_vp_vendedor: string | null
  pct_vp_comprador: string | null
  pct_equipo: string | null
  pct_tercero: string | null

  nombre_tercero: string | null
  motivo_perdida_id: number | null
  motivo_perdida_detalle: string | null
}

export type Movimiento = {
  id: number
  tipo_movimiento: string
  tipo_nombre: string
  etapa_resultante: string | null
  /** Cuándo se hizo la actividad. La elige quien registra. */
  fecha: string
  autor_nombre: string | null
  comentario: string | null
  /** Cuándo se comprometió la próxima acción. Nunca nulo en los que se registran
   *  desde la app: si no se indica, se agenda a 3 días de la fecha del avance. */
  proximo_seguimiento: string | null
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
/** Las cuatro duraciones. **Nulo significa "no se sabe", no cero**: los 7
 *  históricos tienen la misma fecha de inicio y de cierre porque el Excel traía
 *  una sola, así que su duración es desconocida. */
export type Duraciones = {
  dias_abierto: number | null
  dias_sin_gestion: number | null
  dias_en_etapa: number | null
  dias_hasta_el_cierre: number | null
}

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
  /** La comisión real ViveProp partida por bucket. Nunca se suman entre sí: la
   *  primera es plata que entró, la segunda es plata que podría entrar y la
   *  tercera es plata que no entró. Antes venían en un solo total que las
   *  mezclaba, y el filtro por estado no lo arreglaba porque decide qué
   *  negocios se ven, no qué plata se suma. */
  comision_ganada: number
  comision_pipeline: number
  comision_no_concretada: number
  fecha_inicio: string | null
  duraciones: Duraciones
}

/** Los dos primeros salen de un compromiso registrado; los otros del semáforo de
 *  días sin gestión. El compromiso manda cuando existe. */
export type NivelNegocio =
  | 'vencido'
  | 'para_hoy'
  | 'sin_gestion'
  | 'critico'
  | 'advertencia'
  | 'al_dia'

export type FilaBandejaNegocio = {
  negocio_id: number
  codigo: string
  etapa: string | null
  modelo: ModeloNegocio
  direccion: string | null
  comuna: string | null
  fecha_inicio: string | null
  comision_real_vp: string | null
  nivel: NivelNegocio
  duraciones: Duraciones
  ultimo_movimiento: string | null
  ultimo_movimiento_nombre: string | null
  /** El compromiso vigente: el último que exista, no el del último movimiento. */
  proximo_seguimiento: string | null
  /** Positivo si venció, cero si es para hoy, nulo si nadie agendó nada. */
  dias_de_atraso: number | null
}

export type BandejaNegocios = {
  /** Los niveles más `agendados`, que **no están en `filas`**: la pantalla se
   *  llama «qué me toca hoy» y esos negocios no tocan hoy. Se cuentan para que no
   *  parezca que desaparecieron. */
  resumen: Record<NivelNegocio, number> & { agendados: number }
  filas: FilaBandejaNegocio[]
  umbral_critico_dias: number
  umbral_advertencia_dias: number
}

export function obtenerBandejaNegocios(): Promise<BandejaNegocios> {
  return fetch('/api/negocios/bandeja', { credentials: 'include' }).then(parseOrThrow)
}

export type FiltrosNegocios = {
  estado?: string
  modelo?: string
  alianza_id?: string
  codigo?: string
}

/**
 * Guardar una liquidación cerrada le movería la comisión.
 *
 * La API responde 409 con los dos montos en vez de guardar. Lleva su propia clase
 * porque quien la reciba no tiene que mostrar un error: tiene que preguntar, y
 * para eso necesita las dos cifras, no un texto.
 */
export class CambioDeMontoError extends Error {
  readonly comisionActual: string
  readonly comisionNueva: string

  constructor(comisionActual: string, comisionNueva: string, mensaje: string) {
    super(mensaje)
    this.name = 'CambioDeMontoError'
    this.comisionActual = comisionActual
    this.comisionNueva = comisionNueva
  }
}

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const detalle = body.detail
    // Los errores de validación de FastAPI vienen como lista de objetos.
    if (Array.isArray(detalle)) {
      throw new Error(detalle.map((d: { msg?: string }) => d.msg ?? '').join(' · '))
    }
    if (detalle?.motivo === 'cambio_de_monto') {
      throw new CambioDeMontoError(
        detalle.comision_actual,
        detalle.comision_nueva,
        detalle.mensaje,
      )
    }
    // Sin esto un detalle con forma de objeto se mostraría como "[object Object]".
    if (detalle !== null && typeof detalle === 'object') {
      throw new Error(detalle.mensaje ?? JSON.stringify(detalle))
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
  payload: {
    tipo_movimiento: string
    comentario?: string | null
    /** Cuándo pasó. Nulo = ahora. */
    fecha?: string | null
    /** Cuándo se vuelve. Nulo = a 3 días de `fecha`, corrido al lunes si cae fin
     *  de semana. */
    proximo_seguimiento?: string | null
  },
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
  /** Liquidaciones y negocios son dos unidades distintas: 7 liquidaciones
   *  pueden ser 6 negocios si uno tiene la promesa y la escritura. */
  negocios: number
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
  /** El universo. **No** salen de sumar los tres buckets: un negocio con la
   *  promesa ganada y la escritura abierta está en dos, así que la suma lo
   *  contaría dos veces. En liquidaciones sí cierra exacto, porque cada una
   *  tiene un estado y uno solo. */
  total_negocios: number
  total_hitos: number
  /** Ganadas sobre resueltas. Las abiertas quedan afuera del denominador: si
   *  entraran, abrir un negocio nuevo bajaría la tasa sin que se pierda nada. */
  tasa_cierre_pct: number
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
  /** Cuántos tienen la fecha de inicio igual a la de cierre. En los migrados del
   *  Excel el origen traía una sola fecha, así que caen en el mes en que
   *  cerraron y no en el que empezaron. Baja solo a medida que entran negocios
   *  con fechas de verdad. */
  con_inicio_aproximado: number
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

// ----------------------------------------- carga del historial de etapas

/**
 * El resultado de cargar el historial de etapas.
 *
 * Las tres listas del final no son errores todas: `anteriores_al_inicio` es
 * información esperada --la fecha real cae antes del inicio mal registrado, que es
 * justamente lo que la hoja de liquidaciones viene a corregir-- y
 * `no_corregidas_por_plata` es la carga negándose a alterar algo que ya funciona.
 */
export type ResumenHistorial = {
  movimientos_creados: number
  movimientos_actualizados: number
  /** Filas que quedaron sin fecha. Es lo normal: de un negocio se saben dos
   *  fechas y no las siete. */
  filas_sin_fecha: number
  fechas_corregidas: number
  /** Filas que no se pudieron aplicar, con el motivo de cada una. */
  omitidas: string[]
  /** Movimientos cuya fecha quedó antes del inicio registrado de su liquidación.
   *  No es un error: es la lista de las que conviene corregir. */
  anteriores_al_inicio: string[]
  /** Liquidaciones que la carga se negó a corregir porque su valorización depende
   *  de la fecha de inicio, así que cambiarla movería el monto. */
  no_corregidas_por_plata: string[]
}

export async function descargarPlantillaHistorial(): Promise<void> {
  const res = await fetch('/api/negocios/plantilla-historial', { credentials: 'include' })
  if (!res.ok) throw new Error(`Error ${res.status}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'historial-de-etapas.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

export function importarHistorial(archivo: File): Promise<ResumenHistorial> {
  const formData = new FormData()
  formData.append('archivo', archivo)
  return fetch('/api/negocios/importar-historial', {
    method: 'POST',
    credentials: 'include',
    body: formData,
  }).then(parseOrThrow)
}
