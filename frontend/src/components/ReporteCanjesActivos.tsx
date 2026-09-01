import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Badge,
  Collapse,
  Group,
  Paper,
  SimpleGrid,
  Stack,
  Table,
  Text,
  UnstyledButton,
} from '@mantine/core'
import { IconChevronDown, IconChevronRight } from '@tabler/icons-react'
import {
  obtenerCanjesActivos,
  type FilaCanjeActivo,
  type MovimientoDelListado,
} from '../api/canjes'
import { rotuloCorredor, rotuloEtapa } from './canjesEtiquetas'
import EstadoConsulta from './EstadoConsulta'
import StatCard from './StatCard'

/**
 * Los canjes abiertos, con su estado de gestión y su historial desplegable.
 *
 * **Es un reporte, no una lista de trabajo.** Se pisa a propósito con «Qué me
 * toca hoy» en las filas que muestra, pero contesta otra pregunta: aquella dice
 * qué llamar hoy y ésta dice cómo viene cada canje abierto. Dos consecuencias:
 *
 * - Muestra **todos** los activos, incluso los agendados para adelante que la
 *   bandeja esconde. Un reporte que esconde filas no sirve para saber cuántos
 *   canjes abiertos hay.
 * - Dos estados y no seis. Para "cómo viene" el detalle del semáforo es ruido.
 */

const ESTADOS = {
  pendiente: { texto: 'Pendiente', color: 'critical' },
  al_dia: { texto: 'Al día', color: 'good' },
} as const

/** El tiempo sin gestión, en la unidad que se lee. **Nulo no es cero.** */
function antiguedad(horas: number | null): string {
  if (horas === null) return 'nunca'
  if (horas < 24) return `hace ${Math.round(horas)} h`
  const dias = Math.round(horas / 24)
  return dias === 1 ? 'hace 1 día' : `hace ${dias} días`
}

function fechaCorta(iso: string): string {
  const [a, m, d] = iso.slice(0, 10).split('-')
  return `${d}-${m}-${a}`
}

/** Qué dice el compromiso, si alguien agendó algo. */
function compromiso(fila: FilaCanjeActivo): string | null {
  if (fila.proximo_seguimiento === null || fila.dias_de_atraso === null) return null
  const cuando = fechaCorta(fila.proximo_seguimiento)
  if (fila.dias_de_atraso > 0) {
    return fila.dias_de_atraso === 1
      ? `venció ayer (${cuando})`
      : `venció hace ${fila.dias_de_atraso} días (${cuando})`
  }
  if (fila.dias_de_atraso === 0) return `es para hoy (${cuando})`
  return `agendado para ${cuando}`
}

/**
 * Una línea del historial.
 *
 * El orden de lectura es **qué se hizo, dónde quedó, sobre quién y cuándo**, que
 * es el orden en que uno lo cuenta en voz alta.
 */
function Linea({ m }: { m: MovimientoDelListado }) {
  return (
    <Table.Tr>
      <Table.Td w={110} style={{ whiteSpace: 'nowrap' }}>
        <Text size="xs" ff="monospace">
          {fechaCorta(m.fecha)}
        </Text>
      </Table.Td>
      <Table.Td>
        <Group gap={6} wrap="wrap">
          <Text size="xs" fw={600}>
            {m.tipo_nombre}
          </Text>
          {m.etapa_resultante && (
            <Badge size="xs" variant="light" color="brand">
              {rotuloEtapa(m.etapa_resultante)}
            </Badge>
          )}
          {m.corredor && (
            <Text size="xs" c="dimmed">
              sobre el {rotuloCorredor(m.corredor).toLowerCase()}
            </Text>
          )}
        </Group>
        {/* `prosa` le pone el tope de ancho de lectura: es el texto que alguien
            escribió y puede tener tres renglones. */}
        {m.comentario && (
          <Text size="xs" c="dimmed" mt={2} className="prosa">
            {m.comentario}
          </Text>
        )}
        {/* Solo cuando se registró bastante después de la gestión. No cambia el
            estado del canje --la gestión ocurrió cuando ocurrió-- pero sin esto
            un registro atrasado no se puede distinguir de uno al día. */}
        {m.dias_hasta_el_registro !== null && (
          <Text size="xs" c="dimmed" fs="italic" mt={2}>
            registrado {m.dias_hasta_el_registro} días después
          </Text>
        )}
      </Table.Td>
      <Table.Td w={130} style={{ whiteSpace: 'nowrap' }}>
        <Text size="xs" c="dimmed">
          {m.autor_nombre ?? '—'}
        </Text>
      </Table.Td>
    </Table.Tr>
  )
}

function Historial({ fila }: { fila: FilaCanjeActivo }) {
  const { movimientos } = fila
  if (movimientos.length === 0) {
    return (
      <Text size="xs" c="dimmed" p="sm">
        Este canje todavía no tiene ninguna gestión registrada.
      </Text>
    )
  }
  return (
    <Stack gap={4} p="sm">
      <Text size="xs" c="dimmed">
        {movimientos.length} {movimientos.length === 1 ? 'registro' : 'registros'}, del más
        reciente al más antiguo
        {/* Una vez acá y no en cada línea: los 605 movimientos migrados del Excel
            decían todos «registrado N días después», porque una carga masiva es
            por definición un registro posterior a la gestión. Repetido en las 35
            líneas del historial dejaba de ser una señal. */}
        {fila.registros_de_carga > 0 && fila.fecha_de_carga && (
          <>
            {' · '}
            {fila.registros_de_carga === movimientos.length
              ? 'todos vienen'
              : `${fila.registros_de_carga} vienen`}{' '}
            de la carga del histórico del {fechaCorta(fila.fecha_de_carga)}
          </>
        )}
      </Text>
      <Table withRowBorders={false} verticalSpacing={4} className="detalle-envuelto">
        <Table.Tbody>
          {movimientos.map((m) => (
            <Linea key={m.id} m={m} />
          ))}
        </Table.Tbody>
      </Table>
    </Stack>
  )
}

export default function ReporteCanjesActivos() {
  const consulta = useQuery({ queryKey: ['canjes-activos'], queryFn: obtenerCanjesActivos })
  const { data } = consulta
  // Cuáles están desplegados. Varios a la vez: comparar dos historiales es
  // justamente para lo que uno abre un reporte.
  const [abiertos, setAbiertos] = useState<number[]>([])

  if (!data) {
    return <EstadoConsulta de={consulta} alto={200} vacio="No hay canjes abiertos." />
  }

  const alternar = (id: number) =>
    setAbiertos((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))

  return (
    <Stack gap="md">
      <SimpleGrid cols={{ base: 1, sm: 3 }}>
        <StatCard
          label="Canjes abiertos"
          value={data.filas.length}
          color="gray"
          caption="Activos y sin cerrar"
        />
        <StatCard
          label="Pendientes"
          value={data.pendientes}
          color="critical"
          caption={`Más de ${data.umbral_horas} h sin gestión, o con el seguimiento vencido`}
        />
        <StatCard
          label="Al día"
          value={data.al_dia}
          color="good"
          caption="Gestionados dentro del plazo, o agendados para adelante"
        />
      </SimpleGrid>

      <Text size="xs" c="dimmed">
        El estado se calcula sobre <strong>cuándo se hizo la gestión</strong>, no sobre cuándo
        quedó registrada. Cuando alguien agendó un próximo seguimiento, manda ese compromiso: un
        canje agendado para la semana que viene está al día aunque lleve días sin tocarse.
      </Text>

      <div className="tabla-scroll-x">
        <Table striped withTableBorder highlightOnHover fz="xs" className="tabla-una-linea">
          <Table.Thead>
            <Table.Tr>
              <Table.Th w={30} />
              <Table.Th>N°</Table.Th>
              <Table.Th>Estado</Table.Th>
              <Table.Th>Etapa</Table.Th>
              <Table.Th>Corredores</Table.Th>
              <Table.Th>Comuna</Table.Th>
              <Table.Th ta="right">Última gestión</Table.Th>
              <Table.Th>Próximo seguimiento</Table.Th>
              <Table.Th ta="right">Registros</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {data.filas.map((f) => {
              const abierto = abiertos.includes(f.canje_id)
              const nota = compromiso(f)
              return [
                <Table.Tr key={f.canje_id}>
                  <Table.Td>
                    <UnstyledButton
                      onClick={() => alternar(f.canje_id)}
                      aria-label={abierto ? 'Ocultar el historial' : 'Ver el historial'}
                      aria-expanded={abierto}
                    >
                      {abierto ? <IconChevronDown size={16} /> : <IconChevronRight size={16} />}
                    </UnstyledButton>
                  </Table.Td>
                  <Table.Td fw={600}>{f.canje_id}</Table.Td>
                  <Table.Td>
                    <Badge color={ESTADOS[f.estado].color} variant="light">
                      {ESTADOS[f.estado].texto}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Badge variant="default">{rotuloEtapa(f.etapa)}</Badge>
                  </Table.Td>
                  <Table.Td>
                    <Text size="xs">{f.corredor_solicitante_nombre ?? '—'}</Text>
                    <Text size="xs" c="dimmed">
                      {f.corredor_propietario_nombre ?? '—'}
                    </Text>
                  </Table.Td>
                  <Table.Td>{f.comuna ?? '—'}</Table.Td>
                  <Table.Td ta="right" style={{ whiteSpace: 'nowrap' }}>
                    {antiguedad(f.horas_sin_gestion)}
                  </Table.Td>
                  <Table.Td>
                    {nota ?? (
                      <Text size="xs" c="dimmed">
                        sin agendar
                      </Text>
                    )}
                  </Table.Td>
                  <Table.Td ta="right">{f.movimientos.length}</Table.Td>
                </Table.Tr>,
                /* La fila del historial va siempre en el DOM y se colapsa, en vez
                   de montarse al abrir: así la animación tiene desde dónde
                   crecer y no salta. */
                <Table.Tr key={`${f.canje_id}-historial`}>
                  <Table.Td colSpan={9} p={0} style={{ border: 0 }}>
                    <Collapse expanded={abierto}>
                      <Paper bg="var(--mantine-color-default-hover)" radius={0}>
                        <Historial fila={f} />
                      </Paper>
                    </Collapse>
                  </Table.Td>
                </Table.Tr>,
              ]
            })}
          </Table.Tbody>
        </Table>
      </div>

      {data.filas.length === 0 && (
        <Text size="sm" c="dimmed">
          No hay canjes abiertos.
        </Text>
      )}
    </Stack>
  )
}
