import { useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  FileButton,
  Group,
  List,
  Modal,
  Stack,
  Text,
} from '@mantine/core'
import { IconDownload, IconUpload } from '@tabler/icons-react'
import {
  descargarPlantillaNegocios,
  importarNegocios,
  type ResumenCargaNegocios,
} from '../api/negocios'

/** Cuántos errores se listan antes de resumir. Con un archivo muy malo salen
 *  cientos, y una lista de cientos no se lee: se corrigen los primeros y se
 *  vuelve a subir. */
const TOPE_ERRORES = 15

/**
 * Carga masiva de negocios.
 *
 * Los dos pasos van en el mismo lugar a propósito: bajar la plantilla y subirla
 * son el mismo trabajo partido en dos, y separarlos obliga a buscar dónde
 * estaba el otro.
 *
 * La plantilla trae los códigos válidos leídos de la base, así que no hay que
 * adivinar si la alianza se escribe `ASSETPLAN` o `Assetplan`.
 */
export default function CargaMasivaModal({
  abierto,
  onCerrar,
}: {
  abierto: boolean
  onCerrar: () => void
}) {
  const queryClient = useQueryClient()
  const [archivo, setArchivo] = useState<File | null>(null)
  const [resumen, setResumen] = useState<ResumenCargaNegocios | null>(null)
  const resetRef = useRef<() => void>(null)

  const bajar = useMutation({ mutationFn: descargarPlantillaNegocios })

  const subir = useMutation({
    mutationFn: () => importarNegocios(archivo!),
    onSuccess: (r) => {
      setResumen(r)
      setArchivo(null)
      resetRef.current?.()
      if (r.errores.length === 0) {
        queryClient.invalidateQueries({ queryKey: ['negocios'] })
        queryClient.invalidateQueries({ queryKey: ['resumen-negocios'] })
      }
    },
  })

  const cerrar = () => {
    setResumen(null)
    setArchivo(null)
    resetRef.current?.()
    onCerrar()
  }

  const cargado = resumen !== null && resumen.errores.length === 0

  return (
    <Modal opened={abierto} onClose={cerrar} title="Carga masiva de negocios" size="lg">
      <Stack gap="md">
        <Text size="sm" c="dimmed">
          Una fila es un hito. Si repetís el código, agregás otro hito al mismo negocio. Las
          comisiones no se escriben: las calcula el sistema con el valor y las tasas.
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

          <FileButton resetRef={resetRef} onChange={setArchivo} accept=".xlsx,.xlsm">
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
          <Alert color="critical" variant="light">
            {(bajar.error as Error).message}
          </Alert>
        )}
        {subir.isError && (
          <Alert color="critical" variant="light" title="El archivo no se pudo leer">
            {(subir.error as Error).message}
          </Alert>
        )}

        {resumen && (
          <Alert
            color={cargado ? 'good' : 'critical'}
            variant="light"
            title={cargado ? 'Carga lista' : 'No se cargó nada: hay que corregir el archivo'}
          >
            {cargado ? (
              <Text size="sm">
                {resumen.negocios_nuevos} negocios nuevos · {resumen.negocios_actualizados}{' '}
                actualizados · {resumen.hitos_nuevos} hitos nuevos ·{' '}
                {resumen.hitos_actualizados} hitos actualizados
              </Text>
            ) : (
              <>
                <Text size="sm">
                  {/* Se dice explícito que la base quedó intacta: con una lista
                      larga de errores, lo primero que uno se pregunta es si
                      cargó algo a medias. */}
                  {resumen.errores.length}{' '}
                  {resumen.errores.length === 1 ? 'problema' : 'problemas'}. La base quedó
                  igual que antes, no se escribió nada.
                </Text>
                <List size="sm" mt="xs">
                  {resumen.errores.slice(0, TOPE_ERRORES).map((e) => (
                    <List.Item key={e}>{e}</List.Item>
                  ))}
                </List>
                {resumen.errores.length > TOPE_ERRORES && (
                  <Text size="xs" c="dimmed" mt={4}>
                    y {resumen.errores.length - TOPE_ERRORES} más. Corregí estos y volvé a
                    subir el archivo.
                  </Text>
                )}
              </>
            )}
          </Alert>
        )}
      </Stack>
    </Modal>
  )
}
