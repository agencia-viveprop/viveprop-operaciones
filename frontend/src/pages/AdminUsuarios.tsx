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
  Tooltip,
} from '@mantine/core'
import { IconKey } from '@tabler/icons-react'
import {
  actualizarUsuario,
  crearUsuario,
  listarDominios,
  listarUsuarios,
  resetearClave,
  type ClaveReseteada,
  type RolUsuario,
} from '../api/usuarios'
import PageHeader from '../components/PageHeader'
import DominiosOrganizacion from '../components/DominiosOrganizacion'
import { fecha } from '../components/negociosFormato'

const ROLES: { value: RolUsuario; label: string }[] = [
  { value: 'gerencia', label: 'Gerencia' },
  { value: 'operaciones', label: 'Operaciones' },
  { value: 'admin', label: 'Admin' },
]

const dominioDe = (email: string) => email.trim().toLowerCase().split('@')[1] ?? ''

export default function AdminUsuarios() {
  const queryClient = useQueryClient()
  const { data: usuarios, isLoading } = useQuery({ queryKey: ['admin-usuarios'], queryFn: listarUsuarios })
  // La lista de dominios se consulta acá para poder avisar **antes** de mandar el
  // alta. La API igual lo exige: esto no es la guarda, es no hacerle escribir todo
  // el formulario a alguien para después rechazarlo.
  const { data: dominios } = useQuery({ queryKey: ['admin-dominios'], queryFn: listarDominios })
  const [modalAbierto, setModalAbierto] = useState(false)
  const [claveNueva, setClaveNueva] = useState<ClaveReseteada | null>(null)
  const [form, setForm] = useState({ email: '', nombre: '', password: '', rol: 'operaciones' as RolUsuario })
  // Un cambio de correo que la API rechazó por externo, esperando la
  // autorización. Se guarda para poder reenviarlo tal cual.
  const [porAutorizar, setPorAutorizar] = useState<{ id: number; email: string } | null>(null)

  const activos = (dominios ?? []).filter((d) => d.activo).map((d) => d.dominio)
  const esExterno = (email: string) => {
    const dominio = dominioDe(email)
    return dominio.length > 0 && !activos.includes(dominio)
  }
  const nuevoEsExterno = esExterno(form.email)

  const crear = useMutation({
    mutationFn: () => crearUsuario({ ...form, autoriza_externo: nuevoEsExterno }),
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

  /** Cambia el correo, y si la API lo rechaza por externo, ofrece autorizarlo.
   *
   * El aviso sale del rechazo de la API y no de una revisión previa en la
   * pantalla: la celda se edita al salir del campo, así que este es el punto donde
   * de verdad se sabe que el correo nuevo es de fuera. */
  const cambiarEmail = (id: number, email: string) =>
    actualizar
      .mutateAsync({ id, payload: { email } })
      .catch((error: Error) => {
        if (error.message.includes('no es de la organización')) setPorAutorizar({ id, email })
        else throw error
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
                      if (nuevo && nuevo !== u.email) void cambiarEmail(u.id, nuevo)
                    }}
                    w={220}
                  />
                </Table.Td>
                <Table.Td>
                  <Group gap="xs" wrap="nowrap">
                    <Text size="sm">{u.nombre}</Text>
                    {/* Quién autorizó y cuándo, no solo que es externo: cuando
                        alguien pregunte por qué ese correo tiene acceso, la
                        respuesta tiene que estar en la misma fila. */}
                    {u.es_externo && (
                      <Tooltip
                        label={
                          u.externo_autorizado_por
                            ? `Autorizado por ${u.externo_autorizado_por} · ${fecha(u.externo_autorizado_en)}`
                            : `Autorizado el ${fecha(u.externo_autorizado_en)}`
                        }
                      >
                        <Badge variant="default" size="sm">
                          Externo
                        </Badge>
                      </Tooltip>
                    )}
                  </Group>
                </Table.Td>
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

      <DominiosOrganizacion />

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

      <Modal
        opened={porAutorizar !== null}
        onClose={() => setPorAutorizar(null)}
        title="Este correo no es de la organización"
      >
        {porAutorizar && (
          <Stack gap="sm">
            <Text size="sm">
              <strong>{porAutorizar.email}</strong> no pertenece a{' '}
              {activos.length > 0 ? activos.join(' ni a ') : 'ningún dominio de la lista'}. Confirma
              que es un usuario externo y que autorizas su acceso. Va a quedar registrado que lo
              autorizaste tú.
            </Text>
            <Group justify="flex-end">
              <Button variant="default" onClick={() => setPorAutorizar(null)}>
                Cancelar
              </Button>
              <Button
                color="accent"
                loading={actualizar.isPending}
                onClick={() => {
                  actualizar.mutate({
                    id: porAutorizar.id,
                    payload: { email: porAutorizar.email, autoriza_externo: true },
                  })
                  setPorAutorizar(null)
                }}
              >
                Autorizar acceso externo
              </Button>
            </Group>
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
            {/* El aviso aparece mientras se escribe, no después de mandar: la
                decisión se toma con el dato a la vista. Y el botón cambia de
                texto, así que autorizar es un acto y no una casilla que se pasa
                por alto. */}
            {nuevoEsExterno && (
              <Alert color="warning" variant="light" title="Este correo no es de la organización">
                <Text size="sm">
                  <strong>{form.email}</strong> no pertenece a{' '}
                  {activos.length > 0 ? activos.join(' ni a ') : 'ningún dominio de la lista'}.
                  Confirma que es un usuario externo y que autorizas su acceso. Va a quedar
                  registrado que lo autorizaste tú.
                </Text>
              </Alert>
            )}
            {crear.isError && <Alert color="critical" variant="filled">{(crear.error as Error).message}</Alert>}
            <Button type="submit" color="accent" loading={crear.isPending}>
              {nuevoEsExterno ? 'Autorizar acceso externo y crear' : 'Crear'}
            </Button>
          </Stack>
        </form>
      </Modal>
    </Stack>
  )
}
