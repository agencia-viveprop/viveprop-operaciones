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
 * **Una barra por cada mes seleccionado, siempre** (`D-101`). Lo pidió así --«sería
 * bueno ver tantas barras como meses se hayan seleccionado»-- y reemplazó la franja
 * de mínimo-máximo que resumía los meses de la cuarta en adelante. Con doce meses
 * son doce barras por semana, y lo que cambia con la cantidad no es cuántas se
 * dibujan sino **qué codifica el color**: ver `CATEGORICOS` y `RAMPAS`.
 *
 * **Barras agrupadas, nunca apiladas.** Apilar suma, y la S1 de agosto más la S1
 * de julio no es la cantidad de nada: el alto del apilado sería un número
 * inventado. Apilar sirve donde las partes componen un todo real, como el reparto
 * de la comisión en el reporte mensual.
 *
 * **Y una sola línea de tendencia, ajustada con toda la ventana comparada**
 * (`D-100`). No es una por mes --serían doce curvas sobre doce barras-- sino una
 * que dice cómo se mueve el mes por dentro: el promedio de cada semana en los
 * meses que se están comparando. Se dibuja solo sobre las semanas completas,
 * porque la parcial bajaría la curva al final siempre, y solo si tiene algo que
 * decir (`mostrar`).
 *
 * La tabla de «Los mismos números» lista los meses con sus cifras exactas, que es
 * donde se lee lo que un grupo de doce barras no puede decir al detalle.
 */

/**
 * El color cambia de trabajo según cuántos meses haya, y es la única forma de
 * dibujar doce barras sin mentir.
 *
 * **Hasta tres meses: el color identifica el mes.** Es el trío categórico que
 * salió de recorrer el espacio de color con el validador (`D-099`): navy para el
 * elegido, coral para el anterior, teal para el de antes. Pasa las cinco
 * comprobaciones con `--pairs all` en los dos modos --peor par ΔE 10,8 protan y
 * 21,2 en visión normal-- y contraste sobre 3:1 sin excepciones.
 *
 * **De cuatro en adelante: el color codifica recencia.** No hay doce tonos
 * distinguibles y no existe paleta categórica que lo resuelva, así que la escala
 * pasa a ser **ordinal**: el mes elegido en el navy fuerte y los anteriores cada
 * vez más suaves, un solo tono. Se validó con `validateOrdinal`, que pide
 * luminosidad monótona, un salto visible entre pasos (ΔL ≥ 0,06) y que el paso más
 * suave siga leyéndose contra la superficie (≥ 2:1).
 *
 * **Hasta dónde el paso es identificable, medido:** el salto mínimo entra **6
 * veces** en el rango útil, en los dos modos. Con más meses que eso los pasos
 * quedan más juntos que el piso y el validador lo marca. **Se dibujan igual, y por
 * qué:** ahí el color ya no es el canal de identidad sino un
 * gradiente que dice una sola cosa --oscuro es reciente, claro es antiguo--. Quién
 * es cada barra lo dice **la posición** en el grupo, que es fija: la primera de
 * cada semana es siempre el mes elegido. El globo nombra cada mes con su cifra, y
 * la tabla de abajo trae todos los números. Es codificación compuesta, que es lo
 * que corresponde cuando las series pasan de lo que el color aguanta.
 *
 * Las rampas están calculadas, no elegidas: un script las generó en OKLCH sobre el
 * tono del navy y las pasó por el validador, una por cantidad de meses, para que
 * cada ventana use todo el rango disponible en vez de recortar una rampa fija.
 */
const CATEGORICOS = {
  light: ['#024d9d', '#F4545A', '#1794a0'],
  dark: ['#066eda', '#F4545A', '#1794a0'],
} as const

/** Del mes elegido --el paso fuerte-- al más antiguo. Una rampa por cantidad de
 *  meses, para que la ventana use todo el rango que el modo permite. */
const RAMPAS: Record<'light' | 'dark', Record<number, string[]>> = {
  light: {
    4: ['#024d9d', '#1f6dcb', '#5a92dc', '#8db5ec'],
    5: ['#024d9d', '#0564c7', '#3f80d4', '#679be0', '#8db5ec'],
    6: ['#024d9d', '#035fbf', '#2d75cf', '#4f8bd9', '#6ea0e2', '#8db5ec'],
    7: ['#024d9d', '#075cb8', '#1f6dcb', '#3f80d4', '#5a92dc', '#73a4e4', '#8db5ec'],
    8: ['#024d9d', '#065ab4', '#1368c9', '#3278d0', '#4b87d7', '#6197de', '#77a6e5', '#8db5ec'],
    9: ['#024d9d', '#0058b3', '#0564c7', '#2872cd', '#3f80d4', '#538dda', '#679be0', '#7aa8e6', '#8db5ec'],
    10: ['#024d9d', '#0357af', '#0361c3', '#1f6dcb', '#357ad1', '#4886d7', '#5a92dc', '#6b9ee1', '#7ca9e7', '#8db5ec'],
    11: ['#024d9d', '#0656ac', '#035fbf', '#1769c9', '#2d75cf', '#3f80d4', '#4f8bd9', '#5f95de', '#6ea0e2', '#7eabe7', '#8db5ec'],
    12: ['#024d9d', '#0355ac', '#045dbb', '#0f66c8', '#2671cd', '#377bd2', '#4685d6', '#558edb', '#6398df', '#71a2e3', '#7face8', '#8db5ec'],
  },
  // En oscuro el extremo fuerte es el **más claro**: sobre fondo oscuro la marca
  // fuerte es la que más se despega del fondo, así que la rampa corre al revés que
  // en claro. Y arranca más arriba --L 0,78-- porque con el arranque en el navy del
  // trío el rango quedaba en 0,195 y solo entraban cuatro pasos: doce meses salían
  // casi del mismo azul. Estirado entran seis, los mismos que en claro.
  dark: {
    4: ['#88bafd', '#5093ec', '#3d70b4', '#2b4f7f'],
    5: ['#88bafd', '#549dfb', '#4682d0', '#3868a6', '#2b4f7f'],
    6: ['#88bafd', '#5da2fe', '#4c8ce1', '#4177bf', '#36639e', '#2b4f7f'],
    7: ['#88bafd', '#64a6fe', '#5093ec', '#4682d0', '#3d70b4', '#345f99', '#2b4f7f'],
    8: ['#88bafd', '#69a9ff', '#5299f5', '#4a89dc', '#427ac4', '#3a6bac', '#335d95', '#2b4f7f'],
    9: ['#88bafd', '#6cabff', '#549dfb', '#4d8fe5', '#4682d0', '#3f75bb', '#3868a6', '#325b92', '#2b4f7f'],
    10: ['#88bafd', '#70adff', '#59a0fd', '#5093ec', '#4988d9', '#437cc6', '#3d70b4', '#3765a2', '#315a90', '#2b4f7f'],
    11: ['#88bafd', '#73aefe', '#5da2fe', '#5197f2', '#4c8ce1', '#4682d0', '#4177bf', '#3b6daf', '#36639e', '#30598e', '#2b4f7f'],
    12: ['#88bafd', '#74afff', '#61a5fe', '#539af7', '#4e90e7', '#4986d8', '#447dc8', '#3f73b9', '#3a6aaa', '#35619b', '#30588d', '#2b4f7f'],
  },
}

const ESTRUCTURA = {
  light: {
    // La tendencia es una lectura y no una categoría, así que va en un neutro: un
    // tono más se leería como un mes más. En el resto de la app la tendencia usa el
    // teal de `info`, pero acá el teal ya es un mes (`D-099`).
    tendencia: '#212529',
    superficie: '#fcfcfb',
  },
  dark: {
    tendencia: '#f8f9fa',
    superficie: '#1f1f22',
  },
} as const

/** Hasta cuántos meses el color identifica el mes en vez de ordenarlo. */
const TOPE_CATEGORICO = 3

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
  /** El punto de la curva de tendencia, o `null` en la semana parcial, que queda
   *  fuera del ajuste. */
  tendencia: number | null
  [mes: string]: string | number | boolean | null
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
  /** El mes elegido primero y después los anteriores. Se dibujan todos. */
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
  const estructura = ESTRUCTURA[modo]

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

  const [actual] = flujo
  const n = flujo.length
  const ordinal = n > TOPE_CATEGORICO
  const colores = ordinal
    ? (RAMPAS[modo][Math.min(n, 12)] ?? RAMPAS[modo][12])
    : CATEGORICOS[modo].slice(0, n)

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
      tendencia: curva !== null && i < curva.length ? Number(curva[i]) : null,
    }
    for (const f of flujo) fila[f.mes] = f[señal][i] ?? 0
    return fila
  })

  const rayado = (i: number) => `rayado-${señal}-${i}`

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
          // El aire entre barras baja con la cantidad, pero no llega a cero: sin
          // separación dos meses de tonos vecinos se leen como una sola barra
          // ancha. El aire entre semanas --`barCategoryGap`-- es el que separa los
          // grupos y ese no se toca.
          barGap={n > 6 ? 1 : 2}
          barCategoryGap="16%"
        >
          <defs>
            {/* La semana parcial va rayada a 45°: es textura y no color, así que no
                gasta un tono ni se confunde con otro mes. */}
            {colores.map((color, i) => (
              <pattern
                key={i}
                id={rayado(i)}
                width={6}
                height={6}
                patternUnits="userSpaceOnUse"
                patternTransform="rotate(45)"
              >
                <rect width={6} height={6} fill={estructura.superficie} />
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
                  {flujo.map((f, i) => (
                    <Text key={f.mes} size="xs">
                      <Cuadro color={colores[i]} /> {rotuloMes(f.mes)}:{' '}
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
                </Paper>
              )
            }}
          />
          {flujo.map((f, i) => (
            <Bar
              key={f.mes}
              dataKey={f.mes}
              name={rotuloMes(f.mes)}
              fill={colores[i]}
              radius={n > 6 ? [1, 1, 0, 0] : [3, 3, 0, 0]}
              maxBarSize={38}
              isAnimationActive={false}
            >
              {datos.map((d) => (
                <Cell
                  key={d.semana}
                  fill={d.parcial ? `url(#${rayado(i)})` : colores[i]}
                  stroke={d.parcial ? colores[i] : undefined}
                  strokeWidth={d.parcial ? 1 : 0}
                />
              ))}
            </Bar>
          ))}
          {curva !== null && (
            <Line
              type="monotone"
              dataKey="tendencia"
              name="tendencia"
              stroke={estructura.tendencia}
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
        {ordinal ? (
          // Con cuatro meses o más, nombrar doce chips llenaría la tarjeta de
          // leyenda. Va la rampa entera con sus dos extremos rotulados, que es lo
          // que hay que saber para leer el gradiente: el orden dentro del grupo.
          <Group gap={8} wrap="nowrap">
            <Text size="xs">{rotuloMes(actual.mes)}</Text>
            <Group gap={1} wrap="nowrap">
              {colores.map((color) => (
                <span
                  key={color}
                  aria-hidden
                  style={{ width: 10, height: 12, background: color, display: 'inline-block' }}
                />
              ))}
            </Group>
            <Text size="xs">{rotuloMes(flujo[flujo.length - 1].mes)}</Text>
            <Text size="xs" c="dimmed">
              · en ese orden dentro de cada semana
            </Text>
          </Group>
        ) : (
          flujo.map((f, i) => (
            <Leyenda key={f.mes} color={colores[i]} texto={rotuloMes(f.mes)} />
          ))
        )}
        {curva !== null && (
          <Group gap={6} wrap="nowrap">
            <span
              aria-hidden
              style={{
                width: 14,
                height: 0,
                borderTop: `2px dashed ${estructura.tendencia}`,
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
                border: `1px solid ${colores[0]}`,
                backgroundImage: `repeating-linear-gradient(45deg, ${colores[0]} 0 3px, transparent 3px 6px)`,
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

function Cuadro({ color }: { color: string }) {
  return (
    <span
      aria-hidden
      style={{
        width: 8,
        height: 8,
        borderRadius: 2,
        background: color,
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
