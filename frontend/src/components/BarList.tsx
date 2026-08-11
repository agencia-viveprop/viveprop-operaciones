import { Box, Group, Stack, Text } from '@mantine/core'
import type { ConteoEtiqueta } from '../api/reportes'

export default function BarList({ items, color = 'brand' }: { items: ConteoEtiqueta[]; color?: string }) {
  const max = Math.max(1, ...items.map((i) => i.cantidad))
  if (items.length === 0) return <Text size="sm" c="dimmed">Sin datos</Text>

  return (
    <Stack gap="xs">
      {items.map((item) => (
        <div key={item.etiqueta}>
          <Group justify="space-between" mb={2}>
            <Text size="sm">{item.etiqueta}</Text>
            <Text size="sm" fw={600}>
              {item.cantidad}
            </Text>
          </Group>
          <Box h={6} bg="gray.2" style={{ borderRadius: 3 }}>
            <Box h={6} bg={color} style={{ borderRadius: 3, width: `${(item.cantidad / max) * 100}%` }} />
          </Box>
        </div>
      ))}
    </Stack>
  )
}
