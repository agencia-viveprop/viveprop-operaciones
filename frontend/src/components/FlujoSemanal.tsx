import { Group, Paper, Text, Title, useComputedColorScheme } from '@mantine/core'
import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { FlujoDelMes, Semana, TendenciaSemanal } from '../api/reportes'

/**
 * Cómo se movió el mes semana a semana, con los meses anteriores al lado.
 *
 * **El eje X son las semanas del mes**, no los meses: es lo que el usuario pidió
 * --«poder mostrar cómo van moviéndose los canjes y los negocios semana a semana
 * dentro del mes, y a la vez tener la opción de compararlo con meses
 * anteriores»--. Comparar semana contra semana del mes previo es lo que responde
 * «cómo vamos» sin sacar la vista del mes.
 *
 * **Son barras y no líneas** (`D-099`). Una línea entre S1 y S2 dibuja un camino
 * que el dato no tiene: las semanas son cajones, no un continuo, y nada existe a
 * mitad de camino entre la primera y la segunda. Con líneas además los meses
 * anteriores se perdían --el usuario lo dijo: *«tienden a enredar la lectura, y
 * los periodos anteriores se pierden»*--.
 *
 * **Barras agrupadas, nunca apiladas.** Apilar suma, y la S1 de agosto más la S1
 * de julio no es la cantidad de nada: el alto del apilado sería un número
 * inventado. Apilar sirve donde las partes componen un todo real, como el reparto
 * de la comisión en el reporte mensual.
 *
 * **Tres modos según cuántos meses se comparan**, porque un grupo de doce barras
 * por semana no se lee:
 *
 * | Meses | Qué se dibuja |
 * |---|---|
 * | 1 | las barras del mes |
 * | 2 o 3 | una barra por mes dentro de cada semana, cada mes con su color |
 * | 4 a 12 | el mes elegido, y al lado la franja de los anteriores con su promedio |
 *
 * La tabla de abajo lista **todos** los meses en cualquier modo, así que ningún
 * número se pierde por el modo del gráfico.
 *
 * **Y una sola línea de tendencia, ajustada con toda la ventana comparada**
 * (`D-100`). No es una por mes --serían tres curvas sobre tres pares de barras--
 * sino una que dice cómo se mueve el mes por dentro: el promedio de cada semana en
 * los meses que se están comparando. Se dibuja solo sobre las semanas completas,
 * porque la parcial bajaría la curva al final siempre, y solo si tiene algo que
 * decir (`mostrar`).
 */

/**
 * Tres colores para los meses, asignados por recencia: **el mes elegido en azul
 * navy**, el anterior en el coral de la marca, y el tercero en teal. Es lo que
 * pidió el usuario --«en Azul Navy la del mes actual y las otras en colores
 * distintos»--.
 *
 * **Los tres salieron de recorrer el espacio de color con el validador, no de
 * elegirlos a ojo.** El trío que tenía la app (`#3D3EA8, #0891B2, #F4545A`)
 * **falla con `--pairs all` en modo oscuro**: el índigo claro contra el teal queda
 * en ΔE 4,3 deutan y 11,8 en visión normal, bajo el piso de 15. Y `--pairs all`
 * es la comprobación que corresponde: las tres barras se ven juntas dentro del
 * grupo, así que el par que puede confundirse es *cualquiera* de ellos y no solo
 * los vecinos en la lista.
 *
 * La búsqueda recorrió tonos y luminosidades en OKLCH pidiendo el azul más oscuro
 * que pase las cinco comprobaciones en los dos modos. Resultado:
 *
 * | | claro | oscuro |
 * |---|---|---|
 * | mes elegido | `#024d9d` | `#066eda` |
 * | mes anterior | `#F4545A` | `#F4545A` |
 * | el de antes | `#1794a0` | `#1794a0` |
 *
 * Peor par en claro: ΔE 10,8 protan y 21,2 en visión normal. En oscuro: 10,8
 * protan y 15,6 normal. Contraste contra la superficie ≥ 3:1 en los dos modos, sin
 * excepciones ni relief.
 *
 * **Por qué el navy cambia de paso en oscuro.** `#024d9d` contra el fondo oscuro
 * no llega a 3:1 --queda en 2,3-- así que en oscuro sube a `#066eda`, que da 3,5:1.
 * Es el mismo criterio que usa `EvolucionMensual` con su índigo. Con el mismo hex
 * en los dos modos el azul no puede bajar de L 0,48, y ahí ya no se lee como navy.
 *
 * Del cuarto mes en adelante el gráfico cambia de modo --la franja de los
 * anteriores-- así que nunca hacen falta más de tres colores de mes.
 */
const PALETA = {
  light: {
    meses: ['#024d9d', '#F4545A', '#1794a0'],
    // La franja de los meses anteriores es una **referencia**, no un mes: gris de
    // cero croma, para que no se lea como una cuarta categoría.
    franja: '#dee2e6',
    borde: '#adb5bd',
    promedio: '#495057',
    // La tendencia es una lectura y no una categoría, así que va en un neutro:
    // un cuarto tono se leería como un cuarto mes. En el resto de la app la
    // tendencia usa el teal de `info`, pero acá el teal ya es un mes, así que el
    // neutro es lo que queda libre. Se distingue del promedio de la franja por el
    // trazo partido, no por el color.
    tendencia: '#212529',
    superficie: '#fcfcfb',
  },
  dark: {
    meses: ['#066eda', '#F4545A', '#1794a0'],
    franja: '#373A40',
    borde: '#5c5f66',
    promedio: '#c1c2c5',
    tendencia: '#f8f9fa',
    superficie: '#1f1f22',
  },
} as const

/** Cuántos meses se dibujan como barra propia antes de pasar a la franja. Tres es
 *  el tope de series categóricas del proyecto, y también donde deja de leerse: un
 *  grupo de cuatro barras finitas por semana ya no se compara. */
const MAXIMO_DE_BARRAS = 3

export type Señal = 'entraron' | 'avanzaron' | 'se_cayeron'

function rotuloMes(clave: string): string {
  const nombres = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
  const [anio, mes] = clave.split('-')
  return `${nombres[Number(mes) - 1] ?? mes} ${anio.slice(2)}`
}

function numero(valor: number): string {
  return Number.isInteger(valor) ? String(valor) : valor.toFixed(1).replace('.', ',')
}

type Fila = {
  semana: string
  dias: number
  parcial: boolean
  promedio: number | null
  minimo: number | null
  maximo: number | null
  /** El punto de la curva de tendencia, o `null` en la semana parcial, que queda
   *  fuera del ajuste. */
  tendencia: number | null
  [mes: string]: string | number | boolean | null
}

type FormaDeBarra = {
  x?: number
  y?: number
  width?: number
  height?: number
  payload?: Fila
}

/**
 * La franja de los meses anteriores: del mínimo al máximo, con el promedio como
 * raya dentro.
 *
 * **Se dibuja a mano y no con el `<ErrorBar>` de Recharts.** El bigote de la
 * librería se probó primero y dibujaba un rango que no era el del dato --toma el
 * valor como distancia y termina mostrando otra cosa-- así que quedaba mintiendo.
 * Acá la barra lleva el máximo como valor, y de su alto en píxeles salen las tres
 * posiciones: la escala es lineal desde cero, así que un píxel vale
 * `alto / máximo` unidades.
 *
 * **Por qué franja y no solo el promedio.** Un promedio de 3,2 no dice si eso es
 * lo normal o la casualidad de dos meses raros. Con la franja, la barra del mes
 * elegido se lee contra ella: adentro es «vamos como siempre», y asomando arriba
 * es una semana buena de verdad.
 */
function FranjaDeAnteriores({
  x,
  y,
  width,
  height,
  payload,
  colores,
  rayado,
}: FormaDeBarra & {
  colores: { franja: string; borde: string; promedio: string }
  rayado: string
}) {
  if (x === undefined || y === undefined || width === undefined || height === undefined) return null
  const minimo = payload?.minimo
  const maximo = payload?.maximo
  const promedio = payload?.promedio
  if (minimo === null || minimo === undefined) return null
  if (maximo === null || maximo === undefined) return null
  if (promedio === null || promedio === undefined) return null

  // Con máximo cero no hay alto del que sacar la escala, y tampoco hay nada que
  // mostrar: las semanas en cero ya se leen en el eje.
  if (maximo === 0) return null

  const porUnidad = height / maximo
  const yMinimo = y + (maximo - minimo) * porUnidad
  const yPromedio = y + (maximo - promedio) * porUnidad
  const alto = Math.max(yMinimo - y, 2)

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={width}
        height={alto}
        rx={2}
        fill={payload?.parcial ? `url(#${rayado})` : colores.franja}
        stroke={colores.borde}
        strokeWidth={1}
      />
      <line
        x1={x}
        y1={yPromedio}
        x2={x + width}
        y2={yPromedio}
        stroke={colores.promedio}
        strokeWidth={2}
      />
    </g>
  )
}

export default function FlujoSemanal({
  titulo,
  subtitulo,
  semanas,
  flujo,
  señal,
  tendencia,
  sinDatos,
}: {
  titulo: string
  subtitulo: string
  semanas: Semana[]
  /** El mes elegido primero y después los anteriores. */
  flujo: FlujoDelMes[]
  señal: Señal
  /** La curva sobre las semanas, ajustada con toda la ventana. Se dibuja solo si
   *  `mostrar`: una recta plana pegada al promedio no dice nada y tapa barras. */
  tendencia?: TendenciaSemanal
  /** Por qué esta señal no tiene datos, si no los tiene. Se explica en vez de
   *  dibujar una barra en cero, que diría «no pasó nada» cuando lo que pasa es
   *  «no se sabe». */
  sinDatos?: string
}) {
  const modo = useComputedColorScheme('light')
  const paleta = PALETA[modo]

  if (sinDatos) {
    return (
      <Paper withBorder radius="md" p="md">
        <Title order={5}>{titulo}</Title>
        <Text size="sm" c="dimmed" mt={6}>
          {sinDatos}
        </Text>
      </Paper>
    )
  }

  const [actual, ...previos] = flujo
  const unoPorUno = previos.slice(0, MAXIMO_DE_BARRAS - 1)
  const conFranja = previos.length > MAXIMO_DE_BARRAS - 1
  const series = conFranja ? [actual] : [actual, ...unoPorUno]

  // La curva viaja alineada con las primeras semanas --la parcial queda fuera del
  // ajuste-- así que el índice de la semana sirve de índice de la curva.
  const curva = tendencia?.mostrar ? tendencia.curva : null

  const datos: Fila[] = semanas.map((s, i) => {
    const fila: Fila = {
      semana: s.etiqueta,
      // El alto de la barra no dice cuántos días tiene la semana. La última es
      // parcial, así que va rayada y el globo lo repite: siempre va a verse más
      // baja y hay que poder saber por qué.
      dias: s.dias,
      parcial: s.dias < 7,
      promedio: null,
      minimo: null,
      maximo: null,
      tendencia:
        curva !== null && i < curva.length ? Number(curva[i]) : null,
    }
    for (const f of series) fila[f.mes] = f[señal][i] ?? 0
    if (conFranja) {
      const valores = previos.map((f) => f[señal][i]).filter((v) => v !== undefined)
      if (valores.length > 0) {
        fila.promedio = valores.reduce((a, b) => a + b, 0) / valores.length
        fila.minimo = Math.min(...valores)
        fila.maximo = Math.max(...valores)
      }
    }
    return fila
  })

  const rayado = (i: number) => `rayado-${señal}-${i}`
  const rayadoFranja = `rayado-${señal}-franja`

  return (
    <Paper withBorder radius="md" p="md">
      <Group justify="space-between" align="baseline">
        <Title order={5}>{titulo}</Title>
        <Text size="xs" c="dimmed">
          {rotuloMes(actual.mes)} ·{' '}
          <Text span fw={700}>
            {actual[señal].reduce((a, b) => a + b, 0)}
          </Text>{' '}
          en el mes
        </Text>
      </Group>
      <Text size="xs" c="dimmed" mb="sm">
        {subtitulo}
      </Text>

      <ResponsiveContainer width="100%" height={200}>
        <ComposedChart
          data={datos}
          margin={{ top: 8, right: 8, left: 0, bottom: 4 }}
          barGap={2}
          barCategoryGap="18%"
        >
          <defs>
            {/* La semana parcial va rayada a 45°: es textura y no color, así que
                no gasta un tono ni se confunde con otro mes. */}
            {[...series.map((_, i) => paleta.meses[i]), paleta.borde].map((color, i) => (
              <pattern
                key={i}
                id={i < series.length ? rayado(i) : rayadoFranja}
                width={6}
                height={6}
                patternUnits="userSpaceOnUse"
                patternTransform="rotate(45)"
              >
                <rect width={6} height={6} fill={paleta.superficie} />
                <rect width={3} height={6} fill={color} />
              </pattern>
            ))}
          </defs>
          <CartesianGrid stroke="var(--mantine-color-default-border)" vertical={false} />
          <XAxis
            dataKey="semana"
            tick={{ fontSize: 11, fill: 'var(--mantine-color-dimmed)' }}
            stroke="var(--mantine-color-default-border)"
          />
          <YAxis
            allowDecimals={false}
            tick={{ fontSize: 11, fill: 'var(--mantine-color-dimmed)' }}
            stroke="var(--mantine-color-default-border)"
            width={32}
          />
          <Tooltip
            cursor={{ fill: 'var(--mantine-color-default-hover)' }}
            content={({ active, payload }) => {
              if (!active || !payload?.length) return null
              const fila = payload[0].payload as Fila
              return (
                <Paper withBorder radius="sm" p={8} shadow="sm">
                  <Text size="xs" fw={700}>
                    {fila.semana}
                    {fila.parcial ? ` · ${fila.dias} días` : ''}
                  </Text>
                  {series.map((f, i) => (
                    <Text key={f.mes} size="xs">
                      <Cuadro color={paleta.meses[i]} /> {rotuloMes(f.mes)}:{' '}
                      <Text span fw={700}>
                        {numero(Number(fila[f.mes]))}
                      </Text>
                    </Text>
                  ))}
                  {fila.tendencia !== null && (
                    <Text size="xs" c="dimmed">
                      tendencia {numero(fila.tendencia)}
                    </Text>
                  )}
                  {conFranja && fila.promedio !== null && (
                    <>
                      <Text size="xs">
                        <Cuadro color={paleta.franja} borde={paleta.borde} /> {previos.length} meses
                        anteriores: de{' '}
                        <Text span fw={700}>
                          {numero(fila.minimo ?? 0)}
                        </Text>{' '}
                        a{' '}
                        <Text span fw={700}>
                          {numero(fila.maximo ?? 0)}
                        </Text>
                      </Text>
                      <Text size="xs" c="dimmed">
                        promedio {numero(fila.promedio)}
                      </Text>
                    </>
                  )}
                </Paper>
              )
            }}
          />
          {series.map((f, i) => (
            <Bar
              key={f.mes}
              dataKey={f.mes}
              name={rotuloMes(f.mes)}
              fill={paleta.meses[i]}
              radius={[3, 3, 0, 0]}
              maxBarSize={38}
              isAnimationActive={false}
            >
              {datos.map((d) => (
                <Cell
                  key={d.semana}
                  fill={d.parcial ? `url(#${rayado(i)})` : paleta.meses[i]}
                  stroke={d.parcial ? paleta.meses[i] : undefined}
                  strokeWidth={d.parcial ? 1 : 0}
                />
              ))}
            </Bar>
          ))}
          {conFranja && (
            <Bar
              dataKey="maximo"
              name={`${previos.length} meses anteriores`}
              maxBarSize={38}
              isAnimationActive={false}
              shape={(props: object) => (
                <FranjaDeAnteriores
                  {...(props as FormaDeBarra)}
                  colores={paleta}
                  rayado={rayadoFranja}
                />
              )}
            />
          )}
          {curva !== null && (
            <Line
              type="monotone"
              dataKey="tendencia"
              name="tendencia"
              stroke={paleta.tendencia}
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={false}
              connectNulls={false}
              isAnimationActive={false}
            />
          )}
        </ComposedChart>
      </ResponsiveContainer>

      {/* La leyenda va acá y no con el `<Legend>` de Recharts, igual que en
          `EvolucionMensual`: la librería la ordena por `dataKey` y el orden que
          explica el gráfico es el mes elegido primero. */}
      <Group gap="lg" justify="center" mt={4}>
        {series.map((f, i) => (
          <Leyenda key={f.mes} color={paleta.meses[i]} texto={rotuloMes(f.mes)} />
        ))}
        {conFranja && (
          <Group gap={6} wrap="nowrap">
            <svg width={13} height={13} aria-hidden>
              <rect
                x={0.5}
                y={0.5}
                width={12}
                height={12}
                rx={2}
                fill={paleta.franja}
                stroke={paleta.borde}
              />
              <line x1={0.5} y1={7} x2={12.5} y2={7} stroke={paleta.promedio} strokeWidth={2} />
            </svg>
            <Text size="xs">
              los {previos.length} anteriores: el rango, y la raya es el promedio
            </Text>
          </Group>
        )}
        {curva !== null && (
          <Group gap={6} wrap="nowrap">
            <span
              aria-hidden
              style={{
                width: 14,
                height: 0,
                borderTop: `2px dashed ${paleta.tendencia}`,
                display: 'inline-block',
              }}
            />
            <Text size="xs">
              tendencia de las {tendencia?.semanas} semanas completas
              {(tendencia?.meses ?? 0) > 1 ? `, sobre los ${tendencia?.meses} meses` : ''}
            </Text>
          </Group>
        )}
        {datos.some((d) => d.parcial) && (
          <Group gap={6} wrap="nowrap">
            <span
              aria-hidden
              style={{
                width: 12,
                height: 12,
                borderRadius: 2,
                border: `1px solid ${paleta.meses[0]}`,
                backgroundImage: `repeating-linear-gradient(45deg, ${paleta.meses[0]} 0 3px, transparent 3px 6px)`,
                display: 'inline-block',
              }}
            />
            <Text size="xs">semana parcial</Text>
          </Group>
        )}
      </Group>
    </Paper>
  )
}

function Cuadro({ color, borde }: { color: string; borde?: string }) {
  return (
    <span
      aria-hidden
      style={{
        width: 8,
        height: 8,
        borderRadius: 2,
        background: color,
        border: borde ? `1px solid ${borde}` : undefined,
        display: 'inline-block',
      }}
    />
  )
}

function Leyenda({ color, texto }: { color: string; texto: string }) {
  return (
    <Group gap={6} wrap="nowrap">
      <span
        aria-hidden
        style={{
          width: 12,
          height: 12,
          borderRadius: 2,
          background: color,
          display: 'inline-block',
        }}
      />
      <Text size="xs">{texto}</Text>
    </Group>
  )
}
