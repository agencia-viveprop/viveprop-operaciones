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
