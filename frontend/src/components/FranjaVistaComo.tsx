import { useState } from 'react'
import { Button, Group, Paper, Text } from '@mantine/core'
import { IconEye } from '@tabler/icons-react'
import { dejarDeVerComo, type Usuario } from '../api/auth'

const ROTULO_ROL: Record<Usuario['rol'], string> = {
  gerencia: 'Gerencia',
  operaciones: 'Operaciones',
  admin: 'Admin',
}

/**
 * La franja de «Estás viendo como…», fija arriba en todas las pantallas
 * (`D-120`).
 *
 * Tiene que estar siempre a la vista: la pantalla es idéntica a la del otro
 * usuario, así que sin ella el admin podría olvidar que está en una vista y
 * creer que le faltan permisos o datos.
 *
 * Volver recarga la página entera en vez de invalidar consultas: todo lo que hay
 * en caché se pidió como el otro usuario, y una recarga es la forma de no dejar
 * ni una pantalla con esos datos.
 */
export default function FranjaVistaComo({ usuario }: { usuario: Usuario }) {
  const [volviendo, setVolviendo] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!usuario.vista_de_admin) return null

  const volver = async () => {
    setVolviendo(true)
    setError(null)
    try {
      await dejarDeVerComo()
      window.location.assign('/admin/usuarios')
    } catch (e) {
      setError((e as Error).message)
      setVolviendo(false)
    }
  }

  return (
    <Paper
      radius={0}
      px="md"
      py="xs"
      bg="warning.1"
      c="dark.8"
      style={{
        position: 'sticky',
        // Debajo de la cabecera fija del teléfono; en PC la cabecera no existe y
        // la variable vale cero.
        top: 'var(--app-shell-header-offset, 0px)',
        zIndex: 150,
        borderBottom: '1px solid var(--mantine-color-warning-4)',
        // De borde a borde: se come el relleno de `AppShell.Main` para no quedar
        // como una tarjeta más del contenido.
        marginInline: 'calc(var(--app-shell-padding) * -1)',
        marginTop: 'calc(var(--app-shell-padding) * -1)',
        marginBottom: 'var(--mantine-spacing-md)',
      }}
    >
      <Group justify="space-between" gap="xs" wrap="wrap">
        <Group gap="xs" wrap="nowrap">
          <IconEye size={18} style={{ flexShrink: 0 }} />
          <Text size="sm">
            Estás viendo la app como <strong>{usuario.nombre}</strong> ({ROTULO_ROL[usuario.rol]}). Es
            solo para mirar: no se puede guardar nada.
          </Text>
        </Group>
        <Group gap="xs">
          {error && (
            <Text size="xs" c="critical.7">
              {error}
            </Text>
          )}
          <Button size="xs" color="dark" loading={volviendo} onClick={volver}>
            Volver a mi usuario
          </Button>
        </Group>
      </Group>
    </Paper>
  )
}
