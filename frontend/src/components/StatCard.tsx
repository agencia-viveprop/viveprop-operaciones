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
      // `caja-cifra` deja que la cifra se mida contra el ancho de esta tarjeta:
      // en un teléfono de 360 px entran dos por fila y un monto de siete dígitos
      // no cabe al tamaño de escritorio.
      className="caja-cifra"
      style={{ borderTop: `4px solid var(--mantine-color-${colorName}-${shade})` }}
    >
      <Text size="xs" fw={700} c="dimmed" style={{ letterSpacing: 0.5 }}>
        {label.toUpperCase()}
      </Text>
      <Text className="cifra" fw={800} mt={4} lh={1.1}>
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
