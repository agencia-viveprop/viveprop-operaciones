import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Group, Paper, SegmentedControl, SimpleGrid, Stack, Text, Title } from '@mantine/core'
import { obtenerResumenCanjes } from '../api/reportes'
import StatCard from './StatCard'
import BarList from './BarList'
import EstadoConsulta from './EstadoConsulta'
import PlataDeCanjes from './PlataDeCanjes'

/** La rampa del pipeline: cuanto mas avanzado, mas oscuro.
 *
 *  Arranca en `brand.3` y no en `brand.2` porque las etapas pasaron de seis a
 *  cinco (`D-081`) y los colores se asignan por posicion: empezando un paso mas
 *  claro, cada etapa que sobrevivio habria cambiado de color sin motivo. Asi las
 *  cinco conservan el que ya tenian. */
const ETAPA_COLORS = ['brand.3', 'brand.4', 'brand.5', 'brand.6', 'brand.7']

/** Qué se cuenta en los tiles de etapa, y de qué campo sale cada opción. */
const VISTAS = [
  { value: 'todos', label: 'Todos', campo: 'cantidad' },
  { value: 'activos', label: 'Activos', campo: 'activos' },
  { value: 'cerrados', label: 'Cerrados', campo: 'cerrados' },
  { value: 'cancelados', label: 'Cancelados', campo: 'cancelados' },
] as const

type Vista = (typeof VISTAS)[number]['value']

/**
 * El dashboard de canjes. Estaba dentro de `Home`; se extrajo cuando Inicio pasó
 * a hospedar los dos dominios, para que el selector alterne entre dos
 * componentes hermanos en vez de entre dos ramas de un archivo largo.
 */
export default function DashboardCanjes() {
  // Arranca en «Todos», que es lo que la pantalla mostraba antes de que existiera
  // el selector: agregar un filtro no debería cambiar lo que uno ya veía.
  //
  // Vale decir que «Activos» es la vista más informativa de las tres: con 293
  // cancelados de 297, el total por etapa es casi el conteo de cancelados y no
  // dice nada sobre lo que hay vivo.
  const [vista, setVista] = useState<Vista>('todos')
  const consulta = useQuery({
    queryKey: ['reportes-canjes-resumen'],
    queryFn: obtenerResumenCanjes,
  })
  const { data: resumen } = consulta

  if (!resumen) return <EstadoConsulta de={consulta} alto={200} />

  const campo = VISTAS.find((v) => v.value === vista)!.campo
  const totalVista = resumen.por_etapa.reduce((a, e) => a + e[campo], 0)

  return (
    <Stack gap="lg">
      <SimpleGrid cols={{ base: 2, sm: 3, lg: 5 }}>
        <StatCard label="Total canjes" value={resumen.total} color="gray" caption="Histórico" />
        <StatCard label="Activos" value={resumen.activos} color="brand" />
        {/* Cero en todo el histórico, y es cierto: el estado no existía y los 31
            que llegaron a la etapa de cierre se cayeron. Va igual, porque un tile
            en cero que dice la verdad informa más que un tile ausente. */}
        <StatCard
          label="Cerrados"
          value={resumen.cerrados}
          color="good"
          caption={`${resumen.tasa_cierre_pct}% de los resueltos`}
        />
        <StatCard label="Cancelados" value={resumen.cancelados} color="critical" />
        <StatCard label="Tasa activos" value={`${resumen.tasa_activos_pct}%`} color="accent" />
      </SimpleGrid>

      <Stack gap="xs">
        <Group justify="space-between" align="baseline" wrap="wrap">
          <Title order={4}>Canjes por etapa</Title>
          <Group gap="sm" align="baseline">
            <SegmentedControl
              size="xs"
              color="accent"
              data={VISTAS.map((v) => ({ value: v.value, label: v.label }))}
              value={vista}
              onChange={(v) => setVista(v as Vista)}
            />
            {/* El total de lo que se está mirando. Sin esto, con «Activos» se ve
                una fila de números chicos y no queda claro cuántos son en total. */}
            <Text size="sm" c="dimmed">
              {totalVista} {totalVista === 1 ? 'canje' : 'canjes'}
            </Text>
          </Group>
        </Group>

        <SimpleGrid cols={{ base: 2, sm: 3, md: 5 }}>
          {resumen.por_etapa.map((e, i) => (
            <StatCard
              key={e.etiqueta}
              label={e.etiqueta}
              value={e[campo]}
              color={ETAPA_COLORS[i] ?? 'brand.6'}
            />
          ))}
        </SimpleGrid>

        {/* Solo aparece cuando de verdad hay una diferencia que explicar. */}
        {vista === 'activos' && resumen.activos_con_etapa_cerrada > 0 && (
          <Text size="xs" c="dimmed">
            {resumen.activos_con_etapa_cerrada}{' '}
            {resumen.activos_con_etapa_cerrada === 1
              ? 'canje está activo con la etapa en Cerrado, así que suma acá'
              : 'canjes están activos con la etapa en Cerrado, así que suman acá'}{' '}
            y no en el recuadro de Activos de arriba.
          </Text>
        )}
      </Stack>

      {/* La plata va despues del volumen: primero cuantos canjes hay y en que
          etapa, despues cuanta comision hay en juego. */}
      <PlataDeCanjes />

      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <Paper withBorder radius="md" p="md">
          <Title order={4} mb="sm">
            Por tipo de inmueble
          </Title>
          <BarList items={resumen.por_tipo_inmueble} color="brand" />
        </Paper>
        <Paper withBorder radius="md" p="md">
          <Title order={4} mb="sm">
            Por operación
          </Title>
          <BarList items={resumen.por_operacion} color="accent" />
        </Paper>
      </SimpleGrid>

      <Paper withBorder radius="md" p="md">
        <Title order={4} mb="sm">
          Solicitudes por mes
        </Title>
        {resumen.por_mes.length === 0 ? (
          <Text size="sm" c="dimmed">
            Sin datos
          </Text>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={resumen.por_mes} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
              <CartesianGrid vertical={false} stroke="var(--mantine-color-gray-2)" />
              <XAxis dataKey="etiqueta" tick={{ fontSize: 12 }} stroke="var(--mantine-color-gray-5)" />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} stroke="var(--mantine-color-gray-5)" />
              <Tooltip
                formatter={(value) => [value, 'Solicitudes']}
                contentStyle={{ borderRadius: 8, fontSize: 13 }}
              />
              <Bar dataKey="cantidad" fill="var(--mantine-color-brand-6)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </Paper>
    </Stack>
  )
}
