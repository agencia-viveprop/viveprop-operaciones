import { Paper, Text } from '@mantine/core'

export default function StatCard({
  label,
  value,
  color,
  caption,
}: {
  label: string
  value: string | number
  /** Nombre de color del tema ("good") o color.tono explicito ("brand.3") */
  color: string
  caption?: string
}) {
  const [colorName, shade = '6'] = color.split('.')
  return (
    <Paper
      withBorder
      radius="md"
      p="md"
      style={{ borderTop: `4px solid var(--mantine-color-${colorName}-${shade})` }}
    >
      <Text size="xs" fw={700} c="dimmed" style={{ letterSpacing: 0.5 }}>
        {label.toUpperCase()}
      </Text>
      <Text size="28px" fw={800} mt={4} lh={1.1}>
        {value}
      </Text>
      {caption && (
        <Text size="xs" c="dimmed" mt={4}>
          {caption}
        </Text>
      )}
    </Paper>
  )
}
