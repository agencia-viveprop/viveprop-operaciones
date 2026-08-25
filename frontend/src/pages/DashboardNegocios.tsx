import { useQuery } from '@tanstack/react-query'
import {
  Alert,
  Group,
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
import NegociosPorMes from '../components/NegociosPorMes'
import { clp, MODELO_CORTO } from '../components/negociosFormato'
import EstadoConsulta from '../components/EstadoConsulta'

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

/** `embebido` lo usa Inicio, que ya puso su propio encabezado: dos títulos
 *  seguidos se leen como un error de maquetación. */
export default function DashboardNegocios({ embebido = false }: { embebido?: boolean }) {
  const esquema = useComputedColorScheme('light')
  const consulta = useQuery({
    queryKey: ['resumen-negocios'],
    queryFn: obtenerResumenNegocios,
  })
  const { data: r } = consulta

  if (!r) return <EstadoConsulta de={consulta} alto={300} />

  const colorSerie = SERIE[esquema]
  const serieMes = aSerie(r.ganado_por_mes)

  // Cuántos negocios están en más de un bucket. Sale de la diferencia y no de
  // una consulta aparte: los buckets ya vienen contados sin duplicar cada uno.
  const repartidos =
    r.ganado.negocios + r.pipeline.negocios + r.potencial_perdido.negocios - r.total_negocios

  const conRebate = (monto: number) =>
    monto > 0 ? `incluye ${clp(monto)} de rebate` : undefined

  return (
    <Stack gap="lg">
      {!embebido && (
        <PageHeader
          title="Dashboard de Negocios"
          subtitle="Los tres montos son plata, pero no la misma plata. No se suman entre sí."
        />
      )}

      <AvisoUF />

      {/* Primero cuántos, después cuánto. Son dos preguntas y hasta ahora la
          primera solo se respondía en la letra chica del pie de cada monto.

          El número grande es de **negocios** y el chico de **liquidaciones**,
          porque en negocios se piensa el ciclo. Las dos unidades van juntas
          porque ninguna reemplaza a la otra: 7 liquidaciones pueden ser 6
          negocios, y ahí "6" y "7" responden cosas distintas. */}
      <SimpleGrid cols={{ base: 1, xs: 2, md: 4 }}>
        <StatCard
          label="Negocios"
          value={r.total_negocios}
          color="gray"
          caption={`${r.total_hitos} ${r.total_hitos === 1 ? 'liquidación' : 'liquidaciones'} en total`}
        />
        <StatCard
          label="Ganados"
          value={r.ganado.negocios}
          color="good"
          caption={
            [
              `${r.ganado.hitos} ${r.ganado.hitos === 1 ? 'liquidación' : 'liquidaciones'}`,
              `${r.tasa_cierre_pct.toFixed(1).replace('.', ',')}% de cierre`,
            ].join(' · ')
          }
        />
        <StatCard
          label="En pipeline"
          value={r.pipeline.negocios}
          color="brand"
          caption={`${r.pipeline.hitos} ${r.pipeline.hitos === 1 ? 'liquidación abierta' : 'liquidaciones abiertas'}`}
        />
        <StatCard
          label="No concretados"
          value={r.potencial_perdido.negocios}
          color="critical"
          caption={`${r.potencial_perdido.hitos} ${r.potencial_perdido.hitos === 1 ? 'liquidación' : 'liquidaciones'}`}
        />
      </SimpleGrid>

      {/* Los tres conteos de negocios pueden sumar más que el total, y no es un
          error: un negocio con la promesa ganada y la escritura abierta está en
          dos buckets a la vez. Se mide en vez de suponerse, y se dice solo
          cuando pasa, para que la resta no quede como un descuadre sin
          explicación. En liquidaciones nunca pasa: cada una tiene un estado. */}
      {repartidos > 0 && (
        <Text size="xs" c="dimmed">
          {repartidos === 1
            ? `1 negocio tiene liquidaciones en estados distintos, así que aparece en más de un recuadro: por eso los tres suman más que ${r.total_negocios}.`
            : `${repartidos} negocios tienen liquidaciones en estados distintos, así que aparecen en más de un recuadro: por eso los tres suman más que ${r.total_negocios}.`}
        </Text>
      )}

      {/* Los tres buckets. Cada tile lleva su etiqueta y su número, así que la
          identidad nunca depende solo del color. */}
      <SimpleGrid cols={{ base: 1, sm: 3 }}>
        <StatCard
          label="Ganado"
          value={clp(r.ganado.comision_real_vp)}
          color="good"
          caption={conRebate(r.ganado.rebate_concentrador)}
        />
        <StatCard
          label="En pipeline"
          value={clp(r.pipeline.comision_real_vp)}
          color="brand"
          caption={conRebate(r.pipeline.rebate_concentrador)}
        />
        <StatCard
          label="Potencial no concretado"
          value={clp(r.potencial_perdido.comision_real_vp)}
          color="critical"
          caption="Liquidaciones perdidas o desistidas"
        />
      </SimpleGrid>

      {r.hitos_sin_valorizar > 0 && (
        <Alert color="warning" variant="light" icon={<IconInfoCircle size={18} />}>
          {r.hitos_sin_valorizar}{' '}
          {r.hitos_sin_valorizar === 1 ? 'liquidación no está valorizada' : 'liquidaciones no están valorizadas'}{' '}
          todavía, así que no aportan a ningún monto de arriba.
        </Alert>
      )}

      {/* Primero cuántos entraron, después cuánto se cobró. Son dos preguntas
          distintas sobre el mismo mes y el orden ayuda a no confundirlas. */}
      <NegociosPorMes />

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
              detalle: `${c.negocios} ${c.negocios === 1 ? 'negocio' : 'negocios'} · ${c.hitos} liq.`,
            }))}
          />
        </Panel>

        <Panel titulo="Ganado por modelo de negocio">
          <BarrasMontos
            color={colorSerie}
            items={r.ganado_por_modelo.map((c) => ({
              etiqueta: MODELO_CORTO[c.etiqueta as keyof typeof MODELO_CORTO] ?? c.etiqueta,
              monto: Number(c.comision_real_vp),
              detalle: `${c.negocios} ${c.negocios === 1 ? 'negocio' : 'negocios'} · ${c.hitos} liq.`,
            }))}
          />
        </Panel>
      </SimpleGrid>

      <Panel
        titulo="Pipeline por etapa"
        ayuda="Cuántos negocios abiertos hay en cada etapa y cuánta comisión potencial está detenida ahí."
      >
        <BarrasMontos
          color={colorSerie}
          items={r.pipeline_por_etapa.map((c) => ({
            etiqueta: c.etiqueta,
            monto: Number(c.comision_real_vp),
            // La cantidad va primero: la pregunta de esta pantalla es dónde se
            // atasca el ciclo, y para eso "3 negocios" dice más que el monto.
            detalle: `${c.negocios} ${c.negocios === 1 ? 'negocio' : 'negocios'} · ${c.hitos} liq.`,
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
