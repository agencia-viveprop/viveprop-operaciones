import { Group, Paper, Text, Title, useComputedColorScheme } from '@mantine/core'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { FlujoDelMes, Semana } from '../api/reportes'

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
 * | 2 | una barra por mes dentro de cada semana |
 * | 3 a 12 | el mes elegido, y al lado la franja de los anteriores con su promedio |
 *
 * La tabla de abajo lista **todos** los meses en cualquier modo, así que ningún
 * número se pierde por el modo del gráfico.
 */

/**
 * Dos colores para los meses --el índigo principal para el elegido y el coral
 * para el anterior--, asignados por recencia.
 *
 * **Son dos y no tres porque el validador rechazó el tercero.** Con las tres
 * barras a la vista dentro de un grupo, el par que importa es *cualquiera* de
 * ellos, así que la comprobación es `--pairs all`. Ahí el trío del proyecto
 * **falla en modo oscuro**: el índigo claro contra el teal queda en ΔE 4,3 deutan
 * y 11,8 en visión normal, bajo el piso de 15, o sea que ni con visión de color
 * completa se distinguen. La regla para ese caso es cortar series, no shippear
 * una paleta que no pasa. Con dos, el peor par es ΔE 17,6 protan y 25,2 normal en
 * oscuro, y 23,4 / 37,1 en claro.
 *
 * **La rampa de un solo tono también se probó y también la rechazó.** Tres pasos
 * de índigo (`#3D3EA8,#7B7CD0,#B9BAE6` y dos variantes) dejan el tercero bajo el
 * piso de croma --se lee gris-- y bajo 3:1 contra la superficie: una barra que
 * casi no se ve.
 *
 * Del tercer mes en adelante el gráfico cambia de modo --la franja de los
 * anteriores-- así que nunca hacen falta más de dos colores de mes.
 */
const PALETA = {
  light: {
    meses: ['#3D3EA8', '#F4545A'],
    // La franja de los meses anteriores es una **referencia**, no un mes: gris de
    // cero croma, para que no se lea como una tercera categoría.
    franja: '#dee2e6',
    borde: '#adb5bd',
    promedio: '#495057',
    superficie: '#fcfcfb',
  },
  dark: {
    meses: ['#7c7dcf', '#F4545A'],
    franja: '#373A40',
    borde: '#5c5f66',
    promedio: '#c1c2c5',
    superficie: '#1f1f22',
  },
} as const

/** Cuántos meses se dibujan como barra propia antes de pasar a la franja. Son dos
 *  por la paleta --ver `PALETA`-- y porque dos barras por semana es la comparación
 *  más directa que hay: un grupo de barras finitas deja de compararse. */
const MAXIMO_DE_BARRAS = 2

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
  sinDatos,
}: {
  titulo: string
  subtitulo: string
  semanas: Semana[]
  /** El mes elegido primero y después los anteriores. */
  flujo: FlujoDelMes[]
  señal: Señal
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
        <BarChart
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
        </BarChart>
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
