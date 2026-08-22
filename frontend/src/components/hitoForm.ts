/**
 * Los datos y las reglas de una liquidación, sin nada de React.
 *
 * Están separados del componente porque exportar un componente y además
 * constantes desde el mismo archivo rompe el recargado en caliente de Vite: al
 * tocar una constante, el módulo entero se recarga y se pierde el estado del
 * formulario que se estaba llenando.
 */

export type FormHito = {
  nombre: string
  fecha_inicio: string
  fecha_cierre: string
  estado: string
  valor_negocio: number | ''
  moneda: string
  fecha_valorizacion: string
  valor_clp_manual: number | ''
  motivo_valor_manual: string
  pct_lado_vendedor: number | ''
  pct_lado_comprador: number | ''
  pct_rebate_concentrador: number | ''
  pct_broker_vendedor: number | ''
  pct_broker_comprador: number | ''
  pct_vp_vendedor: number | ''
  pct_vp_comprador: number | ''
  pct_equipo: number | ''
  pct_tercero: number | ''
  nombre_tercero: string
  motivo_perdida_detalle: string
}

/** Qué lado se cobra en cada modelo, para no pedir campos que ese modelo ignora. */
export const CAMPOS_POR_MODELO: Record<
  string,
  { vendedor: boolean; comprador: boolean; rebate: boolean }
> = {
  MERCADO_PRIMARIO: { vendedor: true, comprador: false, rebate: false },
  SECUNDARIO_CONCENTRADORES: { vendedor: false, comprador: true, rebate: true },
  SECUNDARIO_AGENCIA: { vendedor: true, comprador: true, rebate: false },
}

export const PCTS = [
  'pct_lado_vendedor',
  'pct_lado_comprador',
  'pct_rebate_concentrador',
  'pct_broker_vendedor',
  'pct_broker_comprador',
  'pct_vp_vendedor',
  'pct_vp_comprador',
  'pct_equipo',
  'pct_tercero',
] as const

/** El formulario pide porcentajes; la base guarda la fracción. */
export function aFraccion(valor: number | string): string | null {
  if (valor === '' || valor === null) return null
  return String(Number(valor) / 100)
}

/** Y al revés, para poblar el formulario desde un hito guardado. */
export function aPorcentaje(valor: string | number | null | undefined): number | '' {
  if (valor === null || valor === undefined || valor === '') return ''
  return Number(valor) * 100
}

export function hitoVacio(): FormHito {
  return {
    nombre: '',
    fecha_inicio: '',
    fecha_cierre: '',
    estado: 'ACTIVO',
    valor_negocio: '',
    moneda: 'UF',
    fecha_valorizacion: '',
    valor_clp_manual: '',
    motivo_valor_manual: '',
    pct_lado_vendedor: '',
    pct_lado_comprador: '',
    pct_rebate_concentrador: '',
    pct_broker_vendedor: '',
    pct_broker_comprador: '',
    pct_vp_vendedor: '',
    pct_vp_comprador: '',
    // El 10% es lo que se usa en la práctica, aunque REGLAS CALCULO diga 30-40%.
    pct_equipo: 10,
    pct_tercero: '',
    nombre_tercero: '',
    motivo_perdida_detalle: '',
  }
}

/** El cuerpo que espera la API. Los vacíos van como nulo, no como cadena. */
export function payloadHito(form: FormHito): Record<string, unknown> {
  const cuerpo: Record<string, unknown> = {
    nombre: form.nombre.trim() || null,
    fecha_inicio: form.fecha_inicio,
    // La API rechaza una fecha de cierre en un hito que no está cerrado, así que
    // no se manda: es la misma regla, aplicada de este lado para no provocar un
    // 422 evitable.
    fecha_cierre: form.estado === 'CERRADO' ? form.fecha_cierre || null : null,
    estado: form.estado,
    valor_negocio: form.valor_negocio === '' ? null : String(form.valor_negocio),
    moneda: form.moneda || null,
    fecha_valorizacion: form.fecha_valorizacion || null,
    valor_clp_manual: form.valor_clp_manual === '' ? null : String(form.valor_clp_manual),
    motivo_valor_manual: form.motivo_valor_manual || null,
    nombre_tercero: form.nombre_tercero || null,
    motivo_perdida_detalle: form.motivo_perdida_detalle || null,
  }
  PCTS.forEach((p) => (cuerpo[p] = aFraccion(form[p])))
  return cuerpo
}

/**
 * Lo que impide guardar, en palabras. Devuelve `null` si está todo bien.
 *
 * Repite las reglas que la API ya valida, y eso es deliberado: la API es la que
 * manda, pero enterarse recién al enviar es peor experiencia que verlo al tipear.
 */
export function validarHito(form: FormHito): string | null {
  if (!form.fecha_inicio) return 'Falta la fecha de inicio.'
  if (form.estado === 'CERRADO' && !form.fecha_cierre) {
    return 'Una liquidación cerrada necesita fecha de cierre: sin ella no aparece en ningún reporte mensual.'
  }
  if (form.fecha_cierre && form.fecha_cierre < form.fecha_inicio) {
    return 'La fecha de cierre es anterior a la de inicio.'
  }
  if (form.moneda === 'UF' && form.valor_negocio !== '' && !form.fecha_valorizacion) {
    return 'Con un valor en UF hace falta la fecha de valorización para convertirlo a pesos.'
  }
  return null
}

