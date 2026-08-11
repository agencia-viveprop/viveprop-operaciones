import { useQueryClient } from '@tanstack/react-query'
import { Anchor, Button, Center, Stack, Text, Title } from '@mantine/core'
import { Link } from 'react-router-dom'
import { logout, type Usuario } from '../api/auth'

export default function Home({ usuario }: { usuario: Usuario }) {
  const queryClient = useQueryClient()

  return (
    <Center h="100vh">
      <Stack align="center" gap="xs">
        <Title order={2}>Bienvenido, {usuario.nombre}</Title>
        <Text c="dimmed">
          {usuario.email} · rol: {usuario.rol}
        </Text>
        {usuario.rol === 'admin' && <Anchor component={Link} to="/admin/usuarios">Administrar usuarios</Anchor>}
        <Button
          variant="light"
          onClick={async () => {
            await logout()
            queryClient.setQueryData(['me'], null)
          }}
        >
          Salir
        </Button>
      </Stack>
    </Center>
  )
}
