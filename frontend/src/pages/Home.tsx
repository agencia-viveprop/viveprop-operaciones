import { Stack, Text, Title } from '@mantine/core'
import type { Usuario } from '../api/auth'

export default function Home({ usuario }: { usuario: Usuario }) {
  return (
    <Stack gap="xs">
      <Title order={2}>Bienvenido, {usuario.nombre}</Title>
      <Text c="dimmed">
        {usuario.email} · rol: {usuario.rol}
      </Text>
    </Stack>
  )
}
