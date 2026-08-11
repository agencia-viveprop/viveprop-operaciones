import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Alert, Button, Center, Paper, PasswordInput, Stack, TextInput, Title } from '@mantine/core'
import { login } from '../api/auth'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: (usuario) => queryClient.setQueryData(['me'], usuario),
  })

  return (
    <Center h="100vh">
      <Paper withBorder shadow="sm" p="xl" radius="md" w={360}>
        <Stack gap="md">
          <Title order={3}>Viveprop Operaciones</Title>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              mutation.mutate()
            }}
          >
            <Stack gap="sm">
              <TextInput
                label="Email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.currentTarget.value)}
              />
              <PasswordInput
                label="Contraseña"
                required
                value={password}
                onChange={(e) => setPassword(e.currentTarget.value)}
              />
              {mutation.isError && <Alert color="critical" variant="filled">{(mutation.error as Error).message}</Alert>}
              <Button type="submit" color="accent" loading={mutation.isPending} fullWidth>
                Ingresar
              </Button>
            </Stack>
          </form>
        </Stack>
      </Paper>
    </Center>
  )
}
