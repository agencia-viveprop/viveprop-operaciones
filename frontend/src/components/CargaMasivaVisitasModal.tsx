import { useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Alert, Button, FileButton, Group, List, Modal, Stack, Text } from '@mantine/core'
import { IconUpload } from '@tabler/icons-react'
import { CLAVE_VISITAS, importarVisitas, type ResumenCargaVisitas } from '../api/visitas'

/** Cuántos errores se listan antes de resumir. Igual criterio que la carga de
 *  negocios: con un archivo muy malo salen cientos, y una lista de cientos no
 *  se lee. */
const TOPE_ERRORES = 15

const COLUMNAS_ESPERADAS = [
  'Propiedad',
  'Dirección',
  'Tipo',
  'Mercado',
  'Cliente',
  'RUT',
  'Objetivo de compra',
  'Fecha/hora solicitada',
  'Etapa',
  'Solicitada el',
]

/**
 * Carga masiva de visitas.
 *
 * A diferencia de la de negocios, no hay botón "Descargar plantilla": el
 * archivo no lo genera ViveProp, sale tal cual de la consola de
 * administración con estas columnas fijas.
 *
 * No hay ID en el archivo de origen, así que cargar el mismo archivo dos
 * veces duplica filas a propósito — se sacan a mano, una por una, desde la
 * tabla de Visitas.
 */
export default function CargaMasivaVisitasModal({
  abierto,
  onCerrar,
}: {
  abierto: boolean
  onCerrar: () => void
}) {
  const queryClient = useQueryClient()
  const [archivo, setArchivo] = useState<File | null>(null)
  const [resumen, setResumen] = useState<ResumenCargaVisitas | null>(null)
  const resetRef = useRef<() => void>(null)

  const subir = useMutation({
    mutationFn: () => importarVisitas(archivo!),
    onSuccess: (r) => {
      setResumen(r)
      setArchivo(null)
      resetRef.current?.()
      if (r.errores.length === 0) {
        queryClient.invalidateQueries({ queryKey: CLAVE_VISITAS })
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
    <Modal opened={abierto} onClose={cerrar} title="Carga masiva de visitas" size="lg">
      <Stack gap="md">
        <Text size="sm" c="dimmed">
          El archivo tiene que traer estas columnas, tal como las exporta la consola:{' '}
          {COLUMNAS_ESPERADAS.join(' · ')}. No trae un identificador único, así que cada
          carga agrega todas las filas como registros nuevos: si se sube el mismo archivo dos
          veces, las filas quedan repetidas y se borran a mano desde la tabla.
        </Text>

        <Group>
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
              <Text size="sm">{resumen.nuevas} visitas nuevas</Text>
            ) : (
              <>
                <Text size="sm">
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
