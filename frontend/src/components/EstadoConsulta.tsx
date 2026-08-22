import { Alert, Button, Center, Group, Loader, Stack, Text } from '@mantine/core'
import { IconAlertTriangle, IconRefresh } from '@tabler/icons-react'

/**
 * Lo mínimo que hace falta saber de una consulta para dibujar su estado.
 *
 * Se declara así, y no como el tipo de TanStack Query, para que sirva igual con
 * una consulta o con cinco y no haya que pelear con sus genéricos en cada
 * pantalla.
 */
export type Consulta = {
  isLoading: boolean
  isError: boolean
  error: unknown
  refetch: () => unknown
}

/**
 * Carga, error y vacío de una pantalla que depende de la API.
 *
 * **El problema que resuelve.** Trece pantallas pedían datos y ninguna
 * contemplaba que la petición falle. Salían de dos formas, las dos malas: las
 * que escribían `isLoading || !data ? <Loader/> : ...` dejaban **el spinner
 * girando para siempre** --al fallar, `isLoading` pasa a falso y `data` sigue sin
 * existir--, y las que escribían `if (!data) return null` dejaban **la pantalla
 * en blanco**. En los dos casos la sesión vencida, Neon despertando o un 500 se
 * veían igual que "todavía cargando", sin nada que hacer salvo recargar a ciegas.
 *
 * Se usa cortando el render antes de tocar los datos, que además le da a
 * TypeScript el estrechamiento para que `data` deje de ser opcional:
 *
 * ```tsx
 * const consulta = useQuery({ ... })
 * if (!consulta.data) return <EstadoConsulta de={consulta} alto={300} />
 * // acá `consulta.data` existe
 * ```
 *
 * Con varias consultas se le pasan todas: se muestra el primer error que haya, y
 * reintentar las reintenta todas.
 */
export default function EstadoConsulta({
  de,
  alto = 200,
  vacio = 'No hay datos para mostrar.',
}: {
  de: Consulta | Consulta[]
  /** Alto del área centrada. Conviene el del contenido que reemplaza, para que
   *  la página no salte cuando termina de cargar. */
  alto?: number
  /** Qué decir cuando la API respondió bien y no trajo nada. */
  vacio?: string
}) {
  const consultas = Array.isArray(de) ? de : [de]
  const conError = consultas.find((c) => c.isError)

  if (conError) {
    const mensaje =
      conError.error instanceof Error
        ? conError.error.message
        : 'No se pudo contactar al servidor.'
    return (
      <Center h={alto}>
        <Alert
          color="critical"
          variant="light"
          icon={<IconAlertTriangle size={18} />}
          title="No se pudieron cargar los datos"
          maw={520}
        >
          <Stack gap="xs">
            <Text size="sm">{mensaje}</Text>
            <Text size="xs" c="dimmed">
              Si dice que la sesión venció, hay que entrar de nuevo. Si no, puede ser
              la base despertando: reintentar suele bastar.
            </Text>
            <Group>
              <Button
                size="compact-sm"
                variant="light"
                leftSection={<IconRefresh size={14} />}
                onClick={() => consultas.forEach((c) => c.refetch())}
              >
                Reintentar
              </Button>
            </Group>
          </Stack>
        </Alert>
      </Center>
    )
  }

  if (consultas.some((c) => c.isLoading)) {
    return (
      <Center h={alto}>
        <Loader />
      </Center>
    )
  }

  return (
    <Center h={alto}>
      <Text size="sm" c="dimmed">
        {vacio}
      </Text>
    </Center>
  )
}
