import { useQuery } from '@tanstack/react-query'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Paper, SimpleGrid, Stack, Text, Title } from '@mantine/core'
import { obtenerResumenCanjes } from '../api/reportes'
import StatCard from './StatCard'
import BarList from './BarList'
import EstadoConsulta from './EstadoConsulta'

const ETAPA_COLORS = ['brand.2', 'brand.3', 'brand.4', 'brand.5', 'brand.6', 'brand.7']

/**
 * El dashboard de canjes. Estaba dentro de `Home`; se extrajo cuando Inicio pasó
 * a hospedar los dos dominios, para que el selector alterne entre dos
 * componentes hermanos en vez de entre dos ramas de un archivo largo.
 */
export default function DashboardCanjes() {
  const consulta = useQuery({
    queryKey: ['reportes-canjes-resumen'],
    queryFn: obtenerResumenCanjes,
  })
  const { data: resumen } = consulta

  if (!resumen) return <EstadoConsulta de={consulta} alto={200} />

  return (
    <Stack gap="lg">
      <SimpleGrid cols={{ base: 2, sm: 4 }}>
        <StatCard label="Total canjes" value={resumen.total} color="brand" caption="Histórico" />
        <StatCard label="Activos" value={resumen.activos} color="good" />
        <StatCard label="Cancelados" value={resumen.cancelados} color="critical" />
        <StatCard label="Tasa activos" value={`${resumen.tasa_activos_pct}%`} color="accent" />
      </SimpleGrid>

      <Stack gap="xs">
        <Title order={4}>Canjes por etapa</Title>
        <SimpleGrid cols={{ base: 2, sm: 3, md: 6 }}>
          {resumen.por_etapa.map((e, i) => (
            <StatCard key={e.etiqueta} label={e.etiqueta} value={e.cantidad} color={ETAPA_COLORS[i] ?? 'brand.6'} />
          ))}
        </SimpleGrid>
      </Stack>

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
