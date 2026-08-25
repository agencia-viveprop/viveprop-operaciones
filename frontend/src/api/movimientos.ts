export type TipoMovimiento = {
  codigo: string
  nombre: string
  etapa_resultante: string | null
  orden: number | null
}

export type Movimiento = {
  id: number
  tipo_movimiento: string
  tipo_nombre: string
  etapa_resultante: string | null
  fecha: string
  autor_nombre: string | null
  comentario: string | null
  proximo_seguimiento: string | null
}

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Error ${res.status}`)
  }
  return res.json()
}

export function listarTiposMovimiento(entityType: 'canje' | 'negocio'): Promise<TipoMovimiento[]> {
  return fetch(`/api/tipos-movimiento?entity_type=${entityType}`, { credentials: 'include' }).then(parseOrThrow)
}

export function listarMovimientosCanje(canjeId: number): Promise<Movimiento[]> {
  return fetch(`/api/canjes/${canjeId}/movimientos`, { credentials: 'include' }).then(parseOrThrow)
}

/**
 * Registra un movimiento en un canje.
 *
 * `fecha` es opcional y va en ISO con zona. Si no se manda, el servidor pone el
 * instante en que llega la petición, que es el comportamiento de siempre.
 */
/**
 * Borra un movimiento de un canje.
 *
 * El servidor recalcula lo que dependía de él: la etapa se vuelve a derivar de
 * los movimientos que quedan --si no queda ninguno, vuelve a «Sin etapa»-- y si
 * el borrado era la cancelación, el canje vuelve a activo.
 */
export async function eliminarMovimientoCanje(canjeId: number, movimientoId: number): Promise<void> {
  const res = await fetch(`/api/canjes/${canjeId}/movimientos/${movimientoId}`, {
    method: 'DELETE',
    credentials: 'include',
  })
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => ({}))
    throw new Error(cuerpo.detail ?? `Error ${res.status}`)
  }
}

export function crearMovimientoCanje(
  canjeId: number,
  payload: {
    tipo_movimiento: string
    comentario?: string
    fecha?: string
    /** Cuándo volver a mirar el canje. Sin él, el servidor agenda dos días
     *  corridos hacia adelante, corridos al lunes si caen fin de semana. */
    proximo_seguimiento?: string
    /** Dónde queda el canje. Es un dato aparte del tipo: el tipo dice qué se
     *  hizo y la etapa dónde quedó. */
    etapa?: string
  },
): Promise<Movimiento> {
  return fetch(`/api/canjes/${canjeId}/movimientos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  }).then(parseOrThrow)
}
