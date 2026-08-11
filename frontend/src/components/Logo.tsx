export default function Logo({ height = 26 }: { height?: number }) {
  return <img src="/logo.png" alt="Viveprop" height={height} style={{ display: 'block' }} />
}
