// Facturación y pago de negocios y canjes. Un solo módulo para los dos dominios
// porque el tipo de dato es el mismo: cambia de qué cuelga la obligación, no qué
// es. Los endpoints sí son dos, cada uno bajo su recurso.

export type Avance = {
  id: number
  estado_codigo: string | null
  estado_nombre: string | null
  monto: number | null
  fecha: string | null
  autor: string | null
  creado_en: string
}

export type Obligacion = {
  tipo: string
  rotulo: string
  /** Falso mientras nadie la tocó: la pantalla dice «sin registrar», que es
   *  información distinta de un monto en cero. */
  registrada: boolean
  estado_id: number | null
  estado_codigo: string | null
  estado_nombre: string | null
  /** Lo que se facturó o se pagó de verdad. Puede diferir del calculado por
   *  ajustes o acuerdos, y esa diferencia se muestra. */
  monto: number | null
  /** Lo que sale del motor de comisiones. Nulo --no cero-- cuando el hito no
   *  tiene el dato: cero diría «no corresponde plata». */
  monto_esperado: number | null
  fecha: string | null
  avances: Avance[]
}

export type AvanceNuevo = {
  tipo: string
  estado_id: number
  monto?: number | null
  fecha?: string | null
}

/** El circuito que pidió el usuario, en orden. No es una transición obligatoria
 *  --un salto se registra igual-- pero sí es el orden en que se ofrece. */
export const CIRCUITO = ['POR_FACTURAR', 'FACTURADO', 'POR_PAGAR', 'PAGADO']

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Error ${res.status}`)
  }
  return res.json()
}

// Las claves de consulta, exportadas para que la pantalla que consulta y las
// mutaciones que invalidan usen el mismo string. Escribirlo en dos archivos es
// cómo se olvida uno (`D-091`).
export const claveObligacionesHito = (negocioId: number, hitoId: number) => [
  'obligaciones',
  'negocio',
  negocioId,
  hitoId,
]
export const claveObligacionesCanje = (canjeId: number) => ['obligaciones', 'canje', canjeId]
export const CLAVE_COBRANZA = ['cobranza']

export function listarObligacionesHito(negocioId: number, hitoId: number): Promise<Obligacion[]> {
  return fetch(`/api/negocios/${negocioId}/hitos/${hitoId}/obligaciones`, {
    credentials: 'include',
  }).then(parseOrThrow)
}

export function registrarObligacionHito(
  negocioId: number,
  hitoId: number,
  cuerpo: AvanceNuevo,
): Promise<Obligacion[]> {
  return fetch(`/api/negocios/${negocioId}/hitos/${hitoId}/obligaciones`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
  }).then(parseOrThrow)
}

export function listarObligacionesCanje(canjeId: number): Promise<Obligacion[]> {
  return fetch(`/api/canjes/${canjeId}/obligaciones`, { credentials: 'include' }).then(parseOrThrow)
}

export function registrarObligacionCanje(
  canjeId: number,
  cuerpo: AvanceNuevo,
): Promise<Obligacion[]> {
  return fetch(`/api/canjes/${canjeId}/obligaciones`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
  }).then(parseOrThrow)
}

// --------------------------------------------------- cobranza

export type TramoDeCobranza = {
  estado_codigo: string | null
  estado_nombre: string | null
  casos: number
  monto_registrado: number
  /** De cuántos casos se registró monto: con esto se lee si el registrado está
   *  incompleto en vez de parecer bajo. */
  con_monto: number
}

/**
 * La misma plata repartida en los tres destinos que la app nunca suma junta.
 *
 * Es la regla de `D-063`, que la cobranza había vuelto a romper: mostraba un solo
 * total por parte y el 38% de esa cifra era de negocios perdidos. Los rótulos los
 * pone la pantalla porque cambian por dominio --«Ganado / En pipeline / No
 * concretado» en negocios, «Cobrada / Potencial / No concretada» en canjes--.
 */
export type PlataPorEstado = {
  logrado: number
  en_curso: number
  no_concretado: number
}

export type ParteDeCobranza = {
  tipo: string
  rotulo: string
  casos: number
  registrado: PlataPorEstado
  calculado: PlataPorEstado
  tramos: TramoDeCobranza[]
}

/** Una liquidación cuya comisión total no cuadra con su reparto. Viene así del
 *  Excel; la ficha del negocio ya lo avisa y la cobranza lo sumaba en silencio. */
export type DescuadreDeReparto = {
  negocio: string
  liquidacion: string | null
  diferencia: number
}

/** Las dos mitades separadas a propósito: la plata de negocios es de ViveProp y
 *  la de canjes es de Dataprop, así que no hay ningún total que las cruce. */
export type Cobranza = {
  negocios: ParteDeCobranza[]
  canjes: ParteDeCobranza[]
  /** El rebate del concentrador. No es una obligación --nadie lo factura-- pero
   *  entra en la comisión real VP sin salir de ninguna otra parte, así que sin él
   *  la resta hacia abajo no cierra. */
  rebate: PlataPorEstado
  descuadres: DescuadreDeReparto[]
  liquidaciones_sin_registrar: number
  canjes_sin_registrar: number
}

export function obtenerCobranza(): Promise<Cobranza> {
  return fetch('/api/reportes/cobranza', { credentials: 'include' }).then(parseOrThrow)
}
