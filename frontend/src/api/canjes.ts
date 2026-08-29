/** En qué terminó el canje, o si sigue en curso.
 *
 *  `CERRADO` llegó tarde: durante todo el histórico solo existieron los otros dos,
 *  así que no había forma de registrar que un canje se concretó. Los 31 que tienen
 *  la etapa en «Cierre» están cancelados — llegaron a la firma y se cayeron.
 *
 *  La **etapa** `CERRADO` y este estado son cosas distintas: la etapa dice hasta
 *  dónde llegó el proceso, el estado en qué terminó. */
export type CanjeEstado = 'ACTIVO' | 'CERRADO' | 'CANCELADO'
export type CanjeEtapa = 'EN_REVISION' | 'PROCESO_DE_ACUERDO' | 'EN_OFERTA' | 'EN_NEGOCIO' | 'CERRADO'
export type OperacionTipo = 'VENTA' | 'ARRIENDO' | 'OTRO'
export type MonedaTipo = 'CLP' | 'UF' | 'OTRA'

export type Canje = {
  id: number
  fecha_solicitud: string
  fecha_cierre: string | null
  estado: CanjeEstado
  etapa: CanjeEtapa
  corredor_solicitante_nombre: string | null
  corredor_solicitante_email: string | null
  corredor_propietario_nombre: string | null
  corredor_propietario_email: string | null
  tipo_operacion: OperacionTipo | null
  tipo_inmueble: string | null
  comuna: string | null
  direccion: string | null
  valor_prop: number | null
  moneda_valor: MonedaTipo | null
  link_propiedad: string | null
  valor_negocio: number | null
  valor_negocio_moneda: MonedaTipo | null
  /** La comisión real que Dataprop cobró al cerrar, no una estimación: la
   *  estimada la calcula el motor a partir del valor de la propiedad. Vacía en las
   *  303 filas, porque nunca se cerró un canje.
   *
   *  Y la plata es de **Dataprop**, no de ViveProp, que opera el Centro de Canje a
   *  nombre de ella y no percibe nada. Nunca se suma con la plata de negocios. */
  comision_dataprop: number | null
  comision_dataprop_moneda: MonedaTipo | null
  notas: string | null
  gestionado_en_app: boolean
}

async function parseOrThrow(res: Response) {
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail ?? `Error ${res.status}`)
  }
  return res.json()
}

export function listarCanjes(
  filtros: {
    estado?: string
    etapa?: string
    comuna?: string
    numero?: string
    solicitante?: string
    propietario?: string
  } = {},
): Promise<Canje[]> {
  const params = new URLSearchParams()
  Object.entries(filtros).forEach(([k, v]) => v && params.set(k, v))
  const qs = params.toString()
  return fetch(`/api/canjes${qs ? `?${qs}` : ''}`, { credentials: 'include' }).then(parseOrThrow)
}

export function crearCanje(payload: Record<string, unknown>): Promise<Canje> {
  return fetch('/api/canjes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  }).then(parseOrThrow)
}

export function actualizarCanje(id: number, payload: Record<string, unknown>): Promise<Canje> {
  return fetch(`/api/canjes/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',
    body: JSON.stringify(payload),
  }).then(parseOrThrow)
}

export type ImportarResumen = {
  nuevas: number
  actualizadas: number
  ignoradas: number
  errores: string[]
}

/**
 * El .xlsx vacío con los 16 encabezados exactos.
 *
 * No es para llenarlo a mano --el archivo sale de la query contra Dataprop-- sino
 * para comparar encabezados cuando la carga falla y no se entiende por qué.
 */
export async function descargarPlantillaCanjes(): Promise<void> {
  const res = await fetch('/api/canjes/plantilla', { credentials: 'include' })
  if (!res.ok) throw new Error(`Error ${res.status}`)
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'plantilla-canjes.xlsx'
  a.click()
  URL.revokeObjectURL(url)
}

export function importarCanjes(archivo: File): Promise<ImportarResumen> {
  const formData = new FormData()
  formData.append('archivo', archivo)
  return fetch('/api/canjes/importar', {
    method: 'POST',
    credentials: 'include',
    body: formData,
  }).then(parseOrThrow)
}

// -------------------------------------------------------------- bandeja diaria

/**
 * `sin_gestion` es un nivel aparte y no "crítico": nunca tocado y abandonado
 * tres días son problemas distintos. Ver el servicio del sprint 20.
 */
/**
 * Los dos primeros salen de un compromiso registrado --alguien agendó una fecha--
 * y los cuatro siguientes del semáforo, que infiere urgencia del tiempo sin
 * gestión. Cuando hay compromiso, manda el compromiso.
 */
export type NivelSemaforo =
  | 'vencido'
  | 'para_hoy'
  | 'sin_gestion'
  | 'critico'
  | 'advertencia'
  | 'al_dia'

export type FilaBandeja = {
  canje_id: number
  fecha_solicitud: string
  etapa: CanjeEtapa
  corredor_solicitante_nombre: string | null
  corredor_propietario_nombre: string | null
  comuna: string | null
  direccion: string | null
  nivel: NivelSemaforo
  horas_sin_gestion: number | null
  ultimo_movimiento: string | null
  ultimo_movimiento_nombre: string | null
  /** Lo que se prometió: la fecha del movimiento más reciente que agendó algo. */
  proximo_seguimiento: string | null
  /** Días de atraso: positivo si venció, cero si es para hoy, nulo sin compromiso.
   *  Lo calcula el servidor, para que el "hoy" no dependa del reloj del navegador. */
  dias_de_atraso: number | null
}

export type Bandeja = {
  resumen: {
    vencido: number
    para_hoy: number
    sin_gestion: number
    critico: number
    advertencia: number
    al_dia: number
    /** Los agendados para más adelante. **No están en `filas`**: la pantalla se
     *  llama «qué me toca hoy». Se cuentan para que se sepa que no se perdieron. */
    agendados: number
  }
  filas: FilaBandeja[]
  umbral_critico_horas: number
  umbral_advertencia_horas: number
}

export function obtenerBandeja(): Promise<Bandeja> {
  return fetch('/api/canjes/bandeja', { credentials: 'include' }).then(parseOrThrow)
}

// -------------------------------------------------- listado de canjes activos

/** Un movimiento del historial desplegado, en el listado de activos. */
export type MovimientoDelListado = {
  id: number
  /** Cuándo se hizo la gestión. Es la fecha que elige la persona al registrar. */
  fecha: string
  tipo_nombre: string
  etapa_resultante: string | null
  corredor: string | null
  autor_nombre: string | null
  comentario: string | null
  /** Días entre la gestión y su registro, cuando pasó más de un día. Nulo cuando
   *  se registró el mismo día o el siguiente, que es lo habitual.
   *
   *  **No es una señal de estado**: si se registró tarde no cambia que la gestión
   *  ocurrió cuando ocurrió. Va al lado del movimiento para que un registro
   *  atrasado no deje un canje con cara de al día sin que se pueda saber por qué.
   *
   *  Nulo también en los que vinieron de una carga masiva: ahí el atraso es la
   *  definición de la carga y no una señal de nada. */
  dias_hasta_el_registro: number | null
  /** Si entró en una carga masiva. Se sabe porque comparte el instante exacto de
   *  creación con otros: una carga es una sola transacción. */
  de_carga_masiva: boolean
}

export type EstadoGestion = 'al_dia' | 'pendiente'

export type FilaCanjeActivo = {
  canje_id: number
  fecha_solicitud: string
  etapa: CanjeEtapa
  corredor_solicitante_nombre: string | null
  corredor_propietario_nombre: string | null
  comuna: string | null
  direccion: string | null
  estado: EstadoGestion
  /** Nulo cuando el canje nunca se gestionó. **No es cero**: un cero diría que se
   *  gestionó hoy. */
  horas_sin_gestion: number | null
  ultima_gestion: string | null
  proximo_seguimiento: string | null
  /** Positivo si el compromiso venció, cero si es para hoy, negativo si es a
   *  futuro, nulo si nadie agendó nada. */
  dias_de_atraso: number | null
  /** Cuántos de sus registros vinieron de una carga masiva, y de cuándo. Se dice
   *  una vez arriba del historial en vez de repetirlo en cada línea. */
  registros_de_carga: number
  fecha_de_carga: string | null
  /** El historial completo, del más viejo al más nuevo. */
  movimientos: MovimientoDelListado[]
}

/**
 * Es un **reporte**, no una lista de trabajo, y por eso muestra **todos** los
 * canjes abiertos --incluso los agendados para adelante, que «Qué me toca hoy»
 * esconde a propósito--. Un reporte que esconde filas no sirve para saber cuántos
 * canjes abiertos hay.
 */
export type ListadoCanjesActivos = {
  filas: FilaCanjeActivo[]
  al_dia: number
  pendientes: number
  umbral_horas: number
}

export function obtenerCanjesActivos(): Promise<ListadoCanjesActivos> {
  return fetch('/api/canjes/reportes/activos', { credentials: 'include' }).then(parseOrThrow)
}

// ------------------------------------- la plata y los plazos del Centro de Canje

/**
 * Un grupo de canjes con su plata.
 *
 * `con_monto` dice **sobre cuántos se pudo calcular**, y va a propósito: es menor
 * que `canjes` cuando falta el valor, la moneda, la operación o la UF de esa fecha.
 * Sin eso no hay comisión, y contarlos como cero bajaría los promedios con datos
 * que no existen.
 */
export type BolsaDeCanjes = {
  canjes: number
  con_monto: number
  valor_propiedades: string
  comision_corredores: string
  comision_dataprop: string
}

/** Cuántos días, sobre las dos poblaciones que sí se pueden medir.
 *
 *  **Ninguna mide "cuánto tarda en cerrar"**: no hay un solo canje cerrado. Llamar
 *  «duración» a la mediana de las cancelaciones sería publicar el tiempo que tardan
 *  en morir como si fuera el que tardan en cerrar. */
export type PlazosCanjes = {
  sobrevivencia_n: number
  sobrevivencia_mediana: number | null
  sobrevivencia_min: number | null
  sobrevivencia_max: number | null
  edad_n: number
  edad_mediana: number | null
  edad_min: number | null
  edad_max: number | null
  /** Cancelados sin fecha de término: su duración es desconocida y no entran en
   *  ninguna mediana. Se dice cuántos son para que no parezca que la muestra es más
   *  grande de lo que es. */
  sin_fecha_de_termino: number
}

/**
 * **Es plata de Dataprop, no de ViveProp.** ViveProp opera el Centro de Canje a
 * nombre de Dataprop y no percibe nada de él, así que estos montos nunca se suman
 * con los de negocios.
 *
 * Las tres cifras significan cosas distintas: la **cobrada** sale del campo manual
 * de los cerrados y es un hecho; las otras dos salen de la regla y son proyecciones.
 */
export type PlataCanjes = {
  cobrada: BolsaDeCanjes
  potencial: BolsaDeCanjes
  no_concretada: BolsaDeCanjes
  plazos: PlazosCanjes
  uf_de_hoy: string
  fecha_uf: string
}

export function obtenerPlataCanjes(): Promise<PlataCanjes> {
  return fetch('/api/canjes/reportes/plata', { credentials: 'include' }).then(parseOrThrow)
}


/** Los valores que existen para cada filtro, para poder sugerir en vez de adivinar.
 *
 *  Es el universo completo y no depende de los filtros aplicados: si saliera del
 *  listado ya filtrado, elegir un valor haria desaparecer al resto de las
 *  opciones y para cambiarlo habria que limpiar primero.
 *
 *  Las tres listas vienen juntas porque se piden en el mismo momento --al abrir
 *  la pantalla-- y son cortas: 106, 134 y 43 valores. */
export type OpcionesDeFiltro = {
  solicitantes: string[]
  propietarios: string[]
  comunas: string[]
}

/** La clave de la consulta de opciones, en un solo lugar. Ver el porqué en el
 *  equivalente de `api/negocios.ts`: una clave escrita en dos archivos deja las
 *  sugerencias viejas cuando alguien crea o importa canjes. */
export const CLAVE_OPCIONES_CANJES = ['canjes-opciones-filtro']

export function listarOpcionesDeFiltro(): Promise<OpcionesDeFiltro> {
  return fetch('/api/canjes/filtros', { credentials: 'include' }).then(parseOrThrow)
}
