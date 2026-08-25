import type { CanjeEtapa } from '../api/canjes'

/**
 * Los rótulos de canjes, en un solo lugar.
 *
 * Estaban copiados en tres archivos --el modal de seguimiento, la bandeja y la
 * pantalla de canjes-- y este listado iba a ser el cuarto. Las tres copias decían
 * lo mismo, así que no había un error todavía; lo que había era tres lugares
 * donde renombrar una etapa deja las pantallas diciendo cosas distintas de la
 * misma cosa, y sin que nada falle.
 *
 * El nombre canónico de cada valor vive en el backend, en `app/models/canje.py`,
 * al lado del enum. Acá está la traducción para mostrar.
 */
export const ETAPA_LABELS: Record<CanjeEtapa, string> = {
  RECEPCION: 'Recepción',
  EN_REVISION: 'En revisión',
  PROCESO_DE_ACUERDO: 'Proceso de acuerdo',
  EN_OFERTA: 'En oferta',
  EN_NEGOCIO: 'En negocio',
  CERRADO: 'Cierre',
}

/** El orden de avance, que es el de lectura de cualquier selector de etapa.
 *
 *  Sale de las claves del mapa y no de una segunda lista: dos listas del mismo
 *  conjunto se desincronizan en cuanto alguien agrega una etapa en una sola. */
export const ETAPAS = Object.keys(ETAPA_LABELS) as CanjeEtapa[]

export const CORREDOR_LABELS: Record<string, string> = {
  SOLICITANTE: 'Corredor solicitante',
  PROPIETARIO: 'Corredor propietario',
}

/**
 * El rótulo de una etapa que llega como texto suelto.
 *
 * `movimientos.etapa_resultante` es `String(20)` y no un tipo enumerado, porque
 * la tabla es polimórfica: sirve a canjes y a negocios, y un valor de un dominio
 * no debería imponerle un tipo a la columna compartida. Así que del backend llega
 * como `string`, y este helper evita un cast en cada lugar que lo muestra.
 *
 * Si el código no está en el mapa se devuelve tal cual: es mejor mostrar
 * `EN_OFERTA` que una celda vacía.
 */
export function rotuloEtapa(codigo: string): string {
  return ETAPA_LABELS[codigo as CanjeEtapa] ?? codigo
}

/** Lo mismo para el corredor sobre el que se hizo la gestión. */
export function rotuloCorredor(codigo: string): string {
  return CORREDOR_LABELS[codigo] ?? codigo
}
