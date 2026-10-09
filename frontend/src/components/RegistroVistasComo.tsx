import { useQuery } from '@tanstack/react-query'
import { Paper, Stack, Table, Text, Title } from '@mantine/core'
import { listarVistasComo } from '../api/usuarios'
import EstadoConsulta from './EstadoConsulta'

function fechaHora(iso: string): string {
  return new Date(iso).toLocaleString('es-CL', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Quién vio la app como quién, y cuándo (`D-120`).
 *
 * Gerencia incluye a usuarios de Dataprop: tiene que quedar a la vista que un
 * admin entró a mirar como ellos. Un registro sin término no es un error: la
 * sesión venció sin que el admin volviera a su usuario, y no se sabe cuándo dejó
 * de mirar.
 */
export default function RegistroVistasComo() {
  const consulta = useQuery({ queryKey: ['admin-vistas-como'], queryFn: listarVistasComo })
  const { data } = consulta

  return (
    <Paper withBorder radius="md" p="md">
      <Stack gap="sm">
        <div>
          <Title order={4}>Registro de «Ver como»</Title>
          <Text size="sm" c="dimmed">
            Cada vez que un admin vio la app como otro usuario. Se muestran las últimas 50.
          </Text>
        </div>
        {!data ? (
          <EstadoConsulta de={consulta} alto={80} />
        ) : data.length === 0 ? (
          <Text size="sm" c="dimmed">
            Nadie ha usado «Ver como» todavía.
          </Text>
        ) : (
          <div className="tabla-scroll-x">
            <Table withTableBorder fz="sm" className="tabla-una-linea">
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Admin</Table.Th>
                  <Table.Th>Vio como</Table.Th>
                  <Table.Th>Desde</Table.Th>
                  <Table.Th>Hasta</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {data.map((v) => (
                  <Table.Tr key={v.id}>
                    <Table.Td>{v.admin ?? 'Cuenta borrada'}</Table.Td>
                    <Table.Td>{v.usuario ?? 'Cuenta borrada'}</Table.Td>
                    <Table.Td>{fechaHora(v.inicio)}</Table.Td>
                    <Table.Td c={v.fin ? undefined : 'dimmed'}>
                      {v.fin ? fechaHora(v.fin) : 'Sin registro de término'}
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </div>
        )}
      </Stack>
    </Paper>
  )
}
