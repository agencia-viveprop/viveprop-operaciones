import { createTheme, type MantineColorsTuple } from '@mantine/core'

// Rampa de 10 tonos derivada de #4a3aa7 (indice 6 = color exacto de marca),
// calzando con el morado que Viveprop ya usa en su otra plataforma (#3D3EA8).
const brand: MantineColorsTuple = [
  '#e7e5f6',
  '#ccc6eb',
  '#ada4df',
  '#8b7ed2',
  '#6555c4',
  '#5240b9',
  '#4a3aa7',
  '#372b7d',
  '#28205b',
  '#191439',
]

// Colores de estado: fijos, nunca reusados como color de categoria/serie.
// Se repite el mismo hex en las 10 posiciones para que Mantine los use
// siempre igual sin importar el shade solicitado.
const solid = (hex: string): MantineColorsTuple => [hex, hex, hex, hex, hex, hex, hex, hex, hex, hex]

export const theme = createTheme({
  primaryColor: 'brand',
  primaryShade: { light: 6, dark: 4 },
  fontFamily: 'system-ui, -apple-system, "Segoe UI", sans-serif',
  defaultRadius: 'md',
  radius: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
  },
  colors: {
    brand,
    good: solid('#0ca30c'),
    warning: solid('#fab219'),
    serious: solid('#ec835a'),
    critical: solid('#d03b3b'),
  },
})
