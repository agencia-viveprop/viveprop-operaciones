import type { EstadoNegocio, ModeloNegocio } from '../api/negocios'

/** Los nombres completos no caben en una celda de tabla. */
export const MODELO_CORTO: Record<ModeloNegocio, string> = {
  MERCADO_PRIMARIO: 'Primario',
  SECUNDARIO_CONCENTRADORES: 'Concentradores',
  SECUNDARIO_AGENCIA: 'Agencia',
}

export const COLOR_ESTADO: Record<EstadoNegocio, string> = {
  ACTIVO: 'info',
  CERRADO: 'good',
  PERDIDO: 'critical',
  DESISTIDO: 'gray',
}

const fmtCLP = new Intl.NumberFormat('es-CL', {
  style: 'currency',
  currency: 'CLP',
  maximumFractionDigits: 0,
})

const fmtUF = new Intl.NumberFormat('es-CL', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
})

/** Pesos sin decimales: nadie factura centavos. */
export function clp(valor: number | string | null | undefined): string {
  if (valor === null || valor === undefined || valor === '') return '—'
  return fmtCLP.format(Number(valor))
}

export function uf(valor: number | string | null | undefined): string {
  if (valor === null || valor === undefined || valor === '') return '—'
  return `UF ${fmtUF.format(Number(valor))}`
}

/** Las tasas se guardan como fracción (0,02) y se muestran como porcentaje. */
export function pct(valor: number | string | null | undefined): string {
  if (valor === null || valor === undefined || valor === '') return '—'
  const n = Number(valor) * 100
  // Hay tasas despejadas a mano como 2,52001208%: se muestran con lo que hagan
  // falta, pero sin arrastrar catorce decimales.
  const decimales = Number.isInteger(n * 100) ? 2 : 4
  return `${n.toFixed(decimales)}%`
}

export function fecha(valor: string | null | undefined): string {
  if (!valor) return '—'
  const [a, m, d] = valor.slice(0, 10).split('-')
  return `${d}-${m}-${a}`
}

/** Días como texto legible. **`null` es "sin dato", no cero.**
 *
 * Los 7 negocios históricos tienen la misma fecha de inicio y de cierre porque
 * el Excel traía una sola, así que su duración es desconocida. Mostrar "0 días"
 * ahí sería presentar un dato malo como un hecho; el guión dice la verdad.
 */
export function duracion(dias: number | null | undefined): string {
  if (dias === null || dias === undefined) return '—'
  if (dias === 0) return 'hoy'
  if (dias === 1) return '1 día'
  if (dias < 45) return `${dias} días`
  const meses = Math.round(dias / 30)
  return `${meses} ${meses === 1 ? 'mes' : 'meses'}`
}
