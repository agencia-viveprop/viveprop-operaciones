import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Button, Center, Loader, Stack, Text, Title } from '@mantine/core'
import { fetchMe, logout } from './api/auth'
import Login from './pages/Login'

function App() {
  const queryClient = useQueryClient()
  const { data: usuario, isLoading } = useQuery({
    queryKey: ['me'],
    queryFn: fetchMe,
    retry: false,
  })

  if (isLoading) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    )
  }

  if (!usuario) {
    return <Login />
  }

  return (
    <Center h="100vh">
      <Stack align="center" gap="xs">
        <Title order={2}>Bienvenido, {usuario.nombre}</Title>
        <Text c="dimmed">
          {usuario.email} · rol: {usuario.rol}
        </Text>
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

export default App
