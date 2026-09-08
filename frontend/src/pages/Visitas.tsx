import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ActionIcon, Button, Group, Table, Text } from '@mantine/core'
import { IconCheck, IconTrash, IconUpload, IconX } from '@tabler/icons-react'
import { CLAVE_VISITAS, eliminarVisita, listarVisitas, type Visita } from '../api/visitas'
import PageHeader from '../components/PageHeader'
import EstadoConsulta from '../components/EstadoConsulta'
import CargaMasivaVisitasModal from '../components/CargaMasivaVisitasModal'

/** Fecha y hora tal como vienen del archivo, en el formato local. `—` cuando
 *  la fila no trae el dato --pasa con "Objetivo de compra" y a veces con la
 *  fecha solicitada. */
function fechaHora(valor: string | null): string {
  if (!valor) return '—'
  return new Date(valor).toLocaleString('es-CL')
}

/** Una fila de la tabla, con su borrado "confirmar en el lugar": mismo patrón
 *  que los movimientos de un canje (`SeguimientoModal`), para no abrir un
 *  modal aparte por cada visita que se quiera sacar. */
function FilaVisita({
  visita,
  puedeEditar,
  onBorrar,
}: {
  visita: Visita
  puedeEditar: boolean
  onBorrar: (id: number) => void
}) {
  const [confirmando, setConfirmando] = useState(false)

  const borrar = useMutation({
    mutationFn: () => eliminarVisita(visita.id),
    onSuccess: () => onBorrar(visita.id),
  })

  return (
    <Table.Tr>
      <Table.Td>{visita.propiedad}</Table.Td>
      <Table.Td>{visita.direccion ?? '—'}</Table.Td>
      <Table.Td>{visita.tipo ?? '—'}</Table.Td>
      <Table.Td>{visita.mercado ?? '—'}</Table.Td>
      <Table.Td>{visita.cliente ?? '—'}</Table.Td>
      <Table.Td>{visita.rut ?? '—'}</Table.Td>
      <Table.Td>{visita.objetivo_compra ?? '—'}</Table.Td>
      <Table.Td>{fechaHora(visita.fecha_solicitada)}</Table.Td>
      <Table.Td>{visita.etapa ?? '—'}</Table.Td>
      <Table.Td>{fechaHora(visita.solicitada_el)}</Table.Td>
      <Table.Td>
        {!puedeEditar ? null : confirmando ? (
          <Group gap={4} wrap="nowrap">
            <ActionIcon
              variant="subtle"
              color="critical"
              size="sm"
              aria-label="Confirmar borrado"
              loading={borrar.isPending}
              onClick={() => borrar.mutate()}
            >
              <IconCheck size={14} />
            </ActionIcon>
            <ActionIcon
              variant="subtle"
              color="gray"
              size="sm"
              aria-label="Cancelar"
              onClick={() => setConfirmando(false)}
            >
              <IconX size={14} />
            </ActionIcon>
          </Group>
        ) : (
          <ActionIcon
            variant="subtle"
            color="critical"
            size="sm"
            aria-label={`Borrar la visita de ${visita.cliente ?? visita.propiedad}`}
            onClick={() => setConfirmando(true)}
          >
            <IconTrash size={14} />
          </ActionIcon>
        )}
      </Table.Td>
    </Table.Tr>
  )
}

export default function Visitas({ puedeEditar }: { puedeEditar: boolean }) {
  const queryClient = useQueryClient()
  const consulta = useQuery({ queryKey: CLAVE_VISITAS, queryFn: listarVisitas })
  const { data } = consulta
  const [cargaAbierta, setCargaAbierta] = useState(false)

  const quitarDeLaLista = (id: number) => {
    queryClient.setQueryData<Visita[]>(CLAVE_VISITAS, (actual) =>
      (actual ?? []).filter((v) => v.id !== id),
    )
  }

  return (
    <>
      <PageHeader
        title="Visitas"
        subtitle="Solicitudes de visita a propiedades, importadas desde la consola"
        action={
          puedeEditar && (
            <Button leftSection={<IconUpload size={16} />} onClick={() => setCargaAbierta(true)}>
              Cargar archivo
            </Button>
          )
        }
      />

      {!data && <EstadoConsulta de={consulta} alto={240} />}

      {data && data.length === 0 && (
        <Text size="sm" c="dimmed">
          Todavía no hay visitas cargadas. Usá "Cargar archivo" para importar el Excel.
        </Text>
      )}

      {data && data.length > 0 && (
        <div className="tabla-scroll-x">
          <Table withRowBorders={false} verticalSpacing={6} miw={1100}>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Propiedad</Table.Th>
                <Table.Th>Dirección</Table.Th>
                <Table.Th>Tipo</Table.Th>
                <Table.Th>Mercado</Table.Th>
                <Table.Th>Cliente</Table.Th>
                <Table.Th>RUT</Table.Th>
                <Table.Th>Objetivo de compra</Table.Th>
                <Table.Th>Fecha/hora solicitada</Table.Th>
                <Table.Th>Etapa</Table.Th>
                <Table.Th>Solicitada el</Table.Th>
                <Table.Th />
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {data.map((v) => (
                <FilaVisita
                  key={v.id}
                  visita={v}
                  puedeEditar={puedeEditar}
                  onBorrar={quitarDeLaLista}
                />
              ))}
            </Table.Tbody>
          </Table>
        </div>
      )}

      <CargaMasivaVisitasModal abierto={cargaAbierta} onCerrar={() => setCargaAbierta(false)} />
    </>
  )
}
