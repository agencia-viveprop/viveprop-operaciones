import { useQuery } from '@tanstack/react-query'
import { Alert, Badge, Group, Paper, Stack, Table, Text, Title } from '@mantine/core'
import { IconInfoCircle } from '@tabler/icons-react'
import {
  CLAVE_COBRANZA,
  obtenerCobranza,
  type ParteDeCobranza,
} from '../api/obligaciones'
import PageHeader from '../components/PageHeader'
import EstadoConsulta from '../components/EstadoConsulta'
import { clp } from '../components/negociosFormato'

/**
 * Cobranza transversal: todo lo facturable y pagable de los dos mundos.
 *
 * **No hay un gran total, y es deliberado.** Los seis conceptos de negocios son
 * dos niveles de la misma plata --la comisión total se reparte entre el corredor
 * aliado y ViveProp, y lo que le queda a ViveProp se reparte otra vez entre el
 * captador, el equipo y la casa--, así que un total general contaría la misma
 * plata dos o tres veces. Cada parte trae el suyo.
 *
 * Y la plata de canjes va aparte porque **es de Dataprop**: ViveProp opera el
 * Centro de Canje a nombre de Dataprop y no percibe nada de él (`D-045`).
 */

const COLOR_ESTADO: Record<string, string> = {
  POR_FACTURAR: 'warning',
  FACTURADO: 'info',
  POR_PAGAR: 'serious',
  PAGADO: 'good',
}

function TablaDePartes({ partes }: { partes: ParteDeCobranza[] }) {
  return (
    <Table withRowBorders={false} verticalSpacing={6}>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>Parte</Table.Th>
          <Table.Th>En qué van</Table.Th>
          <Table.Th ta="right">Registrado</Table.Th>
          <Table.Th ta="right">Calculado</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {partes.map((p) => (
          <Table.Tr key={p.tipo}>
            <Table.Td>
              <Text size="sm" fw={600}>
                {p.rotulo}
              </Text>
              <Text size="xs" c="dimmed">
                {p.casos === 0 ? 'nada registrado' : `${p.casos} registrada(s)`}
              </Text>
            </Table.Td>
            <Table.Td>
              <Group gap={6} wrap="wrap">
                {p.tramos.length === 0 && (
                  <Text size="xs" c="dimmed">
                    —
                  </Text>
                )}
                {p.tramos.map((t) => (
                  <Badge
                    key={t.estado_codigo ?? 'sin-estado'}
                    color={COLOR_ESTADO[t.estado_codigo ?? ''] ?? 'gray'}
                    variant="light"
                    size="sm"
                  >
                    {t.estado_nombre ?? 'sin estado'} · {t.casos}
                    {/* Solo cuando **algunos** tienen monto: ahí el registrado
                        parece bajo y hay que decir que está incompleto. Si no
                        tiene ninguno --el caso de las 114 filas que vinieron del
                        Excel, que no traía montos-- la columna «Registrado» ya
                        muestra un guión y repetirlo en cada chip es ruido. */}
                    {t.con_monto > 0 && t.con_monto < t.casos && ` · ${t.con_monto} con monto`}
                  </Badge>
                ))}
              </Group>
            </Table.Td>
            <Table.Td ta="right" ff="monospace">
              {p.monto_registrado > 0 ? clp(p.monto_registrado) : '—'}
            </Table.Td>
            <Table.Td ta="right" ff="monospace" c="dimmed">
              {p.monto_esperado > 0 ? clp(p.monto_esperado) : '—'}
            </Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  )
}

export default function Cobranza() {
  const consulta = useQuery({ queryKey: CLAVE_COBRANZA, queryFn: obtenerCobranza })
  const { data } = consulta

  return (
    <>
      <PageHeader
        title="Cobranza"
        subtitle="Qué está facturado y qué está pagado, en negocios y en canjes"
      />

      {!data && <EstadoConsulta de={consulta} alto={240} />}

      {data && (
        <Stack gap="lg">
          <Alert variant="light" color="brand" icon={<IconInfoCircle size={18} />}>
            <Text size="sm">
              <Text span fw={700}>
                No hay un total general, y es a propósito.
              </Text>{' '}
              Las seis partes de un negocio son dos niveles de la misma plata: la comisión total
              se reparte entre el corredor aliado y ViveProp, y lo que le queda a ViveProp se
              reparte otra vez. Sumarlas contaría la misma plata dos veces, así que cada parte
              trae su propio total. <Text span fw={600}>Registrado</Text> es lo que se facturó o
              se pagó de verdad; <Text span fw={600}>calculado</Text> es lo que dice el motor de
              comisiones.
            </Text>
          </Alert>

          <Paper withBorder radius="md" p="md">
            <Group justify="space-between" align="baseline" mb="sm">
              <Title order={4}>Negocios · plata de ViveProp</Title>
              <Text size="xs" c="dimmed">
                {data.liquidaciones_sin_registrar === 0
                  ? 'todas las liquidaciones tienen algo registrado'
                  : `${data.liquidaciones_sin_registrar} liquidación(es) sin nada registrado`}
              </Text>
            </Group>
            <TablaDePartes partes={data.negocios} />
          </Paper>

          <Paper withBorder radius="md" p="md">
            <Group justify="space-between" align="baseline" mb="sm">
              <Title order={4}>Canjes · plata de Dataprop</Title>
              <Text size="xs" c="dimmed">
                {data.canjes_sin_registrar === 0
                  ? 'todos los canjes tienen algo registrado'
                  : `${data.canjes_sin_registrar} canje(s) sin nada registrado`}
              </Text>
            </Group>
            <Text size="sm" c="dimmed" mb="sm">
              ViveProp opera el Centro de Canje a nombre de Dataprop y no percibe nada de él.
              Esta plata no se suma nunca con la de negocios.
            </Text>
            <TablaDePartes partes={data.canjes} />
          </Paper>
        </Stack>
      )}
    </>
  )
}
