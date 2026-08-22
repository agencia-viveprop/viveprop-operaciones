import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Center,
  Group,
  Loader,
  Paper,
  Select,
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
import { obtenerCatalogos } from '../api/catalogos'
import { obtenerNegociosPorMes } from '../api/negocios'
import { clp, MODELO_CORTO } from './negociosFormato'

/** El mismo par que usa el dashboard de negocios: cada tono se validó contra su
 *  propia superficie, y el oscuro no es un volteo automático del claro. */
const SERIE = { light: 'var(--mantine-color-brand-6)', dark: 'var(--mantine-color-brand-4)' }

type Punto = { mes: string; negocios: number; real: number }

function TooltipMes({ active, payload }: { active?: boolean; payload?: { payload: Punto }[] }) {
  if (!active || !payload?.length) return null
  const d = payload[0].payload
  return (
    <Paper withBorder radius="sm" p="xs" shadow="sm">
      <Text size="sm" fw={600}>
        {d.mes}
      </Text>
      <Text size="sm">
        {d.negocios} {d.negocios === 1 ? 'negocio' : 'negocios'}
      </Text>
      {/* La comisión va como dato secundario: el gráfico mide cuántos entraron,
          no cuánto se cobró. Mezclar las dos escalas en un eje sería el error
          del gráfico de doble eje. */}
      <Text size="xs" c="dimmed">
        {clp(d.real)} de comisión real hasta hoy
      </Text>
    </Paper>
  )
}

/**
 * Negocios por mes, el equivalente de "solicitudes por mes" en canjes.
 *
 * **Mide cuánto entró, no cuánto se cobró.** Agrupa por fecha de inicio, y un
 * negocio cae en el mes de su hito más antiguo: `VVP-3` tiene promesa y
 * escritura en meses distintos y es un negocio, no dos. Lo cobrado ya está en el
 * gráfico de comisión por mes del mismo dashboard, que agrupa por cierre y
 * responde otra pregunta.
 *
 * **Incluye los perdidos.** Un negocio que se cayó igual entró ese mes; sacarlo
 * haría que el pasado se encogiera cada vez que algo se pierde.
 */
export default function NegociosPorMes() {
  const esquema = useComputedColorScheme('light')
  const [modelo, setModelo] = useState<string | null>(null)
  const [operacion, setOperacion] = useState<string | null>(null)

  const { data: catalogos } = useQuery({ queryKey: ['catalogos'], queryFn: obtenerCatalogos })
  const { data, isLoading } = useQuery({
    queryKey: ['negocios-por-mes', modelo, operacion],
    queryFn: () => obtenerNegociosPorMes({ modelo, tipo_operacion: operacion }),
  })

  const serie: Punto[] =
    data?.meses.map((m) => ({
      mes: m.etiqueta,
      negocios: m.negocios,
      real: Number(m.comision_real_vp),
    })) ?? []

  const filtrado = modelo !== null || operacion !== null

  return (
    <Paper withBorder radius="md" p="md">
      <Group justify="space-between" align="flex-start" mb="sm" wrap="wrap">
        <div>
          <Title order={5}>Negocios por mes</Title>
          <Text size="xs" c="dimmed">
            Cuándo entró cada negocio, por su hito más antiguo. Incluye los perdidos.
          </Text>
        </div>
        <Group gap="xs">
          <Select
            size="xs"
            w={170}
            placeholder="Todos los mercados"
            value={modelo}
            onChange={setModelo}
            clearable
            // Los modelos salen del catálogo, no de una lista escrita acá: es
            // la misma regla que el resto de los desplegables de la app.
            data={(catalogos?.modelos_negocio ?? []).map((c) => ({
              value: c.codigo,
              label: MODELO_CORTO[c.codigo as keyof typeof MODELO_CORTO] ?? c.nombre,
            }))}
          />
          <Select
            size="xs"
            w={150}
            placeholder="Toda operación"
            value={operacion}
            onChange={setOperacion}
            clearable
            data={(catalogos?.tipos_operacion ?? []).map((c) => ({
              value: c.codigo,
              label: c.nombre,
            }))}
          />
        </Group>
      </Group>

      {isLoading ? (
        <Center h={260}>
          <Loader size="sm" />
        </Center>
      ) : serie.length === 0 ? (
        <Center h={260}>
          <Text size="sm" c="dimmed">
            {filtrado
              ? 'Ningún negocio con esos filtros.'
              : 'Todavía no hay negocios cargados.'}
          </Text>
        </Center>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={serie} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
              <CartesianGrid vertical={false} stroke="var(--mantine-color-gray-2)" />
              <XAxis dataKey="mes" tick={{ fontSize: 12 }} stroke="var(--mantine-color-gray-5)" />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} stroke="var(--mantine-color-gray-5)" />
              <Tooltip content={<TooltipMes />} />
              <Bar dataKey="negocios" fill={SERIE[esquema]} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
          <Group justify="space-between" align="flex-start" mt={4}>
            {/* La advertencia va acá y no en un tooltip: cambia cómo se lee el
                gráfico, no es un detalle. Y desaparece sola cuando el número
                llega a cero, o sea cuando todos los negocios tengan fecha de
                inicio de verdad. */}
            {(data?.con_inicio_aproximado ?? 0) > 0 ? (
              <Text size="xs" c="dimmed" maw={430}>
                Ojo: {data?.con_inicio_aproximado} de {data?.total_negocios} vienen del Excel
                con la fecha de inicio igual a la de cierre, porque el origen traía una sola.
                Esos caen en el mes en que cerraron, no en el que empezaron.
              </Text>
            ) : (
              <span />
            )}
            <Text size="xs" c="dimmed" ta="right">
              {data?.total_negocios} {data?.total_negocios === 1 ? 'negocio' : 'negocios'}
              {filtrado && ' con los filtros aplicados'}
            </Text>
          </Group>
        </>
      )}
    </Paper>
  )
}
