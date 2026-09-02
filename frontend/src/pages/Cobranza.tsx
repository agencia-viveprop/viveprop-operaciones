import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Group,
  Paper,
  SegmentedControl,
  Stack,
  Table,
  Text,
  Title,
} from '@mantine/core'
import { IconAlertTriangle, IconInfoCircle } from '@tabler/icons-react'
import {
  CLAVE_COBRANZA,
  obtenerCobranza,
  type Cobranza as DatosCobranza,
  type ParteDeCobranza,
  type PlataPorEstado,
} from '../api/obligaciones'
import PageHeader from '../components/PageHeader'
import EstadoConsulta from '../components/EstadoConsulta'
import { clp } from '../components/negociosFormato'

/**
 * Cobranza transversal: todo lo facturable y pagable de los dos mundos.
 *
 * **No hay un total general, y es deliberado.** Los seis conceptos de negocios son
 * dos niveles de la misma plata --la comisión total se reparte entre el corredor
 * aliado y ViveProp, y lo que le queda a ViveProp se reparte otra vez entre el
 * captador, el equipo y la casa--, así que un total general contaría la misma
 * plata dos o tres veces. Cada parte trae el suyo.
 *
 * **Y dentro de cada parte la plata va en tres columnas** --ganado, en curso y no
 * concretado-- porque el resto de la app nunca las suma juntas (`D-063`). Esta
 * pantalla lo había vuelto a hacer: el 38% de la comisión total que mostraba era
 * de negocios perdidos, y el usuario lo detectó comparando con el listado de
 * negocios, que decía otra cifra. Con las tres columnas separadas, más la fila del
 * rebate y el aviso del descuadre, **la tabla se puede comprobar sumando**
 * (`D-095`).
 *
 * La plata de canjes va aparte porque **es de Dataprop**: ViveProp opera el
 * Centro de Canje a nombre de Dataprop y no percibe nada de él (`D-045`).
 */

const COLOR_ESTADO: Record<string, string> = {
  POR_FACTURAR: 'warning',
  FACTURADO: 'info',
  POR_PAGAR: 'serious',
  PAGADO: 'good',
}

/** Los rótulos de los tres destinos, que cambian por dominio: en negocios es la
 *  plata de ViveProp y en canjes la comisión que Dataprop cobra.
 *
 *  **En canjes solo la columna del medio es comisión** (`D-102`): las otras dos se
 *  rotulan por lo que son --lo ya facturado y lo que se perdió con el canje-- para
 *  que no se lean como plata por cobrar. Antes decían «Cobrada / Potencial / No
 *  concretada», tres nombres de comisión para tres poblaciones distintas. */
const ROTULOS = {
  negocios: { logrado: 'Ganado', en_curso: 'En pipeline', no_concretado: 'No concretado' },
  canjes: {
    logrado: 'Ya facturado',
    en_curso: 'Comisión de activos',
    no_concretado: 'No se llegó a cobrar',
  },
} as const

type Medida = 'calculado' | 'registrado'

function Monto({ valor, atenuado }: { valor: number; atenuado?: boolean }) {
  return (
    <Table.Td ta="right" ff="monospace" c={atenuado ? 'dimmed' : undefined}>
      {Number(valor) > 0 ? clp(valor) : '—'}
    </Table.Td>
  )
}

function TablaDePartes({
  partes,
  dominio,
  medida,
  rebate,
}: {
  partes: ParteDeCobranza[]
  dominio: keyof typeof ROTULOS
  medida: Medida
  /** Solo en negocios: el rebate del concentrador, que no es una obligación. */
  rebate?: PlataPorEstado
}) {
  const rotulos = ROTULOS[dominio]
  const plata = (p: ParteDeCobranza) => (medida === 'calculado' ? p.calculado : p.registrado)

  return (
    // Se desplaza dentro de su caja: los rótulos de las partes y las tres
    // columnas de plata no caben en un teléfono, y apretarlos partiría los
    // montos, que es justo lo que no puede pasar con la plata.
    <div className="tabla-scroll-x">
      <Table withRowBorders={false} verticalSpacing={6} miw={720}>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Parte</Table.Th>
            <Table.Th>En qué van</Table.Th>
            <Table.Th ta="right">{rotulos.logrado}</Table.Th>
            <Table.Th ta="right">{rotulos.en_curso}</Table.Th>
            <Table.Th ta="right">{rotulos.no_concretado}</Table.Th>
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
                          Excel, que no traía montos-- la columna ya muestra un
                          guión y repetirlo en cada chip es ruido. */}
                      {t.con_monto > 0 && t.con_monto < t.casos && ` · ${t.con_monto} con monto`}
                    </Badge>
                  ))}
                </Group>
              </Table.Td>
              <Monto valor={plata(p).logrado} />
              <Monto valor={plata(p).en_curso} />
              <Monto valor={plata(p).no_concretado} atenuado />
            </Table.Tr>
          ))}

          {/* El rebate va **fuera de las seis partes y sin estado**: no es algo que
              se facture, es plata que el concentrador comparte con ViveProp. Va
              igual porque entra en la comisión real VP y no sale de ninguna otra
              parte, así que sin esta fila la resta hacia abajo no cierra. Solo en
              la vista de lo calculado: no hay un rebate «registrado». */}
          {rebate && medida === 'calculado' && (
            <Table.Tr>
              <Table.Td>
                <Text size="sm" fw={600} c="dimmed">
                  Rebate del concentrador
                </Text>
                <Text size="xs" c="dimmed">
                  no se factura: entra a la comisión real VP
                </Text>
              </Table.Td>
              <Table.Td />
              <Monto valor={rebate.logrado} atenuado />
              <Monto valor={rebate.en_curso} atenuado />
              <Monto valor={rebate.no_concretado} atenuado />
            </Table.Tr>
          )}
        </Table.Tbody>
      </Table>
    </div>
  )
}

/** El aviso de los repartos que no cuadran. En el histórico es uno --VVP-2, con
 *  $903.803-- y su ficha ya lo dice en rojo; acá hacía falta porque la cobranza
 *  lo sumaba en silencio y la diferencia se leía como un error de la pantalla. */
function AvisoDescuadre({ datos }: { datos: DatosCobranza }) {
  if (datos.descuadres.length === 0) return null
  const total = datos.descuadres.reduce((a, d) => a + Number(d.diferencia), 0)

  return (
    <Alert
      color="critical"
      variant="light"
      icon={<IconAlertTriangle size={18} />}
      title="Hay repartos que no cuadran con su comisión total"
    >
      <Text size="sm">
        {datos.descuadres.length === 1 ? 'Una liquidación suma' : `${datos.descuadres.length} liquidaciones suman`}{' '}
        <Text span fw={700}>
          {clp(Math.abs(total))}
        </Text>{' '}
        de diferencia entre la comisión total y su reparto, así que las filas de esta tabla no
        van a cuadrar exactamente por ese monto. Viene así del Excel y hay que resolverlo en la
        ficha de cada negocio:
      </Text>
      <Text size="sm" mt={4}>
        {datos.descuadres.map((d) => (
          <Text span key={`${d.negocio}-${d.liquidacion ?? ''}`} mr="sm">
            <Text span fw={600}>
              {d.negocio}
            </Text>
            {d.liquidacion ? ` · ${d.liquidacion}` : ''} · {clp(Math.abs(Number(d.diferencia)))}
          </Text>
        ))}
      </Text>
    </Alert>
  )
}

export default function Cobranza() {
  const consulta = useQuery({ queryKey: CLAVE_COBRANZA, queryFn: obtenerCobranza })
  const { data } = consulta

  // Arranca en lo calculado porque es lo que hay: las 114 obligaciones que
  // vinieron del Excel traen estado pero no monto, así que «Registrado» se va a
  // poblar con el uso.
  const [medida, setMedida] = useState<Medida>('calculado')

  const selector = (
    <SegmentedControl
      size="xs"
      value={medida}
      onChange={(v) => setMedida(v as Medida)}
      data={[
        { value: 'calculado', label: 'Calculado' },
        { value: 'registrado', label: 'Registrado' },
      ]}
    />
  )

  return (
    <>
      <PageHeader
        title="Cobranza"
        subtitle="Qué está facturado y qué está pagado, en negocios y en canjes"
        action={data ? selector : undefined}
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
              trae su propio total.
            </Text>
            <Text size="sm" mt={6}>
              <Text span fw={700}>
                Las tres columnas tampoco se suman entre sí.
              </Text>{' '}
              Lo ganado, lo que está en curso y lo que no se concretó son cosas distintas, igual
              que en el listado de Negocios. <Text span fw={600}>Calculado</Text> es lo que dice
              el motor de comisiones; <Text span fw={600}>Registrado</Text>, lo que se facturó o
              se pagó de verdad.
            </Text>
          </Alert>

          <AvisoDescuadre datos={data} />

          <Paper withBorder radius="md" p="md">
            <Group justify="space-between" align="baseline" mb="sm">
              <Title order={4}>Negocios · plata de ViveProp</Title>
              <Text size="xs" c="dimmed">
                {data.liquidaciones_sin_registrar === 0
                  ? 'todas las liquidaciones tienen algo registrado'
                  : `${data.liquidaciones_sin_registrar} liquidación(es) sin nada registrado`}
              </Text>
            </Group>
            <TablaDePartes
              partes={data.negocios}
              dominio="negocios"
              medida={medida}
              rebate={data.rebate}
            />
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
            <TablaDePartes partes={data.canjes} dominio="canjes" medida={medida} />
            <Text size="xs" c="dimmed">
              La comisión de Dataprop es la columna del medio: la de los canjes{' '}
              <strong>activos, en cualquier etapa</strong>. «Ya facturado» es lo que se registró
              al cerrar un canje y «No se llegó a cobrar» es lo de los cancelados; ninguna de las
              dos es plata por cobrar, y las tres no se suman entre sí.
            </Text>
          </Paper>
        </Stack>
      )}
    </>
  )
}
