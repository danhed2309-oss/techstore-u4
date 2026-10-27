"""Ejecuta los 15 escenarios de datos/escenarios.csv sobre objetos recien
cargados y muestra la tabla de la bitacora en pantalla. Falla si algun resultado no coincide con
el objetivo del CSV (sin editar pedidos para forzar que pasen)."""
import csv
from pathlib import Path
from decimal import Decimal
from cargar_csv import load_fixture
from app.domain import (DomainException, OrderItem, Money)
from app.specifications import discount_rate

BASE = Path(__file__).resolve().parent
rows = list(csv.DictReader((BASE / "datos/escenarios.csv").open(encoding="utf-8-sig")))

# Cada escenario: lista de pasos (nombre, funcion(order)).
PASOS = {
    "E01": [("evaluar descuento", None)],
    "E02": [("evaluar descuento", None)],
    "E03": [("confirm()", lambda o: o.confirm())],
    "E04": [("evaluar descuento", None)],
    "E05": [("evaluar descuento", None)],
    "E06": [("confirm()", lambda o: o.confirm())],
    "E07": [("confirm()", lambda o: o.confirm())],
    "E08": [("add_item(SKU003 x2)", lambda o: o.add_item(OrderItem("SKU003", 2, Money(Decimal("120.00")))))],
    "E09": [("evaluar descuento", None)],
    "E10": [("evaluar descuento", None)],
    "E11": [("confirm()", lambda o: o.confirm()), ("ship('')", lambda o: o.ship(""))],
    "E12": [("confirm() #1", lambda o: o.confirm()), ("confirm() #2", lambda o: o.confirm())],
    "E13": [("confirm()", lambda o: o.confirm()), ("ship('GUIA-014')", lambda o: o.ship("GUIA-014")),
            ("cancel('arrepentimiento')", lambda o: o.cancel("arrepentimiento"))],
    "E14": [("confirm()", lambda o: o.confirm()), ("ship('GUIA-015')", lambda o: o.ship("GUIA-015")),
            ("return_order()", lambda o: o.return_order())],
    "E15": [("confirm()", lambda o: o.confirm()), ("ship('GUIA-016')", lambda o: o.ship("GUIA-016")),
            ("deliver()", lambda o: o.deliver())],
}
# Resultado esperado del ULTIMO paso (segun la columna 'objetivo')
ESPERA = {"10%": ("desc", "0.10"), "0%": ("desc", "0"), "5%": ("desc", "0.05"),
          "rechazo": "err", "rechazo envio": "err_ultimo", "rechazo segunda": "err_ultimo",
          "rechazo cancelacion": "err_ultimo", "exito": "ok"}
EXPLICA = {
    "E01": "VIP, total 2100 > 500, 4 unidades y sin promocion: cumple la regla del 10 %.",
    "E02": "No es VIP y 1050 < 5000: no cumple ninguna regla.",
    "E03": "Cliente inactivo: confirm() lanza InvalidOrderData (API: 422). Sigue DRAFT, sin eventos.",
    "E04": "Promocion activa: ~ActivePromotionSpec bloquea ambas reglas.",
    "E05": "No VIP pero total 18000 > 5000 y sin promocion: regla del 5 %.",
    "E06": "Pedido sin articulos: confirm() lanza InvalidOrderData (API: 422).",
    "E07": "Exactamente 20 unidades es valido (el limite es > 20).",
    "E08": "19 + 2 = 21 unidades: OrderItemLimitExceeded; items no cambia (19 unidades).",
    "E09": "Total exactamente 500: MinimumAmountSpec usa > (estricto). Ademas no es VIP.",
    "E10": "VIP, 1500 MXN, pero solo 3 unidades: MinimumUnitsSpec(4) falla.",
    "E11": "confirm() si es valido (OrderConfirmed); ship('') lanza InvalidOrderData. Queda CONFIRMED.",
    "E12": "La 2.a confirmacion lanza InvalidOrderTransition (API: 409) y NO agrega evento.",
    "E13": "cancel() solo se permite desde CONFIRMED; en SHIPPED lanza InvalidOrderTransition.",
    "E14": "SHIPPED -> RETURNED es transicion valida; termina en RETURNED.",
    "E15": "SHIPPED -> DELIVERED es transicion valida; termina en DELIVERED.",
}

orders_vistos, lineas, fallos = set(), [], []
for r in rows:
    cid, pid = r["caso_id"], r["pedido_id"]
    order = load_fixture()[pid]            # copia fresca por escenario
    inicial = order.status.value
    log, ultimo_error = [], False
    for nombre, fn in PASOS[cid]:
        if fn is None:
            rate = discount_rate(order)
            log.append(f"{nombre} -> {int(rate*100)}%")
            resultado_desc = str(rate)
            continue
        try:
            fn(order)
            log.append(f"{nombre} -> OK")
            ultimo_error = False
        except DomainException as exc:
            log.append(f"{nombre} -> {type(exc).__name__}: {exc}")
            ultimo_error = True
            break
    # verificacion contra 'objetivo'
    esp = ESPERA[r["objetivo"]]
    if isinstance(esp, tuple):
        ok = resultado_desc == esp[1]
    elif esp == "err":
        ok = ultimo_error
    elif esp == "err_ultimo":
        ok = ultimo_error and len(log) == len(PASOS[cid])  # falla justo en el ultimo paso
    else:
        ok = not ultimo_error
    if not ok:
        fallos.append(cid)
    eventos = ", ".join(e.name for e in order.events) or "ninguno"
    lineas.append(
        f"| {cid} | {pid} | {inicial} | {'; '.join(log)} | "
        f"{order.status.value} | {eventos} | {EXPLICA[cid]} |")
    print(("OK  " if ok else "FALLA"), cid, pid, "|", "; ".join(log), "| estado:", order.status.value)

md = ["# Bitacora de los 15 escenarios (E01-E15)\n",
      "Resultado de `python ejecutar_escenarios.py`. Cada escenario usa un pedido recien cargado.\n",
      "| Caso | Pedido | Estado inicial | Operacion -> resultado real | Estado final | Eventos emitidos | Explicacion |",
      "|---|---|---|---|---|---|---|", *lineas, ""]
print("\n" + "\n".join(md))
if fallos:
    raise SystemExit(f"Escenarios con resultado distinto al esperado: {fallos}")
print("\nLos 15 escenarios coinciden con el objetivo del CSV. Tabla de la bitacora impresa arriba.")
