import { Fragment, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Collapse,
  Group,
  NumberInput,
  Select,
  Stack,
  Table,
  Text,
  TextInput,
  Tooltip,
} from '@mantine/core'
import { IconHistory, IconPencil, IconPlus } from '@tabler/icons-react'
import { obtenerCatalogos } from '../api/catalogos'
import {
  CIRCUITO,
  CLAVE_COBRANZA,
  claveObligacionesCanje,
  claveObligacionesHito,
  listarObligacionesCanje,
  listarObligacionesHito,
  registrarObligacionCanje,
  registrarObligacionHito,
  type AvanceNuevo,
  type Obligacion,
} from '../api/obligaciones'
import { clp } from './negociosFormato'

/**
 * Facturación y pago de una liquidación o de un canje.
 *
 * **Las partes se muestran siempre, registradas o no.** Una parte que nadie tocó
 * es información --«esto falta»-- y omitirla haría que la tabla dependiera de lo
 * que ya se registró: una liquidación recién cerrada se vería vacía y no habría
 * dónde hacer el primer registro.
 *
 * **El monto calculado queda a la vista al lado del registrado.** El calculado
 * sale del motor de comisiones y el registrado es lo que efectivamente se facturó
 * o se pagó; la diferencia entre los dos es el ajuste, y esconderla sería
 * perderla. El formulario llega prellenado con el calculado, que es el caso
 * habitual, y se puede corregir.
 */

/** El color dice en qué va, sin tener que leer. Los «No Aplica» van en gris:
 *  son un cierre, no un pendiente. */
const COLOR_ESTADO: Record<string, string> = {
  POR_FACTURAR: 'warning',
  FACTURADO: 'info',
  POR_PAGAR: 'serious',
  PAGADO: 'good',
}

function colorDe(codigo: string | null): string {
  if (!codigo) return 'gray'
  return COLOR_ESTADO[codigo] ?? 'gray'
}

/** Hoy en formato `yyyy-mm-dd`, para prellenar la fecha.
 *
 *  `toISOString()` no sirve: devuelve UTC, así que en Chile antes de las 21:00
 *  daría el día siguiente. */
function hoyLocal(): string {
  const d = new Date()
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10)
}

function fechaCorta(iso: string | null): string {
  if (!iso) return '—'
  return new Date(`${iso}T12:00:00`).toLocaleDateString('es-CL')
}

type Dominio =
  | { tipo: 'negocio'; negocioId: number; hitoId: number }
  | { tipo: 'canje'; canjeId: number }

function Formulario({
  obligacion,
  estados,
  onGuardar,
  onCancelar,
  guardando,
}: {
  obligacion: Obligacion
  estados: { value: string; label: string }[]
  onGuardar: (cuerpo: AvanceNuevo) => void
  onCancelar: () => void
  guardando: boolean
}) {
  // Prellenado con lo vigente y, si no hay nada, con lo calculado: el camino
  // habitual --facturar lo que el motor dice-- no pide escribir un número.
  const [estadoId, setEstadoId] = useState<string | null>(
    obligacion.estado_id ? String(obligacion.estado_id) : null,
  )
  const [monto, setMonto] = useState<string>(
    String(obligacion.monto ?? obligacion.monto_esperado ?? ''),
  )
  const [fecha, setFecha] = useState<string>(obligacion.fecha ?? hoyLocal())

  return (
    <Stack gap="xs" p="sm">
      <Group gap="sm" align="flex-end" wrap="wrap">
        <Select
          label="Estado"
          data={estados}
          value={estadoId}
          onChange={setEstadoId}
          w={{ base: '100%', sm: 180 }}
          searchable
          required
        />
        <NumberInput
          label="Monto"
          description="El calculado, o lo que se facturó de verdad"
          value={monto === '' ? undefined : Number(monto)}
          onChange={(v) => setMonto(String(v ?? ''))}
          thousandSeparator="."
          decimalSeparator=","
          hideControls
          w={{ base: '100%', sm: 200 }}
        />
        <TextInput
          label="Fecha"
          type="date"
          value={fecha}
          onChange={(e) => setFecha(e.currentTarget.value)}
          w={{ base: '100%', sm: 160 }}
        />
        <Button
          size="sm"
          loading={guardando}
          disabled={!estadoId}
          onClick={() =>
            onGuardar({
              tipo: obligacion.tipo,
              estado_id: Number(estadoId),
              // Vacío es nulo y no cero: «facturado, todavía sin monto conocido»
              // es una situación real.
              monto: monto === '' ? null : Number(monto),
              fecha: fecha || null,
            })
          }
        >
          Guardar
        </Button>
        <Button size="sm" variant="default" onClick={onCancelar}>
          Cancelar
        </Button>
      </Group>
      {obligacion.monto_esperado !== null && (
        <Text size="xs" c="dimmed">
          Calculado por el motor de comisiones: {clp(obligacion.monto_esperado)}. Se puede
          corregir; queda registrado que se modificó.
        </Text>
      )}
    </Stack>
  )
}

export default function Obligaciones({
  dominio,
  puedeEditar,
  /** Un texto por tipo para agregar al rótulo. En canjes son los nombres de los
   *  dos corredores: «Facturación corredor solicitante» a secas obliga a
   *  recordar quién es. */
  detalles,
}: {
  dominio: Dominio
  puedeEditar: boolean
  detalles?: Record<string, string | null | undefined>
}) {
  const queryClient = useQueryClient()
  const [editando, setEditando] = useState<string | null>(null)
  const [historia, setHistoria] = useState<string | null>(null)

  const clave =
    dominio.tipo === 'negocio'
      ? claveObligacionesHito(dominio.negocioId, dominio.hitoId)
      : claveObligacionesCanje(dominio.canjeId)

  const { data: catalogos } = useQuery({ queryKey: ['catalogos'], queryFn: obtenerCatalogos })
  const { data: obligaciones, isLoading } = useQuery({
    queryKey: clave,
    queryFn: () =>
      dominio.tipo === 'negocio'
        ? listarObligacionesHito(dominio.negocioId, dominio.hitoId)
        : listarObligacionesCanje(dominio.canjeId),
  })

  const registrar = useMutation({
    mutationFn: (cuerpo: AvanceNuevo) =>
      dominio.tipo === 'negocio'
        ? registrarObligacionHito(dominio.negocioId, dominio.hitoId, cuerpo)
        : registrarObligacionCanje(dominio.canjeId, cuerpo),
    onSuccess: (filas) => {
      // El POST devuelve la tabla completa, así que se escribe directo en la
      // caché en vez de reconsultar: la respuesta ya es el estado nuevo.
      queryClient.setQueryData(clave, filas)
      // La cobranza transversal suma estas filas, así que queda vieja.
      queryClient.invalidateQueries({ queryKey: CLAVE_COBRANZA })
      setEditando(null)
    },
  })

  // Solo los estados de facturación, en el orden del circuito y con los demás
  // --los «No Aplica» y los que venían del Excel-- después.
  const estados = (catalogos?.estados_facturacion ?? [])
    .slice()
    .sort((a, b) => {
      const ia = CIRCUITO.indexOf(a.codigo)
      const ib = CIRCUITO.indexOf(b.codigo)
      return (ia < 0 ? CIRCUITO.length : ia) - (ib < 0 ? CIRCUITO.length : ib)
    })
    .map((c) => ({ value: String(c.id), label: c.nombre }))

  if (isLoading) return <Text size="sm" c="dimmed">Cargando facturación...</Text>

  return (
    <Stack gap="xs">
      {registrar.isError && (
        <Alert color="critical" variant="light">
          {(registrar.error as Error).message}
        </Alert>
      )}

      <Table withRowBorders={false} verticalSpacing={4} horizontalSpacing="xs">
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Parte</Table.Th>
            <Table.Th w={120}>Estado</Table.Th>
            <Table.Th w={110} ta="right">Registrado</Table.Th>
            <Table.Th w={110} ta="right">Calculado</Table.Th>
            <Table.Th w={100}>Fecha</Table.Th>
            <Table.Th w={70} />
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {(obligaciones ?? []).map((o) => {
            const detalle = detalles?.[o.tipo]
            const ajustada =
              o.monto !== null &&
              o.monto_esperado !== null &&
              Math.abs(Number(o.monto) - Number(o.monto_esperado)) > 1
            return (
              <Fragment key={o.tipo}>
                <Table.Tr>
                  <Table.Td>
                    <Text size="sm">{o.rotulo}</Text>
                    {detalle && (
                      <Text size="xs" c="dimmed">
                        {detalle}
                      </Text>
                    )}
                  </Table.Td>
                  <Table.Td>
                    {o.registrada ? (
                      <Badge color={colorDe(o.estado_codigo)} variant="light">
                        {o.estado_nombre}
                      </Badge>
                    ) : (
                      <Text size="xs" c="dimmed">
                        sin registrar
                      </Text>
                    )}
                  </Table.Td>
                  <Table.Td ta="right" ff="monospace">
                    {ajustada ? (
                      <Tooltip label={`Ajustado: el motor calcula ${clp(o.monto_esperado)}`}>
                        <Text size="sm" ff="monospace" c="warning" fw={600} span>
                          {clp(o.monto)}
                        </Text>
                      </Tooltip>
                    ) : (
                      clp(o.monto)
                    )}
                  </Table.Td>
                  <Table.Td ta="right" ff="monospace" c="dimmed">
                    {clp(o.monto_esperado)}
                  </Table.Td>
                  <Table.Td>
                    <Text size="sm" c="dimmed" style={{ whiteSpace: 'nowrap' }}>
                      {fechaCorta(o.fecha)}
                    </Text>
                  </Table.Td>
                  <Table.Td>
                    <Group gap={4} justify="flex-end" wrap="nowrap">
                      {o.avances.length > 0 && (
                        <Tooltip label={`${o.avances.length} registro(s)`}>
                          <ActionIcon
                            variant="subtle"
                            size="sm"
                            aria-label={`Historia de ${o.rotulo}`}
                            onClick={() => setHistoria(historia === o.tipo ? null : o.tipo)}
                          >
                            <IconHistory size={14} />
                          </ActionIcon>
                        </Tooltip>
                      )}
                      {puedeEditar && (
                        <Tooltip label={o.registrada ? 'Registrar un avance' : 'Registrar'}>
                          <ActionIcon
                            variant="subtle"
                            size="sm"
                            aria-label={`Registrar ${o.rotulo}`}
                            onClick={() => setEditando(editando === o.tipo ? null : o.tipo)}
                          >
                            {o.registrada ? <IconPencil size={14} /> : <IconPlus size={14} />}
                          </ActionIcon>
                        </Tooltip>
                      )}
                    </Group>
                  </Table.Td>
                </Table.Tr>
                <Table.Tr>
                  <Table.Td colSpan={6} p={0}>
                    <Collapse expanded={editando === o.tipo}>
                      <Formulario
                        obligacion={o}
                        estados={estados}
                        guardando={registrar.isPending}
                        onGuardar={(cuerpo) => registrar.mutate(cuerpo)}
                        onCancelar={() => setEditando(null)}
                      />
                    </Collapse>
                    <Collapse expanded={historia === o.tipo}>
                      <Stack gap={2} p="sm">
                        {/* Del más reciente al más antiguo, como el resto de los
                            historiales de la app. */}
                        {o.avances.map((a) => (
                          <Text size="xs" c="dimmed" key={a.id}>
                            {new Date(a.creado_en).toLocaleString('es-CL')} ·{' '}
                            <Text span fw={600}>
                              {a.estado_nombre ?? 'sin estado'}
                            </Text>
                            {a.monto !== null && ` · ${clp(a.monto)}`}
                            {a.fecha && ` · ${fechaCorta(a.fecha)}`}
                            {a.autor && ` · ${a.autor}`}
                          </Text>
                        ))}
                      </Stack>
                    </Collapse>
                  </Table.Td>
                </Table.Tr>
              </Fragment>
            )
          })}
        </Table.Tbody>
      </Table>
    </Stack>
  )
}
