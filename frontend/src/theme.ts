import { createTheme, type MantineColorsTuple } from '@mantine/core'

// Paleta oficial entregada por el usuario (hex exactos, no aproximados).

// Primario/marca: #3D3EA8, con "oscuro"/"medio"/"claro"/"pálido" ubicados en
// su posicion real de luminosidad (medida, no asumida por el nombre --
// "claro" resulto ser mas claro que "palido"). index6 = el color de marca
// exacto (calza con el shade que usa Mantine por defecto en modo claro).
const brand: MantineColorsTuple = [
  '#f8f8fc',
  '#EDEDF9', // primario claro (fondos suaves)
  '#DDDDF5', // primario palido
  '#adade1',
  '#7c7dcf',
  '#5557BC', // primario medio
  '#3D3EA8', // primario (marca)
  '#2C2D88', // primario oscuro (hover/estados)
  '#21215a',
  '#131334',
]

// Acento (CTA, badges, botones destacados): #F4545A, con su version clara
// #FEF0F0 dada explicitamente. OJO: este coral y el rojo "critical" quedan
// visualmente parecidos entre si (confirmado con el validador de
// accesibilidad, ΔE 9.2 en vision normal, bajo el piso de 15) -- son los
// hex exactos que se pidieron, no se ajustaron. Mitigado porque en esta app
// el color nunca va solo: siempre acompañado de texto/etiqueta (botones y
// badges con palabra visible, nunca un punto de color aislado). Si en algun
// momento aparecen uno junto al otro en la misma vista y se ve confuso,
// vale la pena revisar.
const accent: MantineColorsTuple = [
  '#fef5f6',
  '#FEF0F0', // acento claro
  '#fbc5c8',
  '#f99fa3',
  '#f6797e',
  '#f5666b',
  '#F4545A', // acento (CTA/badges/botones destacados)
  '#f00f18',
  '#ad0b11',
  '#73070b',
]

// Estados secundarios: solo se dio el tono principal de cada uno: se
// generaron los 9 tonos restantes de cada rampa (incluida la version
// "light" de fondo que se pidio para cada uno) interpolando en el mismo
// matiz/saturacion -- no son hex dictados, a diferencia de brand/accent.
const info: MantineColorsTuple = [
  '#ebfbfe',
  '#cef4fd',
  '#9de9fb',
  '#6dddf8',
  '#0ab9e3',
  '#09a5ca',
  '#0891B2', // teal
  '#06748e',
  '#05576b',
  '#033a47',
]
const good: MantineColorsTuple = [
  '#ebfef8',
  '#cefdef',
  '#9cfcde',
  '#6bface',
  '#07c78c',
  '#06af7a',
  '#059669', // verde
  '#047854',
  '#035a3f',
  '#023c2a',
]
const warning: MantineColorsTuple = [
  '#fef5eb',
  '#fee7cd',
  '#fccf9c',
  '#fbb86a',
  '#f99119',
  '#f28507',
  '#D97706', // ambar
  '#ae5f05',
  '#824704',
  '#573002',
]
const critical: MantineColorsTuple = [
  '#fceded',
  '#f8d3d3',
  '#f1a7a7',
  '#ea7b7b',
  '#e35252',
  '#e03c3c',
  '#DC2626', // rojo
  '#b21d1d',
  '#851515',
  '#590e0e',
]

// Escala de grises: los valores dados (g50 #F9FAFB, g900 #111827) son
// exactamente la escala "gray" de Tailwind CSS -- se completan los pasos
// intermedios con esos mismos valores estandar en vez de inventar otros.
const gray: MantineColorsTuple = [
  '#F9FAFB',
  '#F3F4F6',
  '#E5E7EB',
  '#D1D5DB',
  '#9CA3AF',
  '#6B7280',
  '#4B5563',
  '#374151',
  '#1F2937',
  '#111827',
]

export const theme = createTheme({
  // El coral es el color que realmente domina como estado activo/interactivo
  // en la imagen de referencia (pastilla del nav, linea de encabezado,
  // avatar) -- el indigo aparece ahi solo como UNO de los colores de
  // categoria en las tarjetas del futuro dashboard (Sprint B4), no como el
  // color principal de interaccion. Por eso "accent" (coral) es el
  // primaryColor, no "brand" (indigo).
  primaryColor: 'accent',
  primaryShade: { light: 6, dark: 6 },
  fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", sans-serif',
  headings: { fontFamily: 'Inter, system-ui, -apple-system, "Segoe UI", sans-serif' },
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
    accent,
    info,
    good,
    warning,
    critical,
    gray,
  },
})
