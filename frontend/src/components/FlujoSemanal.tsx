import { Group, Paper, Text, Title, useComputedColorScheme } from '@mantine/core'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { FlujoDelMes, Semana } from '../api/reportes'

/**
 * Cómo se movió el mes semana a semana, con los meses anteriores superpuestos.
 *
 * **El eje X son las semanas del mes**, no los meses: es lo que el usuario pidió
 * --«poder mostrar cómo van moviéndose los canjes y los negocios semana a semana
 * dentro del mes, y a la vez tener la opción de compararlo con meses
 * anteriores»--. Comparar semana contra semana del mes previo es lo que responde
 * «cómo vamos» sin sacar la vista del mes.
 *
 * **Hasta tres meses, una línea por mes. De cuatro en adelante, el mes elegido
 * contra el promedio de los anteriores.** Doce líneas en un gráfico no se leen, y
 * la regla del proyecto es tres series como máximo por gráfico: con más, la
 * identidad por color deja de funcionar. La tabla de abajo sí lista todos los
 * meses, así que no se pierde nada.
 *
 * **Sin curva de tendencia.** Son cuatro o cinco puntos y el último es una semana
 * de tres días: el ajuste bajaría siempre al final por un artefacto del
 * calendario. La tendencia vive en el bloque mensual.
 */

const PALETA = {
  light: { actual: '#3D3EA8', previo: '#9b9cd4', promedio: '#868e96' },
  dark: { actual: '#7c7dcf', previo: '#565792', promedio: '#909296' },
}

/** Cuántos meses se dibujan uno por uno antes de pasar al promedio. Tres es el
 *  tope de series por gráfico del proyecto. */
const MAXIMO_DE_LINEAS = 3

export type Señal = 'entraron' | 'avanzaron' | 'se_cayeron'

function rotuloMes(clave: string): string {
  const nombres = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
  const [anio, mes] = clave.split('-')
  return `${nombres[Number(mes) - 1] ?? mes} ${anio.slice(2)}`
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
   *  dibujar una línea en cero, que diría «no pasó nada» cuando lo que pasa es
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
  const unoPorUno = previos.slice(0, MAXIMO_DE_LINEAS - 1)
  const agrupados = previos.length > MAXIMO_DE_LINEAS - 1

  const datos = semanas.map((s, i) => {
    const fila: Record<string, string | number | null> = {
      semana: s.etiqueta,
      // El alto del punto no dice cuántos días tiene la semana, así que va al
      // globo: la última siempre va a verse más baja y hay que poder saber por qué.
      dias: s.dias,
      [actual.mes]: actual[señal][i] ?? 0,
    }
    for (const f of unoPorUno) fila[f.mes] = f[señal][i] ?? null
    if (agrupados) {
      const valores = previos.map((f) => f[señal][i]).filter((v) => v !== undefined)
      fila.promedio =
        valores.length > 0 ? valores.reduce((a, b) => a + b, 0) / valores.length : null
    }
    return fila
  })

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
        <LineChart data={datos} margin={{ top: 8, right: 8, left: 0, bottom: 4 }}>
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
            contentStyle={{
              background: 'var(--mantine-color-body)',
              border: '1px solid var(--mantine-color-default-border)',
              borderRadius: 8,
              fontSize: 12,
            }}
            labelFormatter={(v, payload) => {
              const dias = payload?.[0]?.payload?.dias
              return dias && dias < 7 ? `${v} · ${dias} días` : String(v)
            }}
          />
          {/* El mes elegido, sólido y por encima: es el dato. */}
          <Line
            type="linear"
            dataKey={actual.mes}
            name={rotuloMes(actual.mes)}
            stroke={paleta.actual}
            strokeWidth={2.5}
            dot={{ r: 3.5, fill: paleta.actual, strokeWidth: 0 }}
            isAnimationActive={false}
          />
          {/* Los anteriores, partidos: son la referencia. `connectNulls` en falso
              para que febrero --que tiene cuatro semanas-- se corte en la cuarta
              en vez de inventar una quinta en cero. */}
          {unoPorUno.map((f) => (
            <Line
              key={f.mes}
              type="linear"
              dataKey={f.mes}
              name={rotuloMes(f.mes)}
              stroke={paleta.previo}
              strokeWidth={2}
              strokeDasharray="5 4"
              dot={{ r: 2.5, fill: paleta.previo, strokeWidth: 0 }}
              connectNulls={false}
              isAnimationActive={false}
            />
          ))}
          {agrupados && (
            <Line
              type="linear"
              dataKey="promedio"
              name={`promedio de ${previos.length} meses`}
              stroke={paleta.promedio}
              strokeWidth={2}
              strokeDasharray="2 3"
              dot={false}
              connectNulls={false}
              isAnimationActive={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      {/* La leyenda va acá y no con el `<Legend>` de Recharts, igual que en
          `EvolucionMensual`: la librería la ordena por `dataKey` y el orden que
          explica el gráfico es el mes elegido primero. */}
      <Group gap="lg" justify="center" mt={4}>
        <Leyenda color={paleta.actual} texto={rotuloMes(actual.mes)} />
        {unoPorUno.map((f) => (
          <Leyenda key={f.mes} color={paleta.previo} texto={rotuloMes(f.mes)} partida />
        ))}
        {agrupados && (
          <Leyenda
            color={paleta.promedio}
            texto={`promedio de ${previos.length} meses anteriores`}
            partida
          />
        )}
      </Group>
    </Paper>
  )
}

function Leyenda({
  color,
  texto,
  partida,
}: {
  color: string
  texto: string
  partida?: boolean
}) {
  return (
    <Group gap={6} wrap="nowrap">
      <span
        aria-hidden
        style={{
          width: 14,
          height: 0,
          borderTop: `2px ${partida ? 'dashed' : 'solid'} ${color}`,
          display: 'inline-block',
        }}
      />
      <Text size="xs">{texto}</Text>
    </Group>
  )
}
