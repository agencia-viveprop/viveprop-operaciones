import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Button,
  Code,
  CopyButton,
  Group,
  Modal,
  PasswordInput,
  Select,
  Stack,
  Switch,
  Table,
  Text,
  TextInput,
} from '@mantine/core'
import { IconKey } from '@tabler/icons-react'
import {
  actualizarUsuario,
  crearUsuario,
  listarUsuarios,
  resetearClave,
  type ClaveReseteada,
  type RolUsuario,
} from '../api/usuarios'
import PageHeader from '../components/PageHeader'

const ROLES: { value: RolUsuario; label: string }[] = [
  { value: 'gerencia', label: 'Gerencia' },
  { value: 'operaciones', label: 'Operaciones' },
  { value: 'admin', label: 'Admin' },
]

export default function AdminUsuarios() {
  const queryClient = useQueryClient()
  const { data: usuarios, isLoading } = useQuery({ queryKey: ['admin-usuarios'], queryFn: listarUsuarios })
  const [modalAbierto, setModalAbierto] = useState(false)
  const [claveNueva, setClaveNueva] = useState<ClaveReseteada | null>(null)
  const [form, setForm] = useState({ email: '', nombre: '', password: '', rol: 'operaciones' as RolUsuario })

  const crear = useMutation({
    mutationFn: () => crearUsuario(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-usuarios'] })
      setModalAbierto(false)
      setForm({ email: '', nombre: '', password: '', rol: 'operaciones' })
    },
  })

  const actualizar = useMutation({
    mutationFn: (vars: { id: number; payload: Parameters<typeof actualizarUsuario>[1] }) =>
      actualizarUsuario(vars.id, vars.payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-usuarios'] }),
  })

  const resetear = useMutation({
    mutationFn: resetearClave,
    onSuccess: (r) => {
      setClaveNueva(r)
      queryClient.invalidateQueries({ queryKey: ['admin-usuarios'] })
    },
  })

  return (
    <Stack p="xl" gap="md">
      <PageHeader title="Usuarios" action={<Button color="accent" onClick={() => setModalAbierto(true)}>Nuevo usuario</Button>} />

      {actualizar.isError && <Alert color="critical" variant="filled">{(actualizar.error as Error).message}</Alert>}

      <Table striped withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Email</Table.Th>
            <Table.Th>Nombre</Table.Th>
            <Table.Th>Rol</Table.Th>
            <Table.Th>Activo</Table.Th>
            <Table.Th>Contraseña</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {!isLoading &&
            usuarios?.map((u) => (
              <Table.Tr key={u.id}>
                <Table.Td>
                  <TextInput
                    defaultValue={u.email}
                    onBlur={(e) => {
                      const nuevo = e.currentTarget.value.trim()
                      if (nuevo && nuevo !== u.email) actualizar.mutate({ id: u.id, payload: { email: nuevo } })
                    }}
                    w={220}
                  />
                </Table.Td>
                <Table.Td>{u.nombre}</Table.Td>
                <Table.Td>
                  <Select
                    data={ROLES}
                    value={u.rol}
                    onChange={(value) => value && actualizar.mutate({ id: u.id, payload: { rol: value as RolUsuario } })}
                    w={160}
                  />
                </Table.Td>
                <Table.Td>
                  <Switch
                    checked={u.activo}
                    onChange={(e) => actualizar.mutate({ id: u.id, payload: { activo: e.currentTarget.checked } })}
                  />
                </Table.Td>
                <Table.Td>
                  <Group gap="xs" wrap="nowrap">
                    <Button
                      size="xs"
                      variant="light"
                      leftSection={<IconKey size={14} />}
                      loading={resetear.isPending && resetear.variables === u.id}
                      onClick={() => resetear.mutate(u.id)}
                    >
                      Resetear
                    </Button>
                    {u.debe_cambiar_password && (
                      <Badge color="warning" variant="light" size="sm">
                        Temporal
                      </Badge>
                    )}
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
        </Table.Tbody>
      </Table>

      {resetear.isError && (
        <Alert color="critical" variant="light">
          {(resetear.error as Error).message}
        </Alert>
      )}

      {/* La temporal se muestra una sola vez: lo que queda guardado es su hash.
          Si se cierra sin copiarla, hay que resetear de nuevo. */}
      <Modal
        opened={claveNueva !== null}
        onClose={() => setClaveNueva(null)}
        title="Contraseña temporal"
      >
        {claveNueva && (
          <Stack gap="sm">
            <Text size="sm">
              Pasale esta contraseña a <strong>{claveNueva.email}</strong>. Al entrar, la app
              le va a pedir que elija una propia; hasta que lo haga no puede hacer nada más.
            </Text>
            <Group>
              <Code fz="md" style={{ letterSpacing: 1 }}>
                {claveNueva.clave_temporal}
              </Code>
              <CopyButton value={claveNueva.clave_temporal}>
                {({ copied, copy }) => (
                  <Button size="xs" variant={copied ? 'filled' : 'light'} onClick={copy}>
                    {copied ? 'Copiada' : 'Copiar'}
                  </Button>
                )}
              </CopyButton>
            </Group>
            <Alert color="warning" variant="light">
              Se muestra una sola vez. Sus sesiones abiertas ya se cerraron.
            </Alert>
          </Stack>
        )}
      </Modal>

      <Modal opened={modalAbierto} onClose={() => setModalAbierto(false)} title="Nuevo usuario">
        <form
          onSubmit={(e) => {
            e.preventDefault()
            crear.mutate()
          }}
        >
          <Stack gap="sm">
            <TextInput
              label="Email"
              type="email"
              required
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.currentTarget.value })}
            />
            <TextInput
              label="Nombre"
              required
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.currentTarget.value })}
            />
            <PasswordInput
              label="Contraseña"
              required
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.currentTarget.value })}
            />
            <Select
              label="Rol"
              data={ROLES}
              value={form.rol}
              onChange={(value) => value && setForm({ ...form, rol: value as RolUsuario })}
            />
            {crear.isError && <Alert color="critical" variant="filled">{(crear.error as Error).message}</Alert>}
            <Button type="submit" color="accent" loading={crear.isPending}>
              Crear
            </Button>
          </Stack>
        </form>
      </Modal>
    </Stack>
  )
}
