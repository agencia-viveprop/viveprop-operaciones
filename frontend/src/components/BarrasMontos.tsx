import { Box, Group, Stack, Text } from '@mantine/core'
import { clp } from './negociosFormato'

export type FilaMonto = {
  etiqueta: string
  monto: number
  detalle?: string
}

/**
 * Barras horizontales para montos. Una sola serie, así que no lleva leyenda:
 * el título del panel dice qué se está midiendo.
 *
 * El valor va como etiqueta directa en cada fila. Con pocas categorías eso hace
 * innecesaria una tabla aparte, y deja de depender del color para leerse.
 */
export default function BarrasMontos({
  items,
  color = 'var(--mantine-color-brand-6)',
}: {
  items: FilaMonto[]
  color?: string
}) {
  if (items.length === 0) {
    return (
      <Text size="sm" c="dimmed">
        Sin datos
      </Text>
    )
  }

  const max = Math.max(1, ...items.map((i) => i.monto))

  return (
    <Stack gap="sm">
      {items.map((item) => (
        <div key={item.etiqueta}>
          <Group justify="space-between" mb={4} gap="xs" wrap="nowrap">
            <Text size="sm" style={{ minWidth: 0 }} truncate>
              {item.etiqueta}
            </Text>
            <Group gap={6} wrap="nowrap">
              {item.detalle && (
                <Text size="xs" c="dimmed">
                  {item.detalle}
                </Text>
              )}
              <Text size="sm" fw={600} ff="monospace">
                {clp(item.monto)}
              </Text>
            </Group>
          </Group>
          {/* Pista recesiva: la barra es el dato, el riel es solo la escala. */}
          <Box
            h={8}
            style={{
              borderRadius: 4,
              background: 'var(--mantine-color-default-border)',
              overflow: 'hidden',
            }}
          >
            <Box
              h={8}
              style={{
                borderRadius: 4,
                background: color,
                width: `${Math.max(2, (item.monto / max) * 100)}%`,
              }}
            />
          </Box>
        </div>
      ))}
    </Stack>
  )
}
