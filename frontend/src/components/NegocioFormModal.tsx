import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Divider,
  Group,
  Modal,
  NumberInput,
  Select,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  Textarea,
} from '@mantine/core'
import { IconInfoCircle } from '@tabler/icons-react'
import { obtenerCatalogos } from '../api/catalogos'
import { buscarPropiedades, crearNegocio } from '../api/negocios'

/** Los porcentajes se ingresan como número (2 = 2%) y se envían como fracción. */
function aFraccion(valor: number | string): string | null {
  if (valor === '' || valor === null) return null
  return String(Number(valor) / 100)
}

function vacio() {
  return {
    codigo: '',
    modelo: '',
    alianza_id: '',
    tipo_operacion_id: '',
    direccion: '',
    unidad: '',
    comuna: '',
    tipo_propiedad_id: '',
    estado_propiedad_id: '',
    vendedor_arrendador: '',
    comprador_arrendatario: '',
    corredor_agente: '',
    observaciones: '',
    // hito único
    fecha_inicio: '',
    estado: 'ACTIVO',
    etapa: '',
    valor_negocio: '' as number | '',
    moneda: 'UF',
    fecha_valorizacion: '',
    valor_clp_manual: '' as number | '',
    motivo_valor_manual: '',
    pct_lado_vendedor: '' as number | '',
    pct_lado_comprador: '' as number | '',
    pct_rebate_concentrador: '' as number | '',
    pct_broker_vendedor: '' as number | '',
    pct_broker_comprador: '' as number | '',
    pct_vp_vendedor: '' as number | '',
    pct_vp_comprador: '' as number | '',
    pct_equipo: 10 as number | '',
    pct_tercero: '' as number | '',
    nombre_tercero: '',
  }
}

/** Qué lado se cobra en cada modelo, para no pedir campos que ese modelo ignora. */
const CAMPOS_POR_MODELO: Record<string, { vendedor: boolean; comprador: boolean; rebate: boolean }> = {
  MERCADO_PRIMARIO: { vendedor: true, comprador: false, rebate: false },
  SECUNDARIO_CONCENTRADORES: { vendedor: false, comprador: true, rebate: true },
  SECUNDARIO_AGENCIA: { vendedor: true, comprador: true, rebate: false },
}

export default function NegocioFormModal({
  abierto,
  onClose,
}: {
  abierto: boolean
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const [form, setForm] = useState(vacio())
  const [parecidas, setParecidas] = useState<string[]>([])

  const { data: catalogos } = useQuery({ queryKey: ['catalogos'], queryFn: obtenerCatalogos })

  const set = (campo: string, valor: unknown) => setForm((f) => ({ ...f, [campo]: valor }))

  // Ofrece propiedades parecidas mientras se escribe la dirección: la clave
  // única no agrupa "Av. Fernández Albano 492" con "Fernández Albano 492".
  useEffect(() => {
    const texto = form.direccion.trim()
    if (texto.length < 3) {
      setParecidas([])
      return
    }
    const id = setTimeout(() => {
      buscarPropiedades(texto)
        .then((props) =>
          setParecidas(
            props
              .filter((p) => p.direccion.toLowerCase() !== texto.toLowerCase())
              .map((p) => [p.direccion, p.unidad, p.comuna].filter(Boolean).join(' · ')),
          ),
        )
        .catch(() => setParecidas([]))
    }, 350)
    return () => clearTimeout(id)
  }, [form.direccion])

  const guardar = useMutation({
    mutationFn: () => {
      const pcts = [
        'pct_lado_vendedor', 'pct_lado_comprador', 'pct_rebate_concentrador',
        'pct_broker_vendedor', 'pct_broker_comprador', 'pct_vp_vendedor',
        'pct_vp_comprador', 'pct_equipo', 'pct_tercero',
      ] as const

      const hito: Record<string, unknown> = {
        fecha_inicio: form.fecha_inicio,
        estado: form.estado,
        etapa: form.etapa || null,
        valor_negocio: form.valor_negocio === '' ? null : String(form.valor_negocio),
        moneda: form.moneda || null,
        fecha_valorizacion: form.fecha_valorizacion || null,
        valor_clp_manual: form.valor_clp_manual === '' ? null : String(form.valor_clp_manual),
        motivo_valor_manual: form.motivo_valor_manual || null,
        nombre_tercero: form.nombre_tercero || null,
      }
      pcts.forEach((p) => (hito[p] = aFraccion(form[p])))

      return crearNegocio({
        codigo: form.codigo.trim(),
        modelo: form.modelo,
        alianza_id: form.alianza_id ? Number(form.alianza_id) : null,
        tipo_operacion_id: form.tipo_operacion_id ? Number(form.tipo_operacion_id) : null,
        propiedad: {
          direccion: form.direccion.trim(),
          unidad: form.unidad.trim() || null,
          comuna: form.comuna.trim(),
          tipo_propiedad_id: form.tipo_propiedad_id ? Number(form.tipo_propiedad_id) : null,
          estado_propiedad_id: form.estado_propiedad_id ? Number(form.estado_propiedad_id) : null,
        },
        vendedor_arrendador: form.vendedor_arrendador || null,
        comprador_arrendatario: form.comprador_arrendatario || null,
        corredor_agente: form.corredor_agente || null,
        observaciones: form.observaciones || null,
        hitos: [hito],
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['negocios'] })
      cerrar()
    },
  })

  function cerrar() {
    setForm(vacio())
    setParecidas([])
    guardar.reset()
    onClose()
  }

  const opciones = (items: { id: number | null; nombre: string }[] = []) =>
    items.map((i) => ({ value: String(i.id), label: i.nombre }))

  const lados = CAMPOS_POR_MODELO[form.modelo] ?? { vendedor: true, comprador: true, rebate: true }
  const completo = form.codigo && form.modelo && form.direccion && form.comuna && form.fecha_inicio

  return (
    <Modal opened={abierto} onClose={cerrar} title="Nuevo negocio" size="lg">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          guardar.mutate()
        }}
      >
        <Stack gap="sm">
          <SimpleGrid cols={2}>
            <TextInput
              label="Código"
              placeholder="VVP-20"
              required
              value={form.codigo}
              onChange={(e) => set('codigo', e.currentTarget.value)}
            />
            <Select
              label="Modelo de negocio"
              required
              data={(catalogos?.modelos_negocio ?? []).map((m) => ({ value: m.codigo, label: m.nombre }))}
              value={form.modelo || null}
              onChange={(v) => set('modelo', v ?? '')}
            />
            <Select
              label="Alianza"
              data={opciones(catalogos?.alianzas)}
              value={form.alianza_id || null}
              onChange={(v) => set('alianza_id', v ?? '')}
              clearable
              searchable
            />
            <Select
              label="Operación"
              data={opciones(catalogos?.tipos_operacion)}
              value={form.tipo_operacion_id || null}
              onChange={(v) => set('tipo_operacion_id', v ?? '')}
              clearable
            />
          </SimpleGrid>

          <Divider label="Propiedad" labelPosition="left" />
          <SimpleGrid cols={{ base: 1, sm: 3 }}>
            <TextInput
              label="Dirección"
              required
              value={form.direccion}
              onChange={(e) => set('direccion', e.currentTarget.value)}
            />
            <TextInput
              label="Unidad"
              placeholder="316-A"
              value={form.unidad}
              onChange={(e) => set('unidad', e.currentTarget.value)}
            />
            <TextInput
              label="Comuna"
              required
              value={form.comuna}
              onChange={(e) => set('comuna', e.currentTarget.value)}
            />
          </SimpleGrid>

          {parecidas.length > 0 && (
            <Alert variant="light" color="info" icon={<IconInfoCircle size={18} />} title="Ya existen propiedades parecidas">
              <Stack gap={2}>
                {parecidas.slice(0, 4).map((p) => (
                  <Text key={p} size="sm">{p}</Text>
                ))}
                <Text size="xs" c="dimmed">
                  Si es la misma unidad, escribe la dirección igual y se reusa en vez de duplicarse.
                </Text>
              </Stack>
            </Alert>
          )}

          <SimpleGrid cols={2}>
            <Select
              label="Tipo de propiedad"
              data={opciones(catalogos?.tipos_propiedad)}
              value={form.tipo_propiedad_id || null}
              onChange={(v) => set('tipo_propiedad_id', v ?? '')}
              clearable
            />
            <Select
              label="Estado de la propiedad"
              data={opciones(catalogos?.estados_propiedad)}
              value={form.estado_propiedad_id || null}
              onChange={(v) => set('estado_propiedad_id', v ?? '')}
              clearable
            />
          </SimpleGrid>

          <Divider label="Contrapartes" labelPosition="left" />
          <SimpleGrid cols={{ base: 1, sm: 3 }}>
            <TextInput
              label="Vendedor / Arrendador"
              value={form.vendedor_arrendador}
              onChange={(e) => set('vendedor_arrendador', e.currentTarget.value)}
            />
            <TextInput
              label="Comprador / Arrendatario"
              value={form.comprador_arrendatario}
              onChange={(e) => set('comprador_arrendatario', e.currentTarget.value)}
            />
            <TextInput
              label="Corredor"
              value={form.corredor_agente}
              onChange={(e) => set('corredor_agente', e.currentTarget.value)}
            />
          </SimpleGrid>

          <Divider label="Liquidación" labelPosition="left" />
          <SimpleGrid cols={{ base: 2, sm: 4 }}>
            <TextInput
              label="Fecha inicio"
              type="date"
              required
              value={form.fecha_inicio}
              onChange={(e) => set('fecha_inicio', e.currentTarget.value)}
            />
            <Select
              label="Estado"
              data={(catalogos?.estados_negocio ?? []).map((e) => ({ value: e.codigo, label: e.nombre }))}
              value={form.estado}
              onChange={(v) => set('estado', v ?? 'ACTIVO')}
            />
            <Select
              label="Etapa"
              data={(catalogos?.etapas ?? []).map((e) => ({ value: e.codigo, label: `${e.codigo} · ${e.nombre}` }))}
              value={form.etapa || null}
              onChange={(v) => set('etapa', v ?? '')}
              clearable
            />
            <Select
              label="Moneda"
              data={['UF', 'CLP']}
              value={form.moneda}
              onChange={(v) => set('moneda', v ?? 'UF')}
            />
          </SimpleGrid>

          <SimpleGrid cols={{ base: 2, sm: 3 }}>
            <NumberInput
              label="Valor del negocio"
              decimalScale={2}
              value={form.valor_negocio}
              onChange={(v) => set('valor_negocio', v)}
            />
            <TextInput
              label="Fecha de valorización"
              type="date"
              description="Si se deja vacía se usa la de inicio"
              value={form.fecha_valorizacion}
              onChange={(e) => set('fecha_valorizacion', e.currentTarget.value)}
            />
            <NumberInput
              label="Valor en pesos a mano"
              description="Manda sobre el cálculo por UF"
              value={form.valor_clp_manual}
              onChange={(v) => set('valor_clp_manual', v)}
            />
          </SimpleGrid>

          {form.valor_clp_manual !== '' && (
            <TextInput
              label="Motivo del valor a mano"
              placeholder="Liquidación de la inmobiliaria, ajuste de costos…"
              value={form.motivo_valor_manual}
              onChange={(e) => set('motivo_valor_manual', e.currentTarget.value)}
            />
          )}

          <Divider label="Comisiones (en %)" labelPosition="left" />
          <SimpleGrid cols={{ base: 2, sm: 4 }}>
            {lados.vendedor && (
              <NumberInput
                label="% lado vendedor"
                decimalScale={4}
                value={form.pct_lado_vendedor}
                onChange={(v) => set('pct_lado_vendedor', v)}
              />
            )}
            {lados.comprador && (
              <NumberInput
                label="% lado comprador"
                decimalScale={4}
                value={form.pct_lado_comprador}
                onChange={(v) => set('pct_lado_comprador', v)}
              />
            )}
            {lados.rebate && (
              <>
                <NumberInput
                  label="% que cobra el concentrador"
                  description="Base del rebate"
                  decimalScale={4}
                  value={form.pct_lado_vendedor}
                  onChange={(v) => set('pct_lado_vendedor', v)}
                />
                <NumberInput
                  label="% de rebate"
                  decimalScale={4}
                  value={form.pct_rebate_concentrador}
                  onChange={(v) => set('pct_rebate_concentrador', v)}
                />
              </>
            )}
          </SimpleGrid>

          <SimpleGrid cols={{ base: 2, sm: 4 }}>
            {lados.vendedor && (
              <>
                <NumberInput
                  label="% broker vendedor"
                  decimalScale={6}
                  value={form.pct_broker_vendedor}
                  onChange={(v) => set('pct_broker_vendedor', v)}
                />
                <NumberInput
                  label="% VP vendedor"
                  decimalScale={6}
                  value={form.pct_vp_vendedor}
                  onChange={(v) => set('pct_vp_vendedor', v)}
                />
              </>
            )}
            {lados.comprador && (
              <>
                <NumberInput
                  label="% broker comprador"
                  decimalScale={6}
                  value={form.pct_broker_comprador}
                  onChange={(v) => set('pct_broker_comprador', v)}
                />
                <NumberInput
                  label="% VP comprador"
                  decimalScale={6}
                  value={form.pct_vp_comprador}
                  onChange={(v) => set('pct_vp_comprador', v)}
                />
              </>
            )}
          </SimpleGrid>

          <SimpleGrid cols={{ base: 2, sm: 3 }}>
            <NumberInput
              label="% equipo ViveProp"
              decimalScale={2}
              value={form.pct_equipo}
              onChange={(v) => set('pct_equipo', v)}
            />
            <NumberInput
              label="% tercero"
              decimalScale={2}
              value={form.pct_tercero}
              onChange={(v) => set('pct_tercero', v)}
            />
            <TextInput
              label="Nombre del tercero"
              value={form.nombre_tercero}
              onChange={(e) => set('nombre_tercero', e.currentTarget.value)}
            />
          </SimpleGrid>

          <Textarea
            label="Observaciones"
            autosize
            minRows={2}
            value={form.observaciones}
            onChange={(e) => set('observaciones', e.currentTarget.value)}
          />

          {guardar.isError && (
            <Alert color="critical" variant="filled">
              {(guardar.error as Error).message}
            </Alert>
          )}

          <Text size="xs" c="dimmed">
            Las comisiones se calculan al guardar, con la UF de la fecha de valorización.
          </Text>

          <Group justify="flex-end">
            <Button variant="default" onClick={cerrar}>
              Cancelar
            </Button>
            <Button type="submit" color="accent" loading={guardar.isPending} disabled={!completo}>
              Guardar
            </Button>
          </Group>
        </Stack>
      </form>
    </Modal>
  )
}
