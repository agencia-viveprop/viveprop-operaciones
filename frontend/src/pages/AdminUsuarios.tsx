import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Group,
  Modal,
  PasswordInput,
  Select,
  Stack,
  Switch,
  Table,
  TextInput,
  Title,
} from '@mantine/core'
import { actualizarUsuario, crearUsuario, listarUsuarios, type RolUsuario } from '../api/usuarios'

const ROLES: { value: RolUsuario; label: string }[] = [
  { value: 'gerencia', label: 'Gerencia' },
  { value: 'operaciones', label: 'Operaciones' },
  { value: 'admin', label: 'Admin' },
]

export default function AdminUsuarios() {
  const queryClient = useQueryClient()
  const { data: usuarios, isLoading } = useQuery({ queryKey: ['admin-usuarios'], queryFn: listarUsuarios })
  const [modalAbierto, setModalAbierto] = useState(false)
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

  return (
    <Stack p="xl" gap="md">
      <Group justify="space-between">
        <Title order={2}>Usuarios</Title>
        <Button onClick={() => setModalAbierto(true)}>Nuevo usuario</Button>
      </Group>

      <Table striped withTableBorder>
        <Table.Thead>
          <Table.Tr>
            <Table.Th>Email</Table.Th>
            <Table.Th>Nombre</Table.Th>
            <Table.Th>Rol</Table.Th>
            <Table.Th>Activo</Table.Th>
          </Table.Tr>
        </Table.Thead>
        <Table.Tbody>
          {!isLoading &&
            usuarios?.map((u) => (
              <Table.Tr key={u.id}>
                <Table.Td>{u.email}</Table.Td>
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
              </Table.Tr>
            ))}
        </Table.Tbody>
      </Table>

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
            {crear.isError && <Alert color="red">{(crear.error as Error).message}</Alert>}
            <Button type="submit" loading={crear.isPending}>
              Crear
            </Button>
          </Stack>
        </form>
      </Modal>
    </Stack>
  )
}
