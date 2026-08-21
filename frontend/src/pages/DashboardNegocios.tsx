import { useQuery } from '@tanstack/react-query'
import {
  Alert,
  Center,
  Group,
  Loader,
  Paper,
  SimpleGrid,
  Stack,
  Table,
  Text,
  Title,
  useComputedColorScheme,
} from '@mantine/core'
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { IconInfoCircle } from '@tabler/icons-react'
import { obtenerResumenNegocios, type Corte } from '../api/negocios'
import AvisoUF from '../components/AvisoUF'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import BarrasMontos from '../components/BarrasMontos'
import { clp, MODELO_CORTO } from '../components/negociosFormato'

/**
 * Paleta validada con el script de la guía de visualización, sobre las rampas
 * de `theme.ts`. No se eligió a ojo:
 *
 * - Serie única de los gráficos: brand-6 en claro, brand-4 en oscuro. Cada uno
 *   pasa las seis comprobaciones contra su propia superficie. El oscuro no es un
 *   volteo automático del claro: los tonos claros de la rampa de marca se
 *   construyeron como fondos y pierden croma, así que hubo que elegir otro paso.
 * - Estados de los tiles: verde, indigo y rojo. La primera opción —verde, teal y
 *   rojo— quedaba a ΔE 2,8 en tritanopía entre el verde y el teal, o sea
 *   prácticamente iguales. Con el indigo el peor caso sube a 18,8.
 */
const SERIE = { light: 'var(--mantine-color-brand-6)', dark: 'var(--mantine-color-brand-4)' }

/** Un mes con su monto, como lo consume Recharts. */
function aSerie(cortes: Corte[]) {
  return cortes.map((c) => ({
    mes: c.etiqueta,
    real: Number(c.comision_real_vp),
    total: Number(c.comision_total),
    hitos: c.hitos,
  }))
}

function TooltipMes({ active, payload }: { active?: boolean; payload?: { payload: ReturnType<typeof aSerie>[number] }[] }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <Paper withBorder radius="sm" p="xs" shadow="sm">
      <Text size="sm" fw={600} mb={4}>
        {d.mes}
      </Text>
      <Text size="xs">
        Comisión real VP: <Text span fw={600} ff="monospace">{clp(d.real)}</Text>
      </Text>
      <Text size="xs" c="dimmed">
        Comisión total: {clp(d.total)}
      </Text>
      <Text size="xs" c="dimmed">
        {d.hitos} {d.hitos === 1 ? 'liquidación' : 'liquidaciones'}
      </Text>
    </Paper>
  )
}

function Panel({ titulo, ayuda, children }: { titulo: string; ayuda?: string; children: React.ReactNode }) {
  return (
    <Paper withBorder radius="md" p="md">
      <Title order={5} mb={ayuda ? 2 : 'sm'}>
        {titulo}
      </Title>
      {ayuda && (
        <Text size="xs" c="dimmed" mb="sm">
          {ayuda}
        </Text>
      )}
      {children}
    </Paper>
  )
}

export default function DashboardNegocios() {
  const esquema = useComputedColorScheme('light')
  const { data: r, isLoading } = useQuery({
    queryKey: ['resumen-negocios'],
    queryFn: obtenerResumenNegocios,
  })

  if (isLoading) {
    return (
      <Center h={300}>
        <Loader />
      </Center>
    )
  }
  if (!r) return null

  const colorSerie = SERIE[esquema]
  const serieMes = aSerie(r.ganado_por_mes)

  const conRebate = (monto: number) =>
    monto > 0 ? `incluye ${clp(monto)} de rebate` : undefined

  return (
    <Stack gap="lg">
      <PageHeader
        title="Dashboard de Negocios"
        subtitle="Los tres montos son plata, pero no la misma plata. No se suman entre sí."
      />

      <AvisoUF />

      {/* Los tres buckets. Cada tile lleva su etiqueta y su número, así que la
          identidad nunca depende solo del color. */}
      <SimpleGrid cols={{ base: 1, sm: 3 }}>
        <StatCard
          label="Ganado"
          value={clp(r.ganado.comision_real_vp)}
          color="good"
          caption={
            [
              `${r.ganado.hitos} liquidaciones en ${r.ganado.negocios} negocios`,
              conRebate(r.ganado.rebate_concentrador),
            ]
              .filter(Boolean)
              .join(' · ')
          }
        />
        <StatCard
          label="En pipeline"
          value={clp(r.pipeline.comision_real_vp)}
          color="brand"
          caption={
            [
              `${r.pipeline.hitos} liquidaciones abiertas`,
              conRebate(r.pipeline.rebate_concentrador),
            ]
              .filter(Boolean)
              .join(' · ')
          }
        />
        <StatCard
          label="Potencial no concretado"
          value={clp(r.potencial_perdido.comision_real_vp)}
          color="critical"
          caption={`${r.potencial_perdido.hitos} liquidaciones perdidas o desistidas`}
        />
      </SimpleGrid>

      {r.hitos_sin_valorizar > 0 && (
        <Alert color="warning" variant="light" icon={<IconInfoCircle size={18} />}>
          {r.hitos_sin_valorizar}{' '}
          {r.hitos_sin_valorizar === 1 ? 'liquidación no está valorizada' : 'liquidaciones no están valorizadas'}{' '}
          todavía, así que no aportan a ningún monto de arriba.
        </Alert>
      )}

      <Panel
        titulo="Comisión real ViveProp por mes de cierre"
        ayuda="Solo lo ganado. El mes es el de cierre, no el de inicio: importa cuándo entró la plata."
      >
        {serieMes.length === 0 ? (
          <Text size="sm" c="dimmed">
            Todavía no hay liquidaciones cerradas.
          </Text>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={serieMes} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                <CartesianGrid vertical={false} stroke="var(--mantine-color-default-border)" />
                <XAxis
                  dataKey="mes"
                  tick={{ fontSize: 12, fill: 'var(--mantine-color-dimmed)' }}
                  stroke="var(--mantine-color-default-border)"
                />
                <YAxis
                  tick={{ fontSize: 12, fill: 'var(--mantine-color-dimmed)' }}
                  stroke="var(--mantine-color-default-border)"
                  tickFormatter={(v) => `${Math.round(Number(v) / 1_000_000)}M`}
                  width={44}
                />
                <Tooltip content={<TooltipMes />} cursor={{ fill: 'var(--mantine-color-default-hover)' }} />
                <Bar dataKey="real" fill={colorSerie} radius={[4, 4, 0, 0]} maxBarSize={56} />
              </BarChart>
            </ResponsiveContainer>

            {/* Los mismos datos en tabla: el gráfico no es la única forma de leerlos. */}
            <Table.ScrollContainer minWidth={420} mt="sm">
              <Table withRowBorders={false} verticalSpacing={4} fz="sm">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Mes</Table.Th>
                    <Table.Th ta="right">Liquidaciones</Table.Th>
                    <Table.Th ta="right">Comisión total</Table.Th>
                    <Table.Th ta="right">Real VP</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {serieMes.map((m) => (
                    <Table.Tr key={m.mes}>
                      <Table.Td>{m.mes}</Table.Td>
                      <Table.Td ta="right">{m.hitos}</Table.Td>
                      <Table.Td ta="right" ff="monospace" c="dimmed">{clp(m.total)}</Table.Td>
                      <Table.Td ta="right" ff="monospace" fw={600}>{clp(m.real)}</Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Table.ScrollContainer>
          </>
        )}
      </Panel>

      <SimpleGrid cols={{ base: 1, md: 2 }}>
        <Panel titulo="Ganado por alianza" ayuda="Comisión real ViveProp de las liquidaciones cerradas.">
          <BarrasMontos
            color={colorSerie}
            items={r.ganado_por_alianza.map((c) => ({
              etiqueta: c.etiqueta,
              monto: Number(c.comision_real_vp),
              detalle: `${c.hitos} liq.`,
            }))}
          />
        </Panel>

        <Panel titulo="Ganado por modelo de negocio">
          <BarrasMontos
            color={colorSerie}
            items={r.ganado_por_modelo.map((c) => ({
              etiqueta: MODELO_CORTO[c.etiqueta as keyof typeof MODELO_CORTO] ?? c.etiqueta,
              monto: Number(c.comision_real_vp),
              detalle: `${c.hitos} liq.`,
            }))}
          />
        </Panel>
      </SimpleGrid>

      <Panel
        titulo="Pipeline por etapa"
        ayuda="Dónde está detenido cada negocio abierto, y cuánta comisión hay ahí."
      >
        <BarrasMontos
          color={colorSerie}
          items={r.pipeline_por_etapa.map((c) => ({
            etiqueta: c.etiqueta,
            monto: Number(c.comision_real_vp),
            detalle: `${c.hitos} liq.`,
          }))}
        />
      </Panel>

      <Group justify="center">
        <Text size="xs" c="dimmed" ta="center" maw={560}>
          El potencial no concretado se conserva a propósito: saber cuánto se dejó de ganar
          sirve para analizar. Pero no es plata que entró, así que no se suma con lo ganado.
        </Text>
      </Group>
    </Stack>
  )
}
