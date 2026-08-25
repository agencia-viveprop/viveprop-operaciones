import { useState } from 'react'
import { Chip, Group, Paper, Text } from '@mantine/core'
import EvolucionMensual, { type SerieDef } from './EvolucionMensual'
import type { MetricasMes, PromedioMes, Tendencia } from '../api/reportes'
import { clp } from './negociosFormato'

/**
 * Los dos paneles de plata de negocios: el reparto de la comisión y el monto de
 * los negocios. Van juntos en un componente porque los usan el reporte mensual y
 * la vista directorio, y separados se desincronizan.
 *
 * **Por qué son varios paneles y no uno.** Dos razones de escala, las dos
 * medidas sobre los datos y no supuestas:
 *
 * 1. El valor de los negocios va **45 veces** por encima de su comisión --1.556
 *    millones contra 34,8 en toda la historia--. En el mismo eje, las comisiones
 *    quedan aplastadas contra el cero. Y no se arregla con dos ejes: ahí la
 *    relación entre las series la termina decidiendo la escala que uno eligió.
 * 2. La venta y el arriendo tampoco comparten panel. En una venta la base es el
 *    precio de la propiedad; en un arriendo es **un mes de renta**: 1.556
 *    millones contra 2,3. La primera versión de este panel los sumaba y el
 *    resultado fue un gráfico con dos barras dibujadas de seis meses, porque los
 *    arriendos quedaban por debajo de un píxel.
 *
 * **Por qué el reparto va apilado y no como líneas superpuestas.** Estos montos
 * no son medidas paralelas: son las partes de una misma plata. Verificado contra
 * el motor, liquidación por liquidación:
 *
 *     comisión total + rebate = corredores + terceros + equipo + real ViveProp
 *
 * Apiladas, el alto de la barra **es** la plata que se reparte y cada segmento
 * dice quién se quedó con qué. Superpuestas se pisan y, peor, invitan a leerlas
 * como si compitieran entre sí.
 */

/** Los tres segmentos del reparto.
 *
 * **El orden no es negociable por estética.** El validador de color mide pares
 * adyacentes, y en modo oscuro el teal contra `brand.4` cae a ΔE 4.3 en
 * deuteranopía --indistinguibles--. Con marca, acento y teal en este orden los
 * dos que colisionan quedan no adyacentes y los dos modos dan ALL CHECKS PASS.
 * Ver la explicación larga en `PALETA`, dentro de `EvolucionMensual`.
 */
const SEGMENTOS: (SerieDef & { clave: string })[] = [
  { clave: 'real', campo: 'comision_real_vp', nombre: 'Real ViveProp', tono: 'principal' },
  { clave: 'corredores', campo: 'comision_broker', nombre: 'Corredores', tono: 'secundaria' },
  { clave: 'equipo', campo: 'comision_equipo', nombre: 'Equipo ViveProp', tono: 'terciaria' },
]

/** La suma de los tres segmentos del mes, mostrados o no.
 *
 * Es lo que permite apagar un segmento sin mentir: si el total se calculara
 * sumando lo visible, apagar uno bajaría la cifra y eso se leería como que la
 * plata bajó. No bajó, la escondiste. */
function sumaDeLosTres(m: MetricasMes): number {
  return SEGMENTOS.reduce((a, s) => a + Number(m[s.campo]), 0)
}

function sumar(serie: MetricasMes[], campo: keyof MetricasMes): number {
  return serie.reduce((a, m) => a + Number(m[campo]), 0)
}

export default function PlataDeNegocios({
  serie,
  promedio,
  tendencias,
}: {
  serie: MetricasMes[]
  promedio: PromedioMes
  tendencias: Record<string, Tendencia>
}) {
  // Arrancan los tres puestos: el reparto completo es la vista por defecto, y el
  // filtro sirve para aislar uno, no para tener que armarlo cada vez.
  const [vistos, setVistos] = useState<string[]>(SEGMENTOS.map((s) => s.clave))

  const elegidos = SEGMENTOS.filter((s) => vistos.includes(s.clave))
  const rebate = sumar(serie, 'rebate_concentrador')
  const terceros = sumar(serie, 'comision_tercero')
  const arriendos = sumar(serie, 'valor_arriendo')

  /**
   * Cuánto se separan los segmentos de la comisión total registrada, una vez
   * descontados los terceros. Debería ser cero:
   *
   *     comisión total + rebate = corredores + terceros + equipo + real ViveProp
   *
   * **Se mide en vez de suponerse, y se dice cuando no cierra.** En la ventana
   * histórica no cierra: da 903.803, y es el descuadre de origen de una
   * liquidación cuya comisión total se bajó en la planilla sin recalcular el
   * reparto. No es un error del gráfico ni del motor --hay un test del motor que
   * fija la identidad sobre las otras 18-- pero el que mira la barra tiene
   * derecho a saber por qué el alto no coincide con la comisión total.
   *
   * El umbral es de un peso y no de cero porque los siete montos se guardan
   * cuantizados por separado: sobre decenas de filas eso deja centavos de
   * arrastre que no son un descuadre de nada.
   */
  const descuadre =
    sumar(serie, 'comision_broker') +
    sumar(serie, 'comision_equipo') +
    sumar(serie, 'comision_real_vp') +
    terceros -
    (sumar(serie, 'comision_total') + rebate)
  const hayDescuadre = Math.abs(descuadre) > 1

  return (
    <>
      <Paper withBorder radius="md" p="md">
        <Group justify="space-between" align="flex-start" mb="xs">
          <Text size="sm" fw={600}>
            Qué segmentos del reparto se muestran
          </Text>
          <Chip.Group
            multiple
            value={vistos}
            /* Nunca los tres apagados: un gráfico vacío no informa nada, así que
               el último clic que dejaría la pila en cero simplemente no aplica. */
            onChange={(v) => v.length > 0 && setVistos(v)}
          >
            <Group gap="xs">
              {SEGMENTOS.map((s) => (
                <Chip key={s.clave} value={s.clave} size="sm" variant="outline">
                  {s.nombre}
                </Chip>
              ))}
            </Group>
          </Chip.Group>
        </Group>
        <Text size="xs" c="dimmed">
          Apagar un segmento lo saca de la pila, pero la cifra de arriba de cada barra
          sigue siendo la del mes completo: es plata que se esconde, no plata que baja.
        </Text>
      </Paper>

      <EvolucionMensual
        titulo="Cómo se reparte la comisión"
        subtitulo={
          'El alto de la barra es la suma de los tres segmentos: toda la comisión que la operación reparte. ' +
          (hayDescuadre
            ? 'No coincide con la comisión total registrada, y el recuadro de abajo dice por cuánto y por qué.'
            : 'Coincide con la comisión total, salvo las partidas que van en el recuadro de abajo.')
        }
        serie={serie}
        series={elegidos}
        apilado
        etiquetaTotal="Se reparten"
        totalDe={sumaDeLosTres}
        esPlata
      />

      {(rebate > 0 || terceros > 0 || hayDescuadre) && (
        <Paper withBorder radius="md" p="md">
          <Text size="sm">
            En la ventana que estás mirando, además:{' '}
            {rebate > 0 && (
              <>
                los concentradores aportaron{' '}
                <Text span fw={600} ff="monospace">
                  {clp(rebate)}
                </Text>{' '}
                de rebate
              </>
            )}
            {rebate > 0 && terceros > 0 && ', y '}
            {terceros > 0 && (
              <>
                <Text span fw={600} ff="monospace">
                  {clp(terceros)}
                </Text>{' '}
                fueron a terceros
              </>
            )}
            .
          </Text>
          <Text size="xs" c="dimmed" mt={4}>
            {rebate > 0 &&
              'El rebate no es una tajada de la comisión: es plata que entra desde afuera, ' +
                'lo que el concentrador comparte de lo que le cobró al vendedor. Ya está dentro de ' +
                '«Real ViveProp», así que no se suma otra vez. '}
            Van acá y no como un cuarto segmento porque en toda la historia son{' '}
            {terceros > 0 ? 'un puñado de' : 'unas pocas'} liquidaciones: dentro de la barra serían
            un pelo invisible.
          </Text>
          {hayDescuadre && (
            <Text size="xs" c="dimmed" mt="xs">
              Ojo: en esta ventana los segmentos suman{' '}
              <Text span fw={600} ff="monospace">
                {clp(Math.abs(descuadre))}
              </Text>{' '}
              {descuadre > 0 ? 'más' : 'menos'} que la comisión total registrada. Viene de una
              liquidación histórica cuya comisión total se bajó en la planilla de origen sin
              recalcular el reparto, así que sus partes ya no suman su total. Se muestra en vez de
              taparse: el reparto de todas las demás cierra exacto.
            </Text>
          )}
        </Paper>
      )}

      <EvolucionMensual
        titulo="Monto de las ventas"
        subtitulo="El precio de las propiedades vendidas, por mes de cierre. Va en su propio panel porque es unas 45 veces su comisión: en el mismo eje, la aplasta al cero."
        serie={serie}
        series={[{ campo: 'valor_venta', nombre: 'Monto de las ventas', tono: 'principal' }]}
        promedio={Number(promedio.valor_venta)}
        tendencia={tendencias.valor_venta}
        esPlata
      />

      {/* Los arriendos van aparte y no como segunda serie del panel de arriba.
          No son la misma unidad: en una venta la base es el precio de la
          propiedad y en un arriendo es **un mes de renta**. En el historico eso
          es 1.556 millones contra 2,3, o sea que en el mismo grafico el arriendo
          es una linea invisible pegada al cero --se vio asi en la primera version
          de este panel, con dos barras dibujadas de seis meses--. Y sumarlos da
          el mismo numero sin sentido que hizo descartar `valor_prop` en canjes. */}
      {arriendos > 0 && (
        <EvolucionMensual
          titulo="Monto de los arriendos"
          subtitulo="Un mes de renta de cada arriendo cerrado. Va aparte de las ventas a propósito: no son la misma unidad, y en un mismo eje el arriendo desaparece contra el precio de una propiedad."
          serie={serie}
          series={[{ campo: 'valor_arriendo', nombre: 'Monto de los arriendos', tono: 'principal' }]}
          promedio={Number(promedio.valor_arriendo)}
          tendencia={tendencias.valor_arriendo}
          esPlata
        />
      )}
    </>
  )
}
