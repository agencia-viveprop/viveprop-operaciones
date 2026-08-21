// Clientes de reportería. El resumen de canjes (sprint B4) y el reporte
// semanal de período (sprint 16) comparten archivo porque los dos son
// reportes; no comparten endpoint ni tipos.

// --------------------------------------------------- resumen de canjes

export type ConteoEtiqueta = { etiqueta: string; cantidad: number }

export type ResumenCanjes = {
  total: number
  activos: number
  cancelados: number
  tasa_activos_pct: number
  por_etapa: ConteoEtiqueta[]
  por_mes: ConteoEtiqueta[]
  por_tipo_inmueble: ConteoEtiqueta[]
  por_operacion: ConteoEtiqueta[]
}

export function obtenerResumenCanjes(): Promise<ResumenCanjes> {
  return fetch('/api/canjes/reportes/resumen', { credentials: 'include' }).then((res) => {
    if (!res.ok) throw new Error(`Error ${res.status}`)
    return res.json()
  })
}


// --------------------------------------------- reporte semanal de período

export type ItemCerrado = {
  referencia: string
  detalle: string | null
  fecha: string | null
  monto: string | null
}

export type ItemMovido = {
  referencia: string
  detalle: string | null
  fecha: string
  etapa: string | null
  comentario: string | null
}

export type ItemEstancado = {
  referencia: string
  detalle: string | null
  etapa: string | null
  dias_sin_movimiento: number | null
}

export type Seccion = {
  cerrados: ItemCerrado[]
  monto_cerrado: string
  avanzados: ItemMovido[]
  caidos: ItemMovido[]
  estancados: ItemEstancado[]
  total_cerrados: number
  total_avanzados: number
  total_caidos: number
  total_estancados: number
}

export type ReporteSemanal = {
  desde: string
  hasta: string
  dias_estancado: number
  negocios: Seccion
  canjes: Seccion
}

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Error ${res.status}`)
  }
  return res.json()
}

export function obtenerReporteSemanal(params: {
  desde?: string
  hasta?: string
  dias_estancado?: number
}): Promise<ReporteSemanal> {
  const qs = new URLSearchParams()
  if (params.desde && params.hasta) {
    qs.set('desde', params.desde)
    qs.set('hasta', params.hasta)
  }
  if (params.dias_estancado) qs.set('dias_estancado', String(params.dias_estancado))
  return fetch(`/api/reportes/semanal${qs.toString() ? `?${qs}` : ''}`, {
    credentials: 'include',
  }).then(parseOrThrow)
}

/** El lunes de la semana que contiene esa fecha, corrida `semanas` semanas.
 *
 * Se calcula en el cliente y no se le pide al servidor para que las flechas de
 * navegación no dependan de un viaje de red: se sabe de antemano qué período se
 * va a pedir.
 */
export function lunesDe(referencia: Date, semanas = 0): Date {
  const d = new Date(referencia)
  // getDay() da 0 el domingo; acá la semana arranca el lunes, igual que en el
  // backend, así que el domingo cuenta como el día 7 de la semana anterior.
  const desplazamiento = (d.getDay() + 6) % 7
  d.setDate(d.getDate() - desplazamiento + semanas * 7)
  return d
}

/** ISO sin la parte de hora y sin pasar por UTC, que correría el día. */
export function aISO(d: Date): string {
  const mes = String(d.getMonth() + 1).padStart(2, '0')
  const dia = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mes}-${dia}`
}
