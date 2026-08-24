// Clientes de reportería. El resumen de canjes (sprint B4) y el reporte
// semanal de período (sprint 16) comparten archivo porque los dos son
// reportes; no comparten endpoint ni tipos.

// --------------------------------------------------- resumen de canjes

export type ConteoEtiqueta = { etiqueta: string; cantidad: number }

/** Una etapa con su total y el desglose por estado, para filtrar sin reconsultar. */
export type ConteoEtapa = ConteoEtiqueta & { activos: number; cancelados: number }

export type ResumenCanjes = {
  total: number
  activos: number
  cancelados: number
  tasa_activos_pct: number
  /** Los que están ACTIVO pero con la etapa en Cerrado: el tile de «Activos» los
   *  excluye, así que explican por qué el desglose puede sumar más que el tile. */
  activos_con_etapa_cerrada: number
  por_etapa: ConteoEtapa[]
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


// --------------------------------------------- reporte mensual comparativo

export type MetricasMes = {
  etiqueta: string
  hitos_cerrados: number
  comision_real_vp: string
  comision_total: string
  negocios_iniciados: number
  canjes_solicitados: number
  canjes_cerrados: number
  canjes_cancelados: number
  /** Los que siguen vivos. `solicitados = activos + cancelados` exacto, y esa
   *  identidad es la que permite dibujarlos apilados. */
  canjes_activos: number
}

/** Los dos reportes en que se separó la pantalla. */
export type Dominio = 'negocios' | 'canjes'

export type Variacion = {
  metrica: string
  /** A qué reporte pertenece. Viene del backend en vez de deducirse del nombre:
   *  filtrar por el texto visible se rompería al renombrar una métrica. */
  dominio: Dominio
  actual: string
  referencia: string
  absoluta: string
  /** Nulo cuando la referencia fue cero: no hay porcentaje que calcular. */
  pct: string | null
}

/**
 * La recta que mejor ajusta la serie de la ventana.
 *
 * `pct_por_mes` viene en la respuesta pero **no se muestra**: con tres meses una
 * serie que cae a cero da pendientes de "-150% por mes", que es correcto y se lee
 * como un error. Lo que se muestra es la dirección y la recta dibujada, que es la
 * misma información sin el número absurdo.
 */
export type Tendencia = {
  metrica: string
  dominio: Dominio
  puntos: number
  pendiente: string
  pct_por_mes: string | null
  direccion: 'sube' | 'baja' | 'plana'
  desde: string
  hasta: string
}

/** El promedio de la ventana. Todos sus campos llegan como texto: son decimales. */
export type PromedioMes = {
  etiqueta: string
  hitos_cerrados: string
  comision_real_vp: string
  comision_total: string
  negocios_iniciados: string
  canjes_solicitados: string
  canjes_cerrados: string
  canjes_cancelados: string
  canjes_activos: string
}

export type Comparacion = {
  /** Los dos lados van explícitos: la ventana móvil no coincide con el mes. */
  actual: MetricasMes
  contra: MetricasMes
  variaciones: Variacion[]
}

export type ReporteMensual = {
  /** El mes calendario, como detalle de "qué pasó". No es el titular. */
  mes: MetricasMes
  ventana_meses: number
  meses_sin_cierres: number
  /** Cuántos meses de la ventana ya tenían negocios. No siempre es el largo de la
   *  ventana: en la histórica, los meses previos al primer negocio no cuentan. */
  meses_con_negocios: number
  /** El titular: la ventana móvil contra la anterior del mismo largo. */
  movil: Comparacion
  anio_corrido: Comparacion
  /** Mes por mes de la ventana, del más viejo al más nuevo. Es lo que permite
   *  ver si el mes actual avanza, se estanca o retrocede: la comparación de
   *  ventana contra ventana dice cuánto cambió, no en qué dirección venía. */
  serie: MetricasMes[]
  /** `true` con la ventana histórica. La pantalla la rotula así y esconde la
   *  comparación contra la ventana anterior, que no existe. */
  es_historico: boolean
  /** Desde qué mes existe cada dominio, en formato '2025-08'. Es desde donde se
   *  promedia y se traza su tendencia, para que los meses previos al primer
   *  negocio no diluyan la referencia. */
  inicio_por_dominio: Record<string, string | null>
  /**
   * El promedio mensual de la ventana, para la línea de referencia.
   *
   * Tipo propio y no `MetricasMes`: acá los conteos son decimales, porque el
   * promedio de un conteo lo es. Cuatro liquidaciones en seis meses son 0,67 por
   * mes, y truncarlo a 0 hacía que el reporte afirmara que no se cierra nada.
   */
  promedio: PromedioMes
  /** La tendencia de cada métrica sobre la ventana, indexada por su campo. */
  tendencias: Record<string, Tendencia>
}

/** Cero es la ventana histórica: toda la serie desde el primer registro. El
 *  servidor la resuelve al número real de meses y lo informa en `ventana_meses`. */
export const VENTANA_HISTORICO = 0

export const VENTANAS = [3, 6, 12, VENTANA_HISTORICO] as const

/**
 * La parte de la serie desde que el dominio que se está mirando existe.
 *
 * **Solo recorta en la ventana histórica.** Ahí la serie arranca en el primer
 * registro de *cualquiera* de los dos dominios --hoy noviembre de 2022, que es un
 * canje-- así que el gráfico de negocios empezaba con 33 meses vacíos antes de su
 * primera barra. No son meses malos: son meses sin negocio, y dibujarlos deja el
 * gráfico casi todo en blanco y la forma real apretada al final.
 *
 * En 3, 6 y 12 meses **no** recorta: ahí el largo es lo que se pidió, y mostrar
 * menos barras que las elegidas sería contestar otra pregunta. Si el dominio
 * arrancó dentro de esa ventana, las barras vacías del principio se quedan y lo
 * que se acota son las líneas de referencia, que ya saben su tramo.
 */
export function serieDelDominio(
  serie: MetricasMes[],
  esHistorico: boolean,
  inicio: string | null | undefined,
): MetricasMes[] {
  if (!esHistorico || !inicio) return serie
  const desde = serie.filter((m) => m.etiqueta >= inicio)
  // Si el recorte deja la serie vacía se devuelve entera: un gráfico sin barras
  // no explica nada, y es mejor mostrar los meses en cero que nada.
  return desde.length > 0 ? desde : serie
}

/** Cómo se llama cada ventana en el selector. */
export function rotuloVentana(v: number): string {
  return v === VENTANA_HISTORICO ? 'Histórico' : `${v} meses`
}

export function obtenerReporteMensual(
  anio: number,
  mes: number,
  ventana: number,
): Promise<ReporteMensual> {
  return fetch(`/api/reportes/mensual?anio=${anio}&mes=${mes}&ventana=${ventana}`, {
    credentials: 'include',
  }).then(parseOrThrow)
}


// ------------------------------------------------------- vista directorio

export type Monto = { etiqueta: string; valor: string }

export type BucketDirectorio = {
  hitos: number
  negocios: number
  comision_real_vp: string
}

export type Conversion = {
  cerrados: number
  perdidos: number
  /** Va siempre: una tasa de 41% sobre 17 casos y otra sobre 1.700 se leen
   *  igual y no valen lo mismo. */
  n: number
  tasa_pct: string
  intervalo_bajo_pct: string
  intervalo_alto_pct: string
}

export type Ticket = {
  mediano: string
  minimo: string
  maximo: string
  n: number
}

export type Proyeccion = {
  pipeline: string
  pesimista: string
  esperado: string
  optimista: string
  /** Si es true, no hay forma de decir *cuándo* entra la plata. */
  sin_dato_de_plazo: boolean
  nota: string
}

/** Un desglose en unidades. El hermano de `Monto` cuando no se cuenta plata. */
export type Conteo = { etiqueta: string; cantidad: number }

/**
 * La mitad de canjes del directorio: volumen, origen y supervivencia.
 *
 * Sin ticket ni proyección, y no es un olvido: canjes sí genera comisión --la de
 * administración de Dataprop-- pero se calcula sobre la comisión de los
 * corredores, que está sin cargar, y `valor_prop` no sirve de reemplazo porque su
 * moneda está equivocada en ~138 de las 297 filas (`D-054`).
 */
export type CanjesDirectorio = {
  /** Del período elegido. `solicitados = activos + cancelados`, exacto. */
  solicitados: number
  activos: number
  cancelados: number
  /** De toda la historia, para que el número del período tenga contra qué leerse. */
  solicitados_historicos: number
  activos_historicos: number
  /** Los que están ACTIVO con la etapa en Cerrado. Restados de los activos dan
   *  lo que el resto de la app llama «vigentes». */
  cerrados_historicos: number
  resueltos_historicos: number
  tasa_cierre_pct: string
  por_operacion: Conteo[]
  por_tipo_inmueble: Conteo[]
  por_comuna: Conteo[]
}

export type VistaDirectorio = {
  generado: string
  /** Manda sobre lo temporal --la ventana móvil, la serie, la tendencia y los
   *  conteos de canjes del período-- y no sobre los buckets, la tasa de cierre,
   *  el ticket ni la proyección, que siguen siendo históricos. */
  ventana_meses: number
  anio_corrido: MetricasMes
  anio_corrido_anterior: MetricasMes
  ventana_movil: MetricasMes
  ganado: BucketDirectorio
  pipeline: BucketDirectorio
  potencial_perdido: BucketDirectorio
  por_modelo: Monto[]
  por_alianza: Monto[]
  conversion: Conversion
  ticket: Ticket | null
  proyeccion: Proyeccion
  serie: MetricasMes[]
  /** `true` con la ventana histórica. La pantalla la rotula así y esconde la
   *  comparación contra la ventana anterior, que no existe. */
  es_historico: boolean
  /** Desde qué mes existe cada dominio, en formato '2025-08'. Es desde donde se
   *  promedia y se traza su tendencia. */
  inicio_por_dominio: Record<string, string | null>
  promedio: PromedioMes
  tendencias: Record<string, Tendencia>
  canjes: CanjesDirectorio
}

export function obtenerVistaDirectorio(ventana: number): Promise<VistaDirectorio> {
  return fetch(`/api/reportes/directorio?ventana=${ventana}`, {
    credentials: 'include',
  }).then(parseOrThrow)
}
