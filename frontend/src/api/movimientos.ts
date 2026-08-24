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
export function crearMovimientoCanje(
  canjeId: number,
  payload: { tipo_movimiento: string; comentario?: string; fecha?: string },
): Promise<Movimiento> {
  return fetch(`/api/canjes/${canjeId}/movimientos`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  }).then(parseOrThrow)
}
