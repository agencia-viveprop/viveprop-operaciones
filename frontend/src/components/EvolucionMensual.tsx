import { useComputedColorScheme } from '@mantine/core'
import {
  Bar,
  ComposedChart,
  Line,
  CartesianGrid,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Group, Paper, Stack, Text, Title } from '@mantine/core'
import type { MetricasMes, Tendencia } from '../api/reportes'

/**
 * La evolución mes por mes de la ventana elegida.
 *
 * **Qué pregunta responde.** El reporte decía cuánto cambió la ventana contra la
 * anterior, que es un número, pero no en qué dirección venía. Con la serie a la
 * vista se lee de un golpe si el mes actual avanza, se estanca o retrocede.
 *
 * **Barras y no línea.** Los cierres son eventos discretos, y con tres puntos una
 * línea insinúa una continuidad que no existe. Además los meses en cero --que en
 * este negocio son normales-- se leen como barra ausente y no como una caída a
 * cero que después "recupera".
 *
 * **La plata y las cantidades van en gráficos separados**, nunca en dos ejes del
 * mismo. Un eje doble deja que la escala de cada serie se elija sola, y con eso
 * cualquier par de curvas se puede hacer coincidir o divergir a gusto.
 *
 * **La línea del promedio es lo que convierte el gráfico en respuesta.** Una barra
 * más baja que la anterior no dice si el mes es malo; una barra bajo el promedio de
 * su propia ventana, sí. El promedio incluye los meses en cero a propósito
 * --excluirlos inflaría la referencia justo en el sentido que hace ver retroceso
 * donde no hay--.
 */

/**
 * Las paletas, una por modo, validadas con el script del sprint de visualización.
 *
 * No es un aclarado automático del modo claro: `brand.6` (#3D3EA8) contra fondo
 * oscuro da contraste 2.03, bajo el mínimo de 3:1. Se eligió `brand.4` para
 * oscuro y se volvió a validar. El acento #F4545A pasa en los dos modos, y el
 * rojo baja a `critical.4` en oscuro por la banda de luminosidad.
 *
 * El orden importa: el validador mide pares **adyacentes**, así que con tres
 * series verde y rojo juntos caían a ΔE 7.9. Se resolvió dejando dos series por
 * gráfico, que además saca del medio una serie que hoy es cero en todos los meses.
 *
 * **La tercera serie llegó con el reparto de la comisión, y no fue gratis.** Ese
 * gráfico necesita tres segmentos --lo que queda, lo del corredor, lo del equipo
 * y terceros-- y el teal de `info` fue el único tercer tono que pasó las seis
 * comprobaciones en los dos modos. Pero solo en un orden: en oscuro, el teal
 * contra `brand.4` cae a ΔE 4.3 en deuteranopía, o sea indistinguibles. Se
 * resolvió poniéndolos **no adyacentes** en la pila --marca, acento, teal--, que
 * es lo que el validador mide. Con ese orden los dos modos dan ALL CHECKS PASS,
 * y el peor par adyacente queda en ΔE 13.1.
 *
 * Por eso el orden de los segmentos de ese gráfico no es negociable por estética:
 * cambiarlo vuelve a juntar el par que colisiona.
 *
 * **`positiva` llegó con el tercer estado de los canjes.** Al aparecer `CERRADO`,
 * el apilado de solicitudes pasó de dos segmentos a tres, y ahí los tres son
 * estados y no categorías: cerrado, en curso, cancelado. Eso lo hace un caso de
 * paleta de estado --verde, marca, rojo-- y no categórica. Validado en ese orden
 * semántico: ALL CHECKS PASS en los dos modos, peor par adyacente ΔE 15.1 en
 * deuteranopía oscuro. El tritan de ese par baja a 7.4, que la guía permite solo
 * con codificación secundaria; el apilado la tiene de sobra: leyenda con nombres,
 * separación de 2px entre segmentos y el total rotulado arriba.
 *
 * El teal es además el color de la tendencia. En el gráfico del reparto no se
 * dibuja tendencia --una sola recta sobre una composición de tres partes no dice
 * de cuál es-- así que no compiten en la misma tarjeta.
 */
const PALETA = {
  light: {
    principal: '#3D3EA8',
    secundaria: '#F4545A',
    negativa: '#DC2626',
    terciaria: '#0891B2',
    positiva: '#059669',
    // Lo que el usuario apagó en el selector. **No desaparece: se atenúa**, para
    // que el alto de la barra siga siendo el total. Es gris a propósito --cero
    // croma, así que no se confunde con ninguna serie-- y llega a 3.2:1 contra la
    // superficie, que es lo que lo hace visible como bloque. El validador marca
    // FAIL de croma y de banda de luminosidad en este color, y está bien: sus
    // comprobaciones son para paletas categóricas y esta marca es deliberadamente
    // neutra. La que importa acá es el contraste, y pasa.
    apagado: '#868e96',
    // La tendencia es una lectura, no una categoría: va en el teal de `info`,
    // que no está asignado a ninguna serie y así no se confunde con una.
    tendencia: '#0891B2',
  },
  dark: {
    principal: '#7c7dcf',
    secundaria: '#F4545A',
    negativa: '#e35252',
    // En oscuro el teal de la tendencia (#0ab9e3) queda fuera de la banda de
    // luminosidad como **relleno**: pasa como línea y no como área. El paso más
    // oscuro sí pasa, así que el relleno usa `info.6` en los dos modos.
    terciaria: '#0891B2',
    // El mismo verde en los dos modos: pasó el validador contra las dos
    // superficies, así que no hace falta un paso distinto.
    positiva: '#059669',
    // Un paso más claro que en modo claro, por la misma razón invertida: contra
    // fondo oscuro el gris tiene que subir para verse. 3.3:1 contra la superficie.
    apagado: '#909296',
    tendencia: '#0ab9e3',
  },
} as const

/** La rejilla y los ejes tienen que quedar detrás de los datos, no compitiendo.
 *  La escala de grises de Mantine no se invierte con el modo, así que un gris
 *  claro que es recesivo sobre blanco queda prominente sobre fondo oscuro. */
const ESTRUCTURA = {
  light: {
    rejilla: 'var(--mantine-color-gray-3)',
    eje: 'var(--mantine-color-gray-5)',
    // La del promedio va un paso mas oscura: es un dato, no estructura.
    promedio: 'var(--mantine-color-gray-6)',
    // La etiqueta del total no compite con la barra: es un dato de apoyo.
    textoSuave: 'var(--mantine-color-gray-7)',
  },
  dark: {
    rejilla: 'var(--mantine-color-dark-4)',
    eje: 'var(--mantine-color-dark-3)',
    promedio: 'var(--mantine-color-dark-1)',
    textoSuave: 'var(--mantine-color-dark-1)',
  },
} as const

/** 'ago 26' desde '2026-08'. El eje no aguanta el año completo con doce meses. */
function rotuloCorto(etiqueta: string): string {
  // Las semanas llegan como «S1 1-7» y ya vienen listas para el eje. Sin esta
  // guarda, el `split('-')` las partía por el guion del rango y el eje mostraba
  // «14 8» y «21 15»: dos números sin relación con nada (`D-098`).
  if (!/^\d{4}-\d{2}$/.test(etiqueta)) return etiqueta
  const [anio, mes] = etiqueta.split('-')
  const nombres = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
  return `${nombres[Number(mes) - 1] ?? mes} ${anio.slice(2)}`
}

const pesos = (v: number) =>
  new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', maximumFractionDigits: 0 }).format(v)

const millones = (v: number) => (v === 0 ? '0' : `$${(v / 1_000_000).toFixed(1)}M`)

/** Un conteo, con coma decimal. El promedio de un conteo es fraccionario --0,67
 *  liquidaciones por mes-- y escribirlo con punto se lee como otro número. */
const unidades = (v: number) =>
  new Intl.NumberFormat('es-CL', { maximumFractionDigits: 2 }).format(v)

/** El campo sintético que lleva el total de la pila. No es una serie: no se
 *  dibuja como barra, solo se lee para el globo y la etiqueta. */
const CAMPO_TOTAL = '__total'
/** La curva de tendencia, como una serie más de los datos del gráfico.
 *
 * Antes la tendencia era una recta dibujada con `ReferenceLine` y dos puntos. Una
 * curva necesita un valor por mes, y la forma de darle uno por mes a Recharts
 * cuando el eje X es categórico es meterla en el mismo arreglo de datos. */
const CAMPO_CURVA = '__curva'

/**
 * El total del período con el que se compara, punto por punto.
 *
 * Va **una sola línea y no una por serie**: en un gráfico apilado de tres
 * segmentos, tres líneas grises encima son ilegibles, y lo que se quiere comparar
 * es la cifra del período --el alto de la barra-- contra la del período anterior.
 * Por eso es el total de los campos dibujados, igual que `CAMPO_TOTAL`.
 */
const CAMPO_COMPARACION = '__comparacion'

/**
 * El globo del gráfico apilado, con el total arriba de sus partes.
 *
 * **Por qué no alcanza el globo por defecto.** Lista un renglón por segmento
 * --"Cancelados: 10", "Siguen activos: 4"-- y deja la cifra del mes para que la
 * sume quien mira. El alto de la barra la dice, pero leer un alto no es leer un
 * número. Acá el total va primero y en negrita, y los segmentos abajo, que es el
 * orden en que se pregunta: cuántos entraron, y en qué terminaron.
 */
function GloboApilado({
  active,
  payload,
  label,
  etiquetaTotal,
  formato,
}: {
  active?: boolean
  payload?: { name?: string; value?: number; color?: string; dataKey?: string }[]
  label?: string
  etiquetaTotal: string
  formato: (v: number) => string
}) {
  if (!active || !payload?.length) return null

  const partes = payload.filter((x) => x.dataKey !== CAMPO_TOTAL)
  const total = partes.reduce((a, x) => a + Number(x.value ?? 0), 0)

  return (
    <Paper withBorder radius="md" p="xs" shadow="sm">
      <Text size="xs" c="dimmed" fw={700}>
        {label}
      </Text>
      <Text size="sm" fw={700} mt={2}>
        {etiquetaTotal}: {formato(total)}
      </Text>
      <Stack gap={2} mt={4}>
        {/* Del más grande al más chico: con noventa cancelados y cuatro activos,
            listarlos en el orden de la pila pone primero al que no importa. */}
        {[...partes]
          .sort((a, b) => Number(b.value ?? 0) - Number(a.value ?? 0))
          .map((x) => (
            <Group key={x.dataKey} gap={6} wrap="nowrap">
              <span
                aria-hidden
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: x.color,
                  display: 'inline-block',
                }}
              />
              <Text size="xs">
                {x.name}: {formato(Number(x.value ?? 0))}
              </Text>
            </Group>
          ))}
      </Stack>
    </Paper>
  )
}


export type SerieDef = {
  campo: keyof MetricasMes
  nombre: string
  /** El rol en la paleta validada. `tendencia` no entra: es la recta, no una
   *  serie de datos. */
  tono: 'principal' | 'secundaria' | 'negativa' | 'terciaria' | 'positiva'
  /**
   * Si va en gris en vez de su color, sin salir del gráfico.
   *
   * Es lo que hace que un selector de segmentos no cambie el alto de la barra ni
   * la escala del eje: el segmento que se apaga sigue ocupando su lugar, atenuado.
   */
  atenuada?: boolean
}



/**
 * Un gráfico de barras de la serie mensual.
 *
 * `formato` decide si el eje va en pesos o en unidades; se pasa desde afuera
 * porque quien arma el gráfico sabe qué está midiendo y el componente no.
 */
export default function EvolucionMensual({
  titulo,
  subtitulo,
  serie,
  series,
  promedio,
  esPlata = false,
  apilado = false,
  etiquetaTotal = 'Total',
  tendencia,
  serieComparacion,
  rotuloComparacion,
}: {
  titulo: string
  subtitulo?: string
  serie: MetricasMes[]
  /** Una, dos o tres. La tercera es el tope: el validador de color no da margen
   *  para una cuarta, y con `apilado` el orden importa (ver `PALETA`). */
  series: SerieDef[]
  /** El valor de la línea de referencia. Solo se dibuja con una sola serie: con
   *  dos, una línea sola no dice a cuál pertenece. */
  promedio?: number
  esPlata?: boolean
  /**
   * Apila las series en vez de ponerlas lado a lado.
   *
   * Sirve cuando una serie es parte de la otra. En canjes lo son: los activos y
   * los cancelados suman exactamente los solicitados, así que apilados el alto
   * total de la barra **es** la solicitud del mes y el activo queda como su
   * propio segmento. Lado a lado, cuatro activos junto a noventa cancelados se
   * ven como una raya al lado de una torre --el problema que esto resuelve--.
   */
  apilado?: boolean
  /** Cómo se llama la suma de los segmentos, para el globo y la etiqueta. Solo
   *  se usa con `apilado`: es el nombre de la cifra completa del mes. */
  etiquetaTotal?: string
  /** La recta de tendencia sobre la ventana, tal como la calcula el backend.
   *  Sus montos llegan como texto --son `Decimal`-- y se convierten acá. */
  tendencia?: Tendencia
  /** La serie del período con el que se compara, alineada **por posición**: el
   *  primer punto de una contra el primero de la otra. Se dibuja como una línea
   *  gris punteada con el total de los campos, no una línea por serie. */
  serieComparacion?: MetricasMes[]
  /** «2026-03 a 2026-05», para la leyenda de esa línea. */
  rotuloComparacion?: string
}) {
  const modo = useComputedColorScheme('light')
  const paleta = PALETA[modo]
  const estructura = ESTRUCTURA[modo]

  const datos: Record<string, string | number>[] = serie.map((m) => ({
    mes: rotuloCorto(m.etiqueta),
    ...Object.fromEntries(series.map((s) => [s.campo, Number(m[s.campo])])),
    // El total de la pila, precalculado. El alto de la barra ya lo dice, pero el
    // número no estaba en ninguna parte: el globo listaba los segmentos y había
    // que sumarlos de cabeza para tener la cifra del mes.
    //
    // Sumar los segmentos alcanza porque **todos se dibujan siempre**: los que el
    // usuario apaga van atenuados, no fuera del gráfico. Hubo una versión con una
    // prop `totalDe` para calcular el total aparte, y dejó de hacer falta cuando
    // apagar un segmento dejó de sacarlo de la pila.
    [CAMPO_TOTAL]: series.reduce((a, s) => a + Number(m[s.campo]), 0),
  }))

  // La comparación se alinea por posición y no por etiqueta: los rótulos son de
  // meses distintos --junio contra marzo-- así que emparejarlos por nombre no
  // tiene sentido. Si la otra serie es más corta --febrero tiene cuatro semanas y
  // agosto cinco-- los puntos que faltan quedan sin valor y la línea se corta ahí.
  const comparando = serieComparacion !== undefined && serieComparacion.length > 0
  if (comparando) {
    datos.forEach((fila, i) => {
      const otro = serieComparacion![i]
      if (otro) {
        fila[CAMPO_COMPARACION] = series.reduce((a, s) => a + Number(otro[s.campo]), 0)
      }
    })
  }

  const ultimo = datos.length - 1
  const unaSola = series.length === 1
  // Con apilado el valor del mes es la suma de sus segmentos: es el total de la
  // barra, que es justamente lo que la forma apilada pone a la vista.
  const ultimoMes =
    datos.length > 0
      ? {
          rotulo: datos[ultimo].mes,
          valor: (unaSola || apilado ? series : series.slice(0, 1)).reduce(
            (a, s) => a + Number(datos[ultimo][s.campo]),
            0,
          ),
        }
      : null
  const conTotal = unaSola || apilado
  // Doce es lo que entra sin que las etiquetas se toquen en el ancho habitual de
  // la tarjeta; de ahí para arriba, el número vive en el globo.
  const etiquetasVisibles = datos.length <= 12

  const dibujaTendencia =
    tendencia !== undefined && tendencia.mostrar && datos.length > 1

  /**
   * Dónde arranca el tramo que la tendencia describe.
   *
   * **No siempre es el principio del gráfico.** En la ventana histórica la serie
   * va desde el primer registro de cualquiera de los dos dominios, pero cada
   * métrica se ajusta desde que **su** dominio existe: la comisión se traza sobre
   * trece meses en un gráfico de cuarenta y seis. Dibujar esa recta de punta a
   * punta le cambiaba la pendiente y sugería que había negocios desde 2022.
   *
   * `puntos` viene del backend justamente para poder acotarla.
   */
  const desdeTendencia = tendencia
    ? Math.max(0, datos.length - tendencia.puntos)
    : 0

  // La curva entra como una columna más de los datos, alineada al final: los meses
  // anteriores al ajuste quedan en `null` y la línea no se dibuja ahí. Sin el
  // `null` --con un cero, por ejemplo-- la curva bajaría al eje en los meses en que
  // el dominio no existía y se leería como una caída.
  if (tendencia?.mostrar) {
    tendencia.curva.forEach((valor, i) => {
      const fila = datos[desdeTendencia + i]
      if (fila) fila[CAMPO_CURVA] = Number(valor)
    })
  }
  const formato = esPlata ? pesos : unidades
  // El eje va sin decimales: sus marcas son enteras y "2,00" solo agrega ruido.
  const ejeY = esPlata ? millones : (v: number) => String(v)

  return (
    <Paper withBorder radius="md" p="md">
      <Group justify="space-between" align="baseline" mb={subtitulo ? 2 : 'sm'}>
        <Title order={5}>{titulo}</Title>
        {/* El valor del mes actual va acá y no como etiqueta sobre la barra.
            La primera versión lo dibujaba con un `content` propio de `LabelList`,
            y al mirarlo renderizado no aparecía: los nombres de las props que
            entrega Recharts no eran los que se asumieron. Puesto en el
            encabezado, al lado de su referencia, se lee mejor y no depende de los
            internals de la librería. */}
        {conTotal && ultimoMes && (
          <Text size="xs" c="dimmed">
            <Text span fw={700} c="var(--mantine-color-text)">
              {ultimoMes.rotulo} {formato(ultimoMes.valor)}
            </Text>
            {promedio !== undefined && promedio > 0 && <> · promedio {formato(promedio)}</>}
          </Text>
        )}
        {!conTotal && promedio !== undefined && promedio > 0 && (
          <Text size="xs" c="dimmed">
            promedio {formato(promedio)}
          </Text>
        )}
      </Group>
      {subtitulo && (
        <Text size="xs" c="dimmed" mb="sm">
          {subtitulo}
        </Text>
      )}

      <ResponsiveContainer width="100%" height={240}>
        <ComposedChart data={datos} margin={{ top: 18, right: 8, left: 0, bottom: 4 }}>
          {/* Rejilla recesiva y solo horizontal: las verticales competirían con
              las barras, que ya marcan la posición en el eje. */}
          <CartesianGrid vertical={false} stroke={estructura.rejilla} />
          <XAxis dataKey="mes" tick={{ fontSize: 11 }} stroke={estructura.eje} />
          <YAxis
            allowDecimals={false}
            tickFormatter={ejeY}
            tick={{ fontSize: 11 }}
            stroke={estructura.eje}
            width={esPlata ? 52 : 34}
          />
          {apilado ? (
            <Tooltip
              content={
                <GloboApilado etiquetaTotal={etiquetaTotal} formato={formato} />
              }
            />
          ) : (
            <Tooltip
              formatter={(valor, nombre) => [formato(Number(valor)), nombre]}
              contentStyle={{ borderRadius: 8, fontSize: 13 }}
            />
          )}
          {/* El promedio también va acotado al tramo que promedia. Dibujado de
              punta a punta afirmaba que ese nivel era la referencia también en los
              meses en que el dominio no existía. */}
          {promedio !== undefined && promedio > 0 && conTotal && (
            <ReferenceLine
              segment={[
                { x: datos[desdeTendencia].mes as string, y: promedio },
                { x: datos[ultimo].mes as string, y: promedio },
              ]}
              stroke={estructura.promedio}
              strokeDasharray="4 4"
              strokeWidth={2}
            />
          )}

          {/* **La curva de tendencia** (`D-089`). Era una recta de dos puntos
              dibujada con `ReferenceLine`; ahora es un polinomio cuyo grado crece
              con la ventana, así que necesita un valor por mes y va como una serie.
              Sigue siendo una lectura de los datos y no un dato: por eso no tiene
              puntos ni entra en el globo --`tooltipType="none"`-- y su color es el
              teal que no usa ninguna serie.
              Se omite cuando no tiene nada que decir; la regla la decide el
              backend (`mostrar`), no la pantalla. */}
          {tendencia?.mostrar && datos.length > 1 && (
            <Line
              type="monotone"
              dataKey={CAMPO_CURVA}
              stroke={paleta.tendencia}
              strokeWidth={2}
              dot={false}
              activeDot={false}
              connectNulls={false}
              isAnimationActive={false}
              tooltipType="none"
              legendType="none"
            />
          )}

          {/* La comparación, en gris punteado y por debajo de las barras en la
              leyenda: es la referencia, no el dato. Con `connectNulls` en falso,
              una serie de comparación más corta se corta en vez de inventar el
              tramo que falta. */}
          {comparando && (
            <Line
              // **Recta y no `monotone`.** Con pocos puntos, la interpolación
              // suave sobrepasa: en una ventana de seis meses con tres valores
              // dibujaba una loma que subía por encima del máximo real y sugería
              // un mes que nunca existió. La tendencia sí puede ser curva porque
              // es un ajuste; esto son valores, y entre dos valores no hubo nada.
              type="linear"
              dataKey={CAMPO_COMPARACION}
              name={rotuloComparacion ?? 'Período anterior'}
              // **El índigo de la serie principal, distinguido por el trazo y no
              // por el color.** Un color propio para esta línea no pasó el
              // validador: el más cercano que se leía como «lo mismo, antes» daba
              // ΔE 14,5 contra el teal de la tendencia --dos líneas del mismo
              // gráfico que no se distinguen ni con visión de color completa-- y
              // además caía bajo el piso de croma y de contraste. Con el índigo,
              // lo que la separa de las barras es que es una línea partida con
              // puntos, y lo que la separa de la tendencia es el color. La leyenda
              // la nombra con su período, así que la identidad nunca depende del
              // color solo.
              stroke={paleta.principal}
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={{ r: 3, fill: paleta.principal, strokeWidth: 0 }}
              activeDot={false}
              connectNulls={false}
              isAnimationActive={false}
            />
          )}

          {series.map((s) => (
            <Bar
              key={s.campo}
              dataKey={s.campo}
              name={s.nombre}
              fill={s.atenuada ? paleta.apagado : paleta[s.tono]}
              stackId={apilado ? 'total' : undefined}
              /* Solo el segmento de arriba lleva las esquinas redondeadas: en los
                 de abajo, redondear el tope deja un hueco contra el siguiente. */
              radius={apilado && s !== series[series.length - 1] ? undefined : [4, 4, 0, 0]}
              /* Dos píxeles de fondo entre segmentos para que se lean como dos y
                 no como una mancha con un cambio de color. */
              stroke={apilado ? 'var(--mantine-color-body)' : undefined}
              strokeWidth={apilado ? 2 : 0}
              maxBarSize={54}
              /* Sin animación de entrada. Se vuelve a dibujar en cada cambio de
                 ventana o de dominio, así que animar convierte cada clic en un
                 rebote; y además hacía imposible verificar el gráfico en un
                 render sin ventana visible, donde quedaba congelado en altura 0. */
              isAnimationActive={false}
            >
              {/* Todas las barras al mismo tono. La primera versión dibujaba el
                  mes actual opaco y los anteriores translúcidos, y al mirarla
                  renderizada el resultado era un gráfico lavado que no destacaba
                  nada: justamente el mes que se mira suele ser el que está en
                  cero --por eso se lo mira-- así que el énfasis caía en una barra
                  ausente. Lo que ubica el mes actual es su posición (siempre el
                  último), su etiqueta directa y la línea del promedio. */}

              {/* El total sobre la barra, solo en el segmento de arriba y solo
                  cuando hay pocos meses: con cuarenta y seis barras las etiquetas
                  se pisan y tapan justamente lo que vienen a explicar. */}
              {apilado && etiquetasVisibles && s === series[series.length - 1] && (
                <LabelList
                  dataKey={CAMPO_TOTAL}
                  position="top"
                  fontSize={11}
                  fill={estructura.textoSuave}
                  /* Con el mismo formato que el resto del gráfico. Sin esto el
                     total salía crudo --"2386289.21"-- porque hasta ahora el
                     apilado solo se había usado con conteos, donde el número
                     pelado se lee bien. Con pesos, no. */
                  formatter={(v) => (v === undefined || Number(v) === 0 ? '' : formato(Number(v)))}
                />
              )}
            </Bar>
          ))}

        </ComposedChart>
      </ResponsiveContainer>

      {/* La leyenda se dibuja acá y no con el `<Legend>` de Recharts.
          Dejada a la librería salía ordenada por `dataKey` en vez de por el orden
          en que se declaran las series --en canjes se leía "Cancelados ·
          Solicitados", al revés de las barras-- y en la versión 3 ya no acepta un
          `payload` propio para corregirlo. El orden de la leyenda es el que
          explica el gráfico, así que no puede quedar a criterio de la librería. */}
      {(!unaSola || dibujaTendencia || comparando) && (
        <Group gap="lg" justify="center" mt={4}>
          {!unaSola &&
            series.map((s) => (
              <Group key={s.campo} gap={6} wrap="nowrap">
                {/* El punto sigue al relleno de la barra, atenuado incluido: una
                    leyenda que dice rojo donde la barra esta gris es peor que no
                    tener leyenda. Y el nombre se atenua con el, para que se lea de
                    un golpe cual esta apagado. */}
                <span
                  aria-hidden
                  style={{
                    width: 9,
                    height: 9,
                    borderRadius: '50%',
                    background: s.atenuada ? paleta.apagado : paleta[s.tono],
                    display: 'inline-block',
                  }}
                />
                <Text size="xs" c={s.atenuada ? 'dimmed' : undefined}>
                  {s.nombre}
                </Text>
              </Group>
            ))}
          {/* La recta también se nombra: una línea sin explicación en un gráfico
              de barras se lee como un umbral o una meta. */}
          {dibujaTendencia && (
            <Group gap={6} wrap="nowrap">
              <span
                aria-hidden
                style={{
                  width: 14,
                  height: 2,
                  background: paleta.tendencia,
                  display: 'inline-block',
                }}
              />
              <Text size="xs">
                Tendencia de {tendencia!.puntos} meses ({tendencia!.direccion})
              </Text>
            </Group>
          )}
          {promedio !== undefined && promedio > 0 && conTotal && (
            <Group gap={6} wrap="nowrap">
              <span
                aria-hidden
                style={{
                  width: 14,
                  height: 0,
                  borderTop: `2px dashed ${estructura.promedio}`,
                  display: 'inline-block',
                }}
              />
              <Text size="xs">Promedio de la ventana</Text>
            </Group>
          )}
          {/* La comparación se nombra con su período: sin eso, la línea partida
              se lee como una meta o un umbral, que es lo que pasa con cualquier
              línea sin explicación sobre un gráfico de barras. */}
          {comparando && (
            <Group gap={6} wrap="nowrap">
              <span
                aria-hidden
                style={{
                  width: 14,
                  height: 0,
                  borderTop: `2px dashed ${paleta.principal}`,
                  display: 'inline-block',
                }}
              />
              <Text size="xs">{rotuloComparacion ?? 'Período anterior'}</Text>
            </Group>
          )}
        </Group>
      )}
    </Paper>
  )
}

/**
 * La frase que dice si el mes va bien o mal, en palabras.
 *
 * Es lo que pidió el pedido --"rápidamente saber si hay avance, estancamiento o
 * retroceso"-- y un gráfico solo no lo da: hay que compararlo con algo. Se compara
 * contra el promedio de la ventana, no contra el mes anterior, porque con ~1 cierre
 * por mes el mes anterior es ruido.
 */
export function Veredicto({
  actual,
  promedio,
  unidad,
  tendencia,
  esPlata = false,
}: {
  actual: number
  promedio: number
  /** Cómo se llama lo que se mide, para armar la frase. */
  unidad: string
  /** La dirección de la ventana. Es la otra mitad de la respuesta: el promedio
   *  dice si el mes está por encima o por debajo de lo normal, y la tendencia
   *  hacia dónde va la ventana. Una ventana puede estar toda sobre su promedio y
   *  venir cayendo. */
  tendencia?: Tendencia
  esPlata?: boolean
}) {
  const formato = esPlata ? pesos : unidades

  // Del porcentaje de la pendiente no se dice nada a propósito: con tres meses
  // una serie que cae a cero da "-150% por mes", que es correcto y se lee como un
  // error. La dirección y la recta del gráfico cuentan lo mismo sin ese número.
  const frase =
    tendencia && tendencia.direccion !== 'plana' ? (
      <>
        {' '}
        La tendencia sobre {tendencia.puntos} meses viene{' '}
        <Text span fw={700} c={tendencia.direccion === 'sube' ? 'good.7' : 'critical.7'}>
          {tendencia.direccion === 'sube' ? 'al alza' : 'a la baja'}
        </Text>
        .
      </>
    ) : tendencia ? (
      // «Plana» se mide al final de la curva, así que sobre una curva con forma
      // --46 meses que arrancan en cero, suben y hacen techo-- decir "viene
      // plana" contradice lo que se está viendo. Se dice que **se aplanó**, que es
      // lo que pasó. Con una recta plana no hay tal forma y el texto de siempre
      // sirve.
      <>
        {' '}
        La tendencia sobre {tendencia.puntos} meses{' '}
        {tendencia.mostrar && tendencia.grado >= 2 ? 'se aplanó al final' : 'viene plana'}.
      </>
    ) : null

  if (promedio === 0) {
    return (
      <Text size="sm" c="dimmed">
        No hay con qué comparar: la ventana no registra {unidad}.
      </Text>
    )
  }

  const dif = actual - promedio
  const pct = Math.round((dif / promedio) * 100)
  // Menos de un 10% de diferencia no es una tendencia con estos volúmenes.
  const estancado = Math.abs(pct) < 10

  return (
    <Text size="sm">
      {estancado ? (
        <>
          El mes va <Text span fw={700}>en línea</Text> con el promedio de la ventana (
          {formato(promedio)}).
        </>
      ) : (
        <>
          El mes va{' '}
          <Text span fw={700} c={dif > 0 ? 'good.7' : 'critical.7'}>
            {Math.abs(pct)}% {dif > 0 ? 'sobre' : 'bajo'}
          </Text>{' '}
          el promedio de la ventana ({formato(promedio)}).
        </>
      )}
      {frase}
    </Text>
  )
}
