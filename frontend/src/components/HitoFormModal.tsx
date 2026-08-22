import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Button, Group, Modal, Stack, Text } from '@mantine/core'
import { obtenerCatalogos } from '../api/catalogos'
import {
  actualizarHito,
  CambioDeMontoError,
  crearHito,
  type Hito,
} from '../api/negocios'
import CamposHito from './CamposHito'
import {
  aPorcentaje,
  hitoVacio,
  payloadHito,
  validarHito,
  type FormHito,
} from './hitoForm'
import { clp } from './negociosFormato'

/** Pasa un hito guardado al formulario. Las tasas vuelven a porcentaje. */
function desdeHito(h: Hito): FormHito {
  return {
    nombre: h.nombre ?? '',
    fecha_inicio: h.fecha_inicio ?? '',
    fecha_cierre: h.fecha_cierre ?? '',
    estado: h.estado,
    valor_negocio: h.valor_negocio === null ? '' : Number(h.valor_negocio),
    moneda: h.moneda ?? 'UF',
    fecha_valorizacion: h.fecha_valorizacion ?? '',
    valor_clp_manual: h.valor_clp_manual === null ? '' : Number(h.valor_clp_manual),
    motivo_valor_manual: h.motivo_valor_manual ?? '',
    pct_lado_vendedor: aPorcentaje(h.pct_lado_vendedor),
    pct_lado_comprador: aPorcentaje(h.pct_lado_comprador),
    pct_rebate_concentrador: aPorcentaje(h.pct_rebate_concentrador),
    pct_broker_vendedor: aPorcentaje(h.pct_broker_vendedor),
    pct_broker_comprador: aPorcentaje(h.pct_broker_comprador),
    pct_vp_vendedor: aPorcentaje(h.pct_vp_vendedor),
    pct_vp_comprador: aPorcentaje(h.pct_vp_comprador),
    pct_equipo: aPorcentaje(h.pct_equipo),
    pct_tercero: aPorcentaje(h.pct_tercero),
    nombre_tercero: h.nombre_tercero ?? '',
    motivo_perdida_detalle: h.motivo_perdida_detalle ?? '',
  }
}

/**
 * Crear o editar una liquidación.
 *
 * **Es lo que faltaba para poder cerrar un negocio desde la app.** La API ya lo
 * permitía y ninguna pantalla lo llamaba: se podía registrar que un negocio se
 * perdió --con un movimiento del pipeline-- pero no que se ganó. El motor de
 * comisiones, que es la pieza más grande del proyecto, no tenía forma de recibir
 * un cierre desde la interfaz.
 *
 * Al guardar, el backend recalcula todo: valor en pesos con la UF de la fecha de
 * valorización, comisión total, broker, rebate, equipo, tercero y real VP. Este
 * formulario manda tasas, no montos.
 */
export default function HitoFormModal({
  negocioId,
  modelo,
  hito,
  abierto,
  onClose,
}: {
  negocioId: number
  modelo: string
  /** `null` crea una liquidación nueva; un hito la edita. */
  hito: Hito | null
  abierto: boolean
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState<FormHito>(hitoVacio())
  // Cuando la API avisa que el monto se movería, queda acá hasta que se decida.
  const [aviso, setAviso] = useState<CambioDeMontoError | null>(null)
  const { data: catalogos } = useQuery({ queryKey: ['catalogos'], queryFn: obtenerCatalogos })

  // Se repuebla al abrir, no en el render: si no, tipear se perdería en cada
  // vuelta y editar sería imposible.
  useEffect(() => {
    if (abierto) {
      setForm(hito ? desdeHito(hito) : hitoVacio())
      setAviso(null)
    }
  }, [abierto, hito])

  const set = <K extends keyof FormHito>(campo: K, valor: FormHito[K]) => {
    setForm((f) => ({ ...f, [campo]: valor }))
    // Editar despues del aviso lo invalida: los montos que mostraba ya no son
    // los que resultarian de guardar.
    setAviso(null)
  }

  const guardar = useMutation({
    mutationFn: (confirmado: boolean) => {
      const cuerpo = payloadHito(form)
      if (confirmado) cuerpo.confirmar_cambio_de_monto = true
      return hito
        ? actualizarHito(negocioId, hito.id, cuerpo)
        : crearHito(negocioId, cuerpo)
    },
    onError: (e) => {
      if (e instanceof CambioDeMontoError) setAviso(e)
    },
    onSuccess: () => {
      // La plata cambió: el negocio, el listado y toda la reportería que lo suma.
      ;['negocio', 'negocios', 'resumen-negocios', 'negocios-por-mes',
        'bandeja-negocios', 'reporte-mensual', 'reporte-semanal', 'vista-directorio',
      ].forEach((k) => queryClient.invalidateQueries({ queryKey: [k] }))
      onClose()
    },
  })

  const problema = validarHito(form)

  return (
    <Modal
      opened={abierto}
      onClose={onClose}
      title={hito ? `Editar ${hito.nombre || 'la liquidación'}` : 'Agregar liquidación'}
      size="lg"
    >
      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (!problema) guardar.mutate(false)
        }}
      >
        <Stack gap="sm">
          {hito && (
            <Text size="xs" c="dimmed">
              Hoy: {hito.estado} · comisión real {clp(hito.comision_real_vp)}. Al guardar se
              recalcula con lo que quede en este formulario.
            </Text>
          )}

          <CamposHito
            form={form}
            set={set}
            modelo={modelo}
            estados={catalogos?.estados_negocio ?? []}
            conNombre
          />

          {problema && (
            <Alert color="warning" variant="light">
              {problema}
            </Alert>
          )}

          {/* El aviso de la API: esta liquidación ya está cerrada y guardarla le
              cambiaría la comisión. Se muestran los dos montos porque sin ellos
              no hay nada que decidir. */}
          {aviso && (
            <Alert color="critical" variant="light" title="La comisión va a cambiar">
              <Stack gap={4}>
                <Text size="sm">
                  Esta liquidación está cerrada. Hoy su comisión real es{' '}
                  <Text span fw={700} ff="monospace">{clp(aviso.comisionActual)}</Text> y al
                  guardar quedaría en{' '}
                  <Text span fw={700} ff="monospace">{clp(aviso.comisionNueva)}</Text>.
                </Text>
                <Text size="xs" c="dimmed">
                  Si ese monto ya se facturó, cancela y revisa las tasas antes de guardar.
                </Text>
              </Stack>
            </Alert>
          )}

          {guardar.isError && !aviso && (
            <Alert color="critical" variant="light">
              {(guardar.error as Error).message}
            </Alert>
          )}

          <Group justify="flex-end">
            <Button variant="default" onClick={onClose}>
              Cancelar
            </Button>
            {aviso ? (
              <Button
                color="critical"
                loading={guardar.isPending}
                onClick={() => guardar.mutate(true)}
              >
                Guardar de todas formas
              </Button>
            ) : (
              <Button
                type="submit"
                color="accent"
                loading={guardar.isPending}
                disabled={problema !== null}
              >
                {hito ? 'Guardar' : 'Agregar'}
              </Button>
            )}
          </Group>
        </Stack>
      </form>
    </Modal>
  )
}
