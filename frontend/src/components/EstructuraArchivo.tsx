import { useState } from 'react'
import {
  Badge,
  Box,
  Button,
  Code,
  Collapse,
  Group,
  List,
  Stack,
  Table,
  Text,
} from '@mantine/core'
import { IconChevronDown, IconChevronRight } from '@tabler/icons-react'
import type { EstructuraArchivo as Estructura } from '../api/estructura'
import EstadoConsulta from './EstadoConsulta'

/**
 * Qué columnas espera un archivo de carga masiva.
 *
 * **El problema que resuelve.** Las dos cargas pedían un `.xlsx` sin decir en
 * ninguna parte qué columnas esperaban. La de negocios tenía plantilla, así que
 * la respuesta estaba dentro de un archivo que había que bajar y abrir en Excel;
 * la de canjes no tenía ni eso. En los dos casos la única forma de saber si el
 * archivo servía era subirlo y leer los errores.
 *
 * **Va cerrado y no abierto.** Con 32 columnas en negocios, mostrarlas al abrir
 * el modal empuja el botón de cargar fuera de la vista, y quien ya sabe llenar el
 * archivo --que va a ser el caso habitual-- tendría que bajar cada vez. Se abre
 * cuando hace falta.
 *
 * La estructura viene de la API, de la misma definición que pinta la plantilla, así
 * que no puede quedar describiendo columnas que el Excel ya no trae.
 *
 * La consulta la arma quien lo usa, no este componente: así el modal la deja
 * apagada hasta abrirse --es la forma de un archivo, no cambia entre sesiones y no
 * hay razón para traerla al cargar la página--. Y este archivo exporta solo el
 * componente, que es lo que necesita el refresco en caliente de Vite.
 */
export default function EstructuraArchivo({
  consulta,
}: {
  /** El `useQuery` de la estructura. Se recibe armado para que el modal decida
   *  cuándo pedirla --sirve con `enabled`, así que no se consulta hasta abrirse. */
  consulta: {
    data: Estructura | undefined
    isLoading: boolean
    isError: boolean
    error: unknown
    refetch: () => unknown
  }
}) {
  const [abierto, setAbierto] = useState(false)
  const data = consulta.data
  const total = data ? data.grupos.reduce((a, g) => a + g.columnas.length, 0) : null

  return (
    <Box>
      <Button
        variant="subtle"
        size="compact-sm"
        px={4}
        leftSection={
          abierto ? <IconChevronDown size={14} /> : <IconChevronRight size={14} />
        }
        onClick={() => setAbierto((v) => !v)}
      >
        Ver estructura del archivo
        {total !== null && ` (${total} columnas)`}
      </Button>

      <Collapse expanded={abierto}>
        <Box pt="sm">
          {!data ? (
            <EstadoConsulta de={consulta} alto={120} />
          ) : (
            <Stack gap="sm">
              <Text size="sm">
                <Text span fw={600}>De dónde sale: </Text>
                {data.origen}
              </Text>
              <Text size="sm">
                <Text span fw={600}>Qué es una fila: </Text>
                {data.fila}
              </Text>

              <div className="tabla-scroll-x">
                <Table fz="xs" verticalSpacing={4} withTableBorder>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th w={230}>Columna</Table.Th>
                      <Table.Th>Qué va en ella</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {data.grupos.map((grupo) => [
                      // El grupo va como fila de título y no como tabla aparte:
                      // así las dos columnas quedan alineadas de arriba a abajo.
                      <Table.Tr key={grupo.nombre} bg="var(--mantine-color-default-hover)">
                        <Table.Td colSpan={2}>
                          <Text size="xs" fw={700} tt="uppercase">
                            {grupo.nombre}
                          </Text>
                        </Table.Td>
                      </Table.Tr>,
                      ...grupo.columnas.map((col) => (
                        <Table.Tr key={col.nombre}>
                          <Table.Td>
                            <Group gap={6} wrap="nowrap">
                              <Code fz="xs">{col.nombre}</Code>
                              {col.obligatoria && (
                                <Badge size="xs" color="critical" variant="light">
                                  obligatoria
                                </Badge>
                              )}
                            </Group>
                          </Table.Td>
                          <Table.Td>{col.ayuda}</Table.Td>
                        </Table.Tr>
                      )),
                    ])}
                  </Table.Tbody>
                </Table>
              </div>

              {data.valores.length > 0 && (
                <Stack gap={4}>
                  <Text size="xs" fw={700} tt="uppercase" c="dimmed">
                    Valores que se aceptan
                  </Text>
                  {data.valores.map((v) => (
                    <Text size="xs" key={v.columna}>
                      <Code fz="xs">{v.columna}</Code>{' '}
                      {v.valores.length > 0 ? v.valores.join(' · ') : '—'}
                      {v.nota && (
                        <Text span c="dimmed">
                          {' '}
                          {v.nota}
                        </Text>
                      )}
                    </Text>
                  ))}
                </Stack>
              )}

              {data.notas.length > 0 && (
                <Stack gap={4}>
                  <Text size="xs" fw={700} tt="uppercase" c="dimmed">
                    Ojo con esto
                  </Text>
                  <List size="xs" spacing={4}>
                    {data.notas.map((n) => (
                      <List.Item key={n}>{n}</List.Item>
                    ))}
                  </List>
                </Stack>
              )}
            </Stack>
          )}
        </Box>
      </Collapse>
    </Box>
  )
}
