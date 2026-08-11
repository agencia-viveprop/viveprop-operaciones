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
      <Group justify="space-between" align="flex-start">
        <Title order={2}>{title}</Title>
        {action}
      </Group>
      <Box w={36} h={4} bg="accent" style={{ borderRadius: 2 }} />
      {subtitle && (
        <Text size="sm" c="dimmed">
          {subtitle}
        </Text>
      )}
    </Stack>
  )
}
