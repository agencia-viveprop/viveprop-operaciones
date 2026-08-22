import {
  Alert,
  Divider,
  NumberInput,
  Select,
  SimpleGrid,
  TextInput,
} from '@mantine/core'
import type { ItemCatalogo } from '../api/catalogos'
import { CAMPOS_POR_MODELO, type FormHito } from './hitoForm'

/**
 * Los campos de una liquidación, compartidos por el alta de negocio y la edición
 * de un hito.
 *
 * Están acá y no duplicados en cada formulario porque son las reglas del motor de
 * comisiones puestas en pantalla: qué lado se cobra según el modelo, las tasas en
 * porcentaje, la fecha de valorización. Tenerlos dos veces garantizaba que un día
 * divergieran, y el que quedara viejo calcularía distinto sin que nadie lo note.
 */
export default function CamposHito({
  form,
  set,
  modelo,
  estados,
  conNombre = false,
}: {
  form: FormHito
  set: <K extends keyof FormHito>(campo: K, valor: FormHito[K]) => void
  modelo: string
  estados: ItemCatalogo[]
  /** El alta crea una sola liquidación y no le pide nombre; al agregar la
   *  segunda, el nombre es lo que las distingue. */
  conNombre?: boolean
}) {
  const lados = CAMPOS_POR_MODELO[modelo] ?? { vendedor: true, comprador: true, rebate: true }
  const cerrado = form.estado === 'CERRADO'
  const perdido = form.estado === 'PERDIDO' || form.estado === 'DESISTIDO'

  return (
    <>
      <Divider label="Liquidación" labelPosition="left" />

      {conNombre && (
        <TextInput
          label="Nombre de la liquidación"
          description="PROMESA, ESCRITURA… es lo que la distingue de las otras del mismo negocio"
          value={form.nombre}
          onChange={(e) => set('nombre', e.currentTarget.value)}
        />
      )}

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
          data={estados.map((e) => ({ value: e.codigo, label: e.nombre }))}
          value={form.estado}
          onChange={(v) => set('estado', v ?? 'ACTIVO')}
        />
        {/* Solo aparece cuando corresponde: un campo de fecha de cierre visible
            en una liquidación activa invita a llenarlo, y la API lo rechaza. */}
        {cerrado && (
          <TextInput
            label="Fecha de cierre"
            type="date"
            required
            value={form.fecha_cierre}
            onChange={(e) => set('fecha_cierre', e.currentTarget.value)}
          />
        )}
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
          onChange={(v) => set('valor_negocio', v as number | '')}
        />
        <TextInput
          label="Fecha de valorización"
          type="date"
          description="Con qué UF se convierte a pesos"
          value={form.fecha_valorizacion}
          onChange={(e) => set('fecha_valorizacion', e.currentTarget.value)}
        />
        <NumberInput
          label="Valor en pesos a mano"
          description="Manda sobre el cálculo por UF"
          value={form.valor_clp_manual}
          onChange={(v) => set('valor_clp_manual', v as number | '')}
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

      {perdido && (
        <TextInput
          label="Por qué no se concretó"
          description="Texto libre: el catálogo de motivos todavía no está definido"
          value={form.motivo_perdida_detalle}
          onChange={(e) => set('motivo_perdida_detalle', e.currentTarget.value)}
        />
      )}

      <Divider label="Comisiones (en %)" labelPosition="left" />
      <Alert color="brand" variant="light" p="xs">
        Acá van las tasas. Los montos —comisión total, broker, rebate, real VP— los calcula
        el sistema al guardar.
      </Alert>

      <SimpleGrid cols={{ base: 2, sm: 4 }}>
        {lados.vendedor && (
          <NumberInput
            label="% lado vendedor"
            decimalScale={4}
            value={form.pct_lado_vendedor}
            onChange={(v) => set('pct_lado_vendedor', v as number | '')}
          />
        )}
        {lados.comprador && (
          <NumberInput
            label="% lado comprador"
            decimalScale={4}
            value={form.pct_lado_comprador}
            onChange={(v) => set('pct_lado_comprador', v as number | '')}
          />
        )}
        {lados.rebate && (
          <>
            <NumberInput
              label="% que cobra el concentrador"
              description="Base del rebate"
              decimalScale={4}
              value={form.pct_lado_vendedor}
              onChange={(v) => set('pct_lado_vendedor', v as number | '')}
            />
            <NumberInput
              label="% de rebate"
              decimalScale={4}
              value={form.pct_rebate_concentrador}
              onChange={(v) => set('pct_rebate_concentrador', v as number | '')}
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
              onChange={(v) => set('pct_broker_vendedor', v as number | '')}
            />
            <NumberInput
              label="% VP vendedor"
              decimalScale={6}
              value={form.pct_vp_vendedor}
              onChange={(v) => set('pct_vp_vendedor', v as number | '')}
            />
          </>
        )}
        {lados.comprador && (
          <>
            <NumberInput
              label="% broker comprador"
              decimalScale={6}
              value={form.pct_broker_comprador}
              onChange={(v) => set('pct_broker_comprador', v as number | '')}
            />
            <NumberInput
              label="% VP comprador"
              decimalScale={6}
              value={form.pct_vp_comprador}
              onChange={(v) => set('pct_vp_comprador', v as number | '')}
            />
          </>
        )}
      </SimpleGrid>

      <SimpleGrid cols={{ base: 2, sm: 3 }}>
        <NumberInput
          label="% equipo"
          description="Sobre la comisión de ViveProp"
          decimalScale={4}
          value={form.pct_equipo}
          onChange={(v) => set('pct_equipo', v as number | '')}
        />
        <NumberInput
          label="% tercero"
          decimalScale={4}
          value={form.pct_tercero}
          onChange={(v) => set('pct_tercero', v as number | '')}
        />
        <TextInput
          label="Nombre del tercero"
          value={form.nombre_tercero}
          onChange={(e) => set('nombre_tercero', e.currentTarget.value)}
        />
      </SimpleGrid>
    </>
  )
}
