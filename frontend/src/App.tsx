import { useQuery } from '@tanstack/react-query'
import { Center, Loader, Stack, Text, Title } from '@mantine/core'

async function fetchHealth() {
  const res = await fetch('/api/health')
  if (!res.ok) throw new Error('backend no disponible')
  return res.json() as Promise<{ status: string }>
}

function App() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
  })

  return (
    <Center h="100vh">
      <Stack align="center" gap="xs">
        <Title order={2}>Viveprop Operaciones</Title>
        {isLoading && <Loader size="sm" />}
        {isError && <Text c="red">Backend no disponible</Text>}
        {data && <Text c="dimmed">Backend: {data.status}</Text>}
      </Stack>
    </Center>
  )
}

export default App
