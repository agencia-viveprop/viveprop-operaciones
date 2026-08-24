import { useComputedColorScheme } from '@mantine/core'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Group, Paper, Text, Title } from '@mantine/core'
import type { MetricasMes } from '../api/reportes'

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
 */
const PALETA = {
  light: { principal: '#3D3EA8', secundaria: '#F4545A', negativa: '#DC2626' },
  dark: { principal: '#7c7dcf', secundaria: '#F4545A', negativa: '#e35252' },
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
  },
  dark: {
    rejilla: 'var(--mantine-color-dark-4)',
    eje: 'var(--mantine-color-dark-3)',
    promedio: 'var(--mantine-color-dark-1)',
  },
} as const

/** 'ago 26' desde '2026-08'. El eje no aguanta el año completo con doce meses. */
function rotuloCorto(etiqueta: string): string {
  const [anio, mes] = etiqueta.split('-')
  const nombres = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
  return `${nombres[Number(mes) - 1] ?? mes} ${anio.slice(2)}`
}

const pesos = (v: number) =>
  new Intl.NumberFormat('es-CL', { style: 'currency', currency: 'CLP', maximumFractionDigits: 0 }).format(v)

const millones = (v: number) => (v === 0 ? '0' : `$${(v / 1_000_000).toFixed(1)}M`)

export type SerieDef = {
  campo: keyof MetricasMes
  nombre: string
  /** 'principal' | 'secundaria' | 'negativa' — el rol en la paleta validada. */
  tono: keyof (typeof PALETA)['light']
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
}: {
  titulo: string
  subtitulo?: string
  serie: MetricasMes[]
  /** Una o dos. Con más de dos, el validador de color no da el margen. */
  series: SerieDef[]
  /** El valor de la línea de referencia. Solo se dibuja con una sola serie: con
   *  dos, una línea sola no dice a cuál pertenece. */
  promedio?: number
  esPlata?: boolean
}) {
  const modo = useComputedColorScheme('light')
  const paleta = PALETA[modo]
  const estructura = ESTRUCTURA[modo]

  const datos: Record<string, string | number>[] = serie.map((m) => ({
    mes: rotuloCorto(m.etiqueta),
    ...Object.fromEntries(series.map((s) => [s.campo, Number(m[s.campo])])),
  }))

  const ultimo = datos.length - 1
  const unaSola = series.length === 1
  const ultimoMes =
    unaSola && datos.length > 0
      ? { rotulo: datos[ultimo].mes, valor: Number(datos[ultimo][series[0].campo]) }
      : null
  const formato = esPlata ? pesos : (v: number) => String(v)
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
        {unaSola && ultimoMes && (
          <Text size="xs" c="dimmed">
            <Text span fw={700} c="var(--mantine-color-text)">
              {ultimoMes.rotulo} {formato(ultimoMes.valor)}
            </Text>
            {promedio !== undefined && promedio > 0 && <> · promedio {formato(promedio)}</>}
          </Text>
        )}
        {!unaSola && promedio !== undefined && promedio > 0 && (
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
        <BarChart data={datos} margin={{ top: 18, right: 8, left: 0, bottom: 4 }}>
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
          <Tooltip
            formatter={(valor, nombre) => [formato(Number(valor)), nombre]}
            contentStyle={{ borderRadius: 8, fontSize: 13 }}
          />
          {promedio !== undefined && promedio > 0 && unaSola && (
            <ReferenceLine
              y={promedio}
              stroke={estructura.promedio}
              strokeDasharray="4 4"
              strokeWidth={2}
            />
          )}

          {series.map((s) => (
            <Bar
              key={s.campo}
              dataKey={s.campo}
              name={s.nombre}
              fill={paleta[s.tono]}
              radius={[4, 4, 0, 0]}
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
            </Bar>
          ))}

        </BarChart>
      </ResponsiveContainer>

      {/* La leyenda se dibuja acá y no con el `<Legend>` de Recharts.
          Dejada a la librería salía ordenada por `dataKey` en vez de por el orden
          en que se declaran las series --en canjes se leía "Cancelados ·
          Solicitados", al revés de las barras-- y en la versión 3 ya no acepta un
          `payload` propio para corregirlo. El orden de la leyenda es el que
          explica el gráfico, así que no puede quedar a criterio de la librería. */}
      {!unaSola && (
        <Group gap="lg" justify="center" mt={4}>
          {series.map((s) => (
            <Group key={s.campo} gap={6} wrap="nowrap">
              <span
                aria-hidden
                style={{
                  width: 9,
                  height: 9,
                  borderRadius: '50%',
                  background: paleta[s.tono],
                  display: 'inline-block',
                }}
              />
              <Text size="xs">{s.nombre}</Text>
            </Group>
          ))}
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
  esPlata = false,
}: {
  actual: number
  promedio: number
  /** Cómo se llama lo que se mide, para armar la frase. */
  unidad: string
  esPlata?: boolean
}) {
  const formato = esPlata ? pesos : (v: number) => String(v)

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
    </Text>
  )
}
