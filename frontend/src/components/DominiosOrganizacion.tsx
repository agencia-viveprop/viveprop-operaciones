import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ActionIcon,
  Alert,
  Badge,
  Button,
  Group,
  Paper,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
  Tooltip,
} from '@mantine/core'
import { IconTrash } from '@tabler/icons-react'
import { agregarDominio, desactivarDominio, listarDominios } from '../api/usuarios'

/**
 * Los dominios de correo de la organización, administrables por un admin.
 *
 * **Qué hace esta lista y qué no.** Los correos de estos dominios se crean sin
 * preguntar nada. Cualquier otro correo **también se puede usar** --un director o
 * un advisor tiene el correo que tiene-- pero pide que el admin lo autorice en el
 * momento, y ese acto queda con nombre y fecha en la ficha del usuario. Así dejar
 * entrar a una persona no obliga a abrir su dominio entero: habilitar `gmail.com`
 * para un advisor habría dejado la lista sin significado y con apariencia de
 * control.
 *
 * Antes esto vivía en una variable de entorno de Render, con dos problemas: había
 * que salir de la app para dar un acceso, y **vacío significaba «sin
 * restricción»**, así que borrarla por error abría la aplicación en silencio.
 * Ahora vacío es lo más cerrado que hay: todo correo pide autorización.
 */
export default function DominiosOrganizacion() {
  const queryClient = useQueryClient()
  const { data: dominios } = useQuery({ queryKey: ['admin-dominios'], queryFn: listarDominios })
  const [nuevo, setNuevo] = useState({ dominio: '', nombre: '' })

  const invalidar = () => {
    queryClient.invalidateQueries({ queryKey: ['admin-dominios'] })
    // El formulario de alta de usuarios decide con esta lista si el correo es
    // externo, así que tiene que enterarse del cambio.
    queryClient.invalidateQueries({ queryKey: ['admin-usuarios'] })
  }

  const agregar = useMutation({
    mutationFn: () =>
      agregarDominio({ dominio: nuevo.dominio, nombre: nuevo.nombre || undefined }),
    onSuccess: () => {
      setNuevo({ dominio: '', nombre: '' })
      invalidar()
    },
  })

  const quitar = useMutation({ mutationFn: desactivarDominio, onSuccess: invalidar })

  const activos = (dominios ?? []).filter((d) => d.activo)

  return (
    <Paper withBorder radius="md" p="md">
      <Stack gap="sm">
        <div>
          <Title order={4}>Dominios de la organización</Title>
          <Text size="sm" c="dimmed">
            Los correos de estos dominios se crean sin preguntar. Cualquier otro correo se puede usar
            igual, pero hay que autorizarlo como externo al crear el usuario, y queda registrado quién
            lo autorizó.
          </Text>
        </div>

        {/* Que la lista quede vacía no abre la app: la cierra. Se dice, porque el
            comportamiento contrario --el de la variable de entorno que esto
            reemplaza-- es el que uno esperaría por costumbre. */}
        {dominios && activos.length === 0 && (
          <Alert color="warning" variant="light">
            No hay dominios en la lista, así que <strong>todo correo nuevo pide autorización
            explícita</strong>. No es un bloqueo: se pueden seguir creando usuarios, uno por uno y
            autorizando cada uno.
          </Alert>
        )}

        {activos.length > 0 && (
          <Table striped withTableBorder fz="sm">
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Dominio</Table.Th>
                <Table.Th>Para qué</Table.Th>
                <Table.Th w={60} />
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {activos.map((d) => (
                <Table.Tr key={d.id}>
                  <Table.Td fw={600}>{d.dominio}</Table.Td>
                  <Table.Td>{d.nombre === d.dominio ? '—' : d.nombre}</Table.Td>
                  <Table.Td>
                    {/* Quitar un dominio **no le saca el acceso a nadie**: la lista
                        se aplica al crear un usuario o al cambiarle el correo. Para
                        cortar un acceso está el switch de arriba. El tooltip lo
                        dice, porque el botón parece hacer más de lo que hace. */}
                    <Tooltip
                      label="Deja de aceptarse para usuarios nuevos. No le quita el acceso a nadie que ya lo tenga."
                      multiline
                      w={260}
                    >
                      <ActionIcon
                        variant="subtle"
                        color="critical"
                        aria-label={`Quitar ${d.dominio}`}
                        loading={quitar.isPending && quitar.variables === d.id}
                        onClick={() => quitar.mutate(d.id)}
                      >
                        <IconTrash size={16} />
                      </ActionIcon>
                    </Tooltip>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        )}

        {/* Los que se quitaron quedan a la vista, apagados: así se ve que alguien
            los sacó a propósito y no que nunca estuvieron. */}
        {(dominios ?? []).some((d) => !d.activo) && (
          <Group gap="xs">
            <Text size="xs" c="dimmed">
              Quitados:
            </Text>
            {(dominios ?? [])
              .filter((d) => !d.activo)
              .map((d) => (
                <Badge key={d.id} variant="default" size="sm">
                  {d.dominio}
                </Badge>
              ))}
          </Group>
        )}

        <form
          onSubmit={(e) => {
            e.preventDefault()
            agregar.mutate()
          }}
        >
          <Group gap="xs" align="flex-end">
            <TextInput
              label="Agregar dominio"
              placeholder="dataprop.cl"
              description="Se puede pegar un correo completo: se guarda solo el dominio."
              value={nuevo.dominio}
              onChange={(e) => setNuevo({ ...nuevo, dominio: e.currentTarget.value })}
              w={260}
            />
            <TextInput
              label="Para qué (opcional)"
              placeholder="Dataprop"
              value={nuevo.nombre}
              onChange={(e) => setNuevo({ ...nuevo, nombre: e.currentTarget.value })}
              w={200}
            />
            <Button type="submit" variant="light" loading={agregar.isPending} disabled={!nuevo.dominio.trim()}>
              Agregar
            </Button>
          </Group>
        </form>

        {agregar.isError && (
          <Alert color="critical" variant="light">
            {(agregar.error as Error).message}
          </Alert>
        )}
        {quitar.isError && (
          <Alert color="critical" variant="light">
            {(quitar.error as Error).message}
          </Alert>
        )}
      </Stack>
    </Paper>
  )
}
