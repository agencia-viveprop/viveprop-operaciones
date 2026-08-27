"""La logica de la correccion de monedas de canjes.

El script escribe en produccion, asi que lo que decide **que** escribir esta en
una funcion pura y se prueba acá. Lo que se fija:

1. Solo cambia lo que hay que cambiar.
2. **No pisa una edicion mas nueva.** Si el canje cambio en la base despues de que
   se genero el archivo, la revision que trae el archivo esta vieja: se omite y se
   informa, en vez de ganar por ser la ultima en llegar.
3. Una celda vacia es "no revisada", no "borrala".
"""
from app.scripts.aplicar_monedas_canjes import Decision, planificar


def test_cambia_solo_lo_que_corresponde():
    decisiones = [
        Decision(1, "CLP", "UF"),
        Decision(2, "UF", "CLP"),
    ]
    plan = planificar(decisiones, actual={1: "CLP", 2: "UF"})

    assert plan.cambios == [(1, "CLP", "UF"), (2, "UF", "CLP")]
    assert plan.ya_estaban == 0
    assert plan.desactualizadas == []


def test_no_pisa_una_edicion_mas_nueva():
    """El caso que justifica la guarda.

    El archivo se genero cuando el canje 1 tenia CLP. Alguien lo corrigio a mano a
    UF despues. Si la revision se aplicara igual no romperia nada acá --coincide--
    pero el canje 2 muestra el peligro: el archivo propone CLP porque lo vio en UF,
    y ahora esta en OTRA. Aplicarlo pisaria esa edicion sin que nadie se enterara.
    """
    plan = planificar(
        [Decision(2, "UF", "CLP")],
        actual={2: "OTRA"},
    )

    assert plan.cambios == []
    assert len(plan.desactualizadas) == 1
    assert "lo editó después" in plan.desactualizadas[0]
    assert "canje 2" in plan.desactualizadas[0]


def test_lo_que_ya_esta_bien_no_se_cuenta_como_cambio():
    """Recorrer el archivo dos veces no tiene que hacer nada la segunda."""
    plan = planificar([Decision(1, "UF", "UF")], actual={1: "UF"})

    assert plan.cambios == []
    assert plan.ya_estaban == 1


def test_una_celda_vacia_es_no_revisada():
    plan = planificar([Decision(1, "CLP", "")], actual={1: "CLP"})

    assert plan.cambios == []
    assert plan.sin_decision == 1


def test_rechaza_una_moneda_inventada():
    """Si alguien escribe "pesos" en la celda, no se escribe nada."""
    plan = planificar([Decision(1, "CLP", "PESOS")], actual={1: "CLP"})

    assert plan.cambios == []
    assert len(plan.invalidas) == 1
    assert "PESOS" in plan.invalidas[0]


def test_un_canje_que_no_existe_se_informa():
    plan = planificar([Decision(999, "CLP", "UF")], actual={1: "CLP"})

    assert plan.cambios == []
    assert plan.inexistentes == ["canje 999: no existe"]


def test_un_canje_sin_moneda_puede_recibir_una():
    """Nulo es un estado valido de partida: el archivo lo trae como vacio."""
    plan = planificar([Decision(1, None, "UF")], actual={1: None})

    assert plan.cambios == [(1, "nada", "UF")]
