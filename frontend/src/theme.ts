import { createTheme, type MantineColorsTuple } from '@mantine/core'

// Rampa de 10 tonos derivada de #3b3b98 (indice 6 = color exacto de marca),
// extraido por muestreo de pixeles del logo real (frontend/public/logo.png,
// entregado por el usuario) -- es el color dominante del icono y de la
// palabra "prop" del wordmark. Calza con el morado que Viveprop ya usa en
// su otra plataforma (--brand:#3D3EA8), asi que confirma que esa familia de
// color era la correcta desde el Sprint A4. Revalidado con el script de
// accesibilidad del skill de dataviz junto a los colores de estado: sin
// choques (el unico fail que queda es preexistente entre warning/serious y
// critical/good, sin relacion con este color).
const brand: MantineColorsTuple = [
  '#e5e5f5',
  '#c8c8ea',
  '#9f9fda',
  '#7777ca',
  '#4f4fbb',
  '#3c3c9a',
  '#3b3b98',
  '#282867',
  '#1d1d49',
  '#131330',
]

// Segundo color real del logo (wordmark "vive"), muestreado del mismo PNG.
// Disponible para cuando se necesite un acento secundario (ej. categorias
// del futuro dashboard) -- no forma parte de la paleta tematica de Mantine.
export const LOGO_ACCENT_COLOR = '#fd5968'

// Colores de estado: fijos, nunca reusados como color de categoria/serie.
// Se repite el mismo hex en las 10 posiciones para que Mantine los use
// siempre igual sin importar el shade solicitado.
// OJO al usarlos en Badge/Button: variant="light" (y "outline"/"dot") calculan
// fondo y texto a partir de DOS shades distintos de la rampa -- como aqui son
// todas iguales, fondo y texto quedan del mismo color (texto invisible).
// Usar siempre variant="filled" (texto blanco calculado por contraste) con
// estos colores.
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
