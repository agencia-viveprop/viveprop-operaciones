import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Anchor,
  Button,
  Center,
  Group,
  Paper,
  PasswordInput,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { cambiarClave, logout, type Usuario } from '../api/auth'

/**
 * La pantalla que tapa la app cuando la contraseña es temporal.
 *
 * **No es la que impide usar la app.** Eso lo hace la API: con el flag puesto,
 * todos los endpoints devuelven 403 salvo ver quién soy, cambiar la clave y
 * salir. Esta pantalla existe para que la persona entienda por qué, en vez de
 * chocar contra un error en cada vista.
 *
 * Va sin el menú a propósito: dejarlo sería ofrecer botones que no funcionan.
 * Sí queda la salida, porque quedarse encerrado sin poder cerrar sesión es peor.
 */
export default function CambioForzado({ usuario }: { usuario: Usuario }) {
  const queryClient = useQueryClient()
  const [actual, setActual] = useState('')
  const [nueva, setNueva] = useState('')
  const [confirmar, setConfirmar] = useState('')

  const cambiar = useMutation({
    mutationFn: () => cambiarClave(actual, nueva),
    // Al invalidar, `fetchMe` vuelve sin el flag y la app se muestra completa.
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['me'] }),
  })

  const salir = useMutation({
    mutationFn: logout,
    onSuccess: () => queryClient.setQueryData(['me'], null),
  })

  const noCoinciden = confirmar.length > 0 && nueva !== confirmar
  const igualALaTemporal = nueva.length > 0 && nueva === actual

  return (
    <Center h="100vh">
      <Paper withBorder shadow="sm" p="xl" radius="md" w={420}>
        <Stack gap="md">
          <div>
            <Title order={3}>Elegí tu contraseña</Title>
            <Text size="sm" c="dimmed" mt={4}>
              Tu contraseña actual es temporal: la generó un administrador. Para entrar a la
              app tenés que reemplazarla por una tuya.
            </Text>
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault()
              if (!noCoinciden && !igualALaTemporal) cambiar.mutate()
            }}
          >
            <Stack gap="sm">
              <PasswordInput
                label="Contraseña temporal"
                description="La que te pasaron"
                required
                value={actual}
                onChange={(e) => setActual(e.currentTarget.value)}
              />
              <PasswordInput
                label="Tu contraseña nueva"
                required
                value={nueva}
                onChange={(e) => setNueva(e.currentTarget.value)}
                error={igualALaTemporal ? 'Tiene que ser distinta de la temporal' : undefined}
              />
              <PasswordInput
                label="Repetila"
                required
                value={confirmar}
                onChange={(e) => setConfirmar(e.currentTarget.value)}
                error={noCoinciden ? 'No coincide' : undefined}
              />

              {cambiar.isError && (
                <Alert color="critical" variant="light">
                  {(cambiar.error as Error).message}
                </Alert>
              )}

              <Button
                type="submit"
                color="accent"
                loading={cambiar.isPending}
                disabled={noCoinciden || igualALaTemporal}
              >
                Guardar y entrar
              </Button>
            </Stack>
          </form>

          <Group justify="space-between">
            <Text size="xs" c="dimmed">
              {usuario.email}
            </Text>
            <Anchor size="xs" component="button" type="button" onClick={() => salir.mutate()}>
              Salir
            </Anchor>
          </Group>
        </Stack>
      </Paper>
    </Center>
  )
}
