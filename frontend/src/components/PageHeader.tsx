import { Box, Group, Stack, Text, Title } from '@mantine/core'

export default function PageHeader({
  title,
  subtitle,
  action,
}: {
  title: string
  subtitle?: string
  action?: React.ReactNode
}) {
  return (
    <Stack gap={4} mb="md">
      {/* El titulo y su barrita van juntos en la misma columna. Estaban en
          niveles distintos, y cuando la accion no cabe al lado --en un telefono
          los botones se van a la linea siguiente-- la barra quedaba debajo de
          ellos, separada del titulo al que subraya. */}
      <Group justify="space-between" align="flex-start" gap="sm">
        <Stack gap={4}>
          <Title order={2}>{title}</Title>
          <Box w={36} h={4} bg="accent" style={{ borderRadius: 2 }} />
        </Stack>
        {action}
      </Group>
      {subtitle && (
        <Text size="sm" c="dimmed">
          {subtitle}
        </Text>
      )}
    </Stack>
  )
}
