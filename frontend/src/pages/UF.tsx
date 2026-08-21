import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Badge,
  Button,
  Center,
  FileButton,
  Group,
  List,
  Loader,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from '@mantine/core'
import { IconCloudDownload, IconDownload, IconHistory, IconUpload } from '@tabler/icons-react'
import {
  actualizarUFDesdeSII,
  cargarHistoriaUF,
  descargarPlantillaUF,
  importarUF,
  obtenerEstadoUF,
  type ResumenCargaUF,
  type ResumenSII,
} from '../api/uf'
import PageHeader from '../components/PageHeader'
import { fecha } from '../components/negociosFormato'

const COLOR_NIVEL: Record<string, string> = {
  ok: 'good',
  aviso: 'warning',
  vencida: 'critical',
  vacia: 'critical',
}

const ETIQUETA_NIVEL: Record<string, string> = {
  ok: 'Al día',
  aviso: 'Por agotarse',
  vencida: 'Vencida',
  vacia: 'Sin cargar',
}

export default function UF() {
  const queryClient = useQueryClient()
  const [archivo, setArchivo] = useState<File | null>(null)
  const [resumen, setResumen] = useState<ResumenCargaUF | null>(null)
  const [resumenSII, setResumenSII] = useState<ResumenSII | null>(null)
  const resetRef = useRef<() => void>(null)

  /** La UF cambia lo que se puede valorizar, así que los negocios también. */
  const refrescar = () => {
    queryClient.invalidateQueries({ queryKey: ['estado-uf'] })
    queryClient.invalidateQueries({ queryKey: ['negocios'] })
    queryClient.invalidateQueries({ queryKey: ['resumen-negocios'] })
  }

  const { data: estado, isLoading } = useQuery({
    queryKey: ['estado-uf'],
    queryFn: obtenerEstadoUF,
  })

  const bajar = useMutation({ mutationFn: descargarPlantillaUF })

  const subir = useMutation({
    mutationFn: () => importarUF(archivo!),
    onSuccess: (r) => {
      setResumen(r)
      setArchivo(null)
      resetRef.current?.()
      refrescar()
    },
  })

  const desdeSII = useMutation({
    mutationFn: actualizarUFDesdeSII,
    onSuccess: (r) => {
      setResumenSII(r)
      refrescar()
    },
  })

  const historia = useMutation({
    mutationFn: cargarHistoriaUF,
    onSuccess: (r) => {
      setResumenSII(r)
      refrescar()
    },
  })

  if (isLoading) {
    return (
      <Center h={200}>
        <Loader />
      </Center>
    )
  }

  return (
    <Stack gap="lg">
      <PageHeader
        title="Unidad de Fomento"
        subtitle="La serie se actualiza sola desde el SII una vez al día. La UF se publica del día 10 al 9 del siguiente, así que siempre hay un tramo por delante."
      />

      {estado && (
        <>
          <SimpleGrid cols={{ base: 1, sm: 3 }}>
            <Paper withBorder radius="md" p="md">
              <Text size="xs" fw={700} c="dimmed">
                ESTADO
              </Text>
              <Group mt={6}>
                <Badge color={COLOR_NIVEL[estado.nivel]} variant="light" size="lg">
                  {ETIQUETA_NIVEL[estado.nivel]}
                </Badge>
              </Group>
            </Paper>
            <Paper withBorder radius="md" p="md">
              <Text size="xs" fw={700} c="dimmed">
                LLEGA HASTA
              </Text>
              <Text size="24px" fw={800} mt={4} lh={1.1}>
                {fecha(estado.ultima)}
              </Text>
              {estado.dias_de_colchon !== null && (
                <Text size="xs" c="dimmed" mt={4}>
                  {estado.dias_de_colchon >= 0
                    ? `${estado.dias_de_colchon} días por delante`
                    : `vencida hace ${Math.abs(estado.dias_de_colchon)} días`}
                </Text>
              )}
            </Paper>
            <Paper withBorder radius="md" p="md">
              <Text size="xs" fw={700} c="dimmed">
                FILAS CARGADAS
              </Text>
              <Text size="24px" fw={800} mt={4} lh={1.1}>
                {estado.filas.toLocaleString('es-CL')}
              </Text>
              {estado.primera && (
                <Text size="xs" c="dimmed" mt={4}>
                  desde {fecha(estado.primera)}
                </Text>
              )}
            </Paper>
          </SimpleGrid>

          {estado.nivel !== 'ok' && (
            <Alert color={COLOR_NIVEL[estado.nivel]} variant="light">
              {estado.mensaje}
            </Alert>
          )}
        </>
      )}

      <Paper withBorder radius="md" p="md">
        <Title order={5} mb={4}>
          Traer del SII
        </Title>
        <Text size="sm" c="dimmed" mb="md">
          Corre solo una vez al día cuando quedan menos de 20 días de serie. Este botón es
          para no esperarlo, cuando el SII acaba de publicar el mes. Traer lo mismo dos
          veces no cambia nada.
        </Text>

        <Group>
          <Button
            color="accent"
            leftSection={<IconCloudDownload size={16} />}
            loading={desdeSII.isPending}
            onClick={() => desdeSII.mutate()}
          >
            Actualizar desde el SII
          </Button>

          <Button
            variant="light"
            leftSection={<IconHistory size={16} />}
            loading={historia.isPending}
            onClick={() => historia.mutate()}
          >
            Traer toda la historia
          </Button>
        </Group>
        <Text size="xs" c="dimmed" mt="xs">
          "Toda la historia" baja un año completo por página, desde 2022. Sirve cuando la
          serie arranca tarde: la actualización diaria solo cubre el año en curso, así que
          por sí sola nunca llenaría los años anteriores.
        </Text>

        {(desdeSII.isError || historia.isError) && (
          <Alert color="critical" variant="light" mt="md" title="El SII no respondió">
            <Text size="sm">{((desdeSII.error ?? historia.error) as Error).message}</Text>
            <Text size="sm" mt="xs">
              No se cargó nada. La salida es descargar la plantilla y cargarla a mano, más
              abajo.
            </Text>
          </Alert>
        )}

        {resumenSII && (
          <Alert color="good" variant="light" mt="md" title="Listo">
            <Text size="sm">
              {resumenSII.fechas_leidas} fechas leídas del SII ({resumenSII.anios.join(', ')}) ·{' '}
              {resumenSII.carga.nuevas} nuevas · {resumenSII.carga.actualizadas} actualizadas ·{' '}
              {resumenSII.carga.sin_cambio} sin cambio
            </Text>
            {resumenSII.carga.nuevas === 0 && resumenSII.carga.actualizadas === 0 && (
              <Text size="sm" c="dimmed" mt={4}>
                El SII no tiene nada más nuevo que lo que ya estaba cargado.
              </Text>
            )}
            {resumenSII.anios_sin_pagina.length > 0 && (
              <Text size="sm" c="dimmed" mt={4}>
                El SII no tiene página para {resumenSII.anios_sin_pagina.join(', ')}. El resto
                se cargó igual.
              </Text>
            )}
          </Alert>
        )}
      </Paper>

      <Paper withBorder radius="md" p="md">
          <Title order={5} mb={4}>
            Cargar a mano
          </Title>
          <Text size="sm" c="dimmed" mb="md">
            El respaldo, para cuando el SII no está disponible o cambió su página. La
            plantilla trae las fechas que faltan ya escritas: solo hay que rellenar los
            valores y subirla.
          </Text>

          <Group>
            <Button
              variant="light"
              leftSection={<IconDownload size={16} />}
              loading={bajar.isPending}
              onClick={() => bajar.mutate()}
            >
              Descargar plantilla
            </Button>

            <FileButton
              resetRef={resetRef}
              onChange={setArchivo}
              accept=".xlsx,.xlsm"
            >
              {(props) => (
                <Button {...props} variant="default">
                  {archivo ? archivo.name : 'Elegir archivo'}
                </Button>
              )}
            </FileButton>

            <Button
              color="accent"
              leftSection={<IconUpload size={16} />}
              disabled={!archivo}
              loading={subir.isPending}
              onClick={() => subir.mutate()}
            >
              Cargar
            </Button>
          </Group>

          {bajar.isError && (
            <Alert color="critical" variant="filled" mt="md">
              {(bajar.error as Error).message}
            </Alert>
          )}
          {subir.isError && (
            <Alert color="critical" variant="filled" mt="md">
              {(subir.error as Error).message}
            </Alert>
          )}

          {resumen && (
            <Alert
              color={resumen.errores.length > 0 ? 'critical' : 'good'}
              variant="light"
              mt="md"
              title={
                resumen.errores.length > 0
                  ? 'No se cargó nada: hay que corregir el archivo'
                  : 'Carga lista'
              }
            >
              <Text size="sm">
                {resumen.nuevas} nuevas · {resumen.actualizadas} actualizadas ·{' '}
                {resumen.sin_cambio} sin cambio
              </Text>
              {resumen.errores.length > 0 && (
                <>
                  <Text size="sm" mt="xs" fw={600}>
                    {resumen.errores.length}{' '}
                    {resumen.errores.length === 1 ? 'problema' : 'problemas'}:
                  </Text>
                  <List size="sm" mt={4}>
                    {resumen.errores.slice(0, 12).map((e) => (
                      <List.Item key={e}>{e}</List.Item>
                    ))}
                  </List>
                  {resumen.errores.length > 12 && (
                    <Text size="xs" c="dimmed" mt={4}>
                      y {resumen.errores.length - 12} más
                    </Text>
                  )}
                </>
              )}
            </Alert>
          )}
      </Paper>
    </Stack>
  )
}
