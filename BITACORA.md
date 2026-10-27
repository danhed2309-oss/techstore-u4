# Bitácora de los 15 escenarios (E01-E15)

Resultado de ejecutar `python ejecutar_escenarios.py`. Cada escenario usa un pedido recién cargado.
Los mensajes de error aparecen sin acentos porque así están escritos en el código.

| Caso | Pedido | Estado inicial | Operación -> resultado real | Estado final | Eventos emitidos | Explicación |
|---|---|---|---|---|---|---|
| E01 | O001 | DRAFT | evaluar descuento -> 10% | DRAFT | ninguno | VIP, total 2100 > 500, 4 unidades y sin promoción: cumple la regla del 10 %. |
| E02 | O002 | DRAFT | evaluar descuento -> 0% | DRAFT | ninguno | No es VIP y 1050 < 5000: no cumple ninguna regla. |
| E03 | O003 | DRAFT | confirm() -> InvalidOrderData: Requiere articulos y cliente activo | DRAFT | ninguno | Cliente inactivo: confirm() lanza InvalidOrderData (API: 422). Sigue en DRAFT, sin eventos. |
| E04 | O005 | DRAFT | evaluar descuento -> 0% | DRAFT | ninguno | Promoción activa: ~ActivePromotionSpec bloquea ambas reglas. |
| E05 | O006 | DRAFT | evaluar descuento -> 5% | DRAFT | ninguno | No es VIP, pero el total 18000 > 5000 y no hay promoción: regla del 5 %. |
| E06 | O007 | DRAFT | confirm() -> InvalidOrderData: Requiere articulos y cliente activo | DRAFT | ninguno | Pedido sin artículos: confirm() lanza InvalidOrderData (API: 422). |
| E07 | O008 | DRAFT | confirm() -> OK | CONFIRMED | OrderConfirmed | Exactamente 20 unidades es válido (el límite es más de 20). |
| E08 | O009 | DRAFT | add_item(SKU003 x2) -> OrderItemLimitExceeded: Maximo 20 unidades | DRAFT | ninguno | 19 + 2 = 21 unidades: OrderItemLimitExceeded; items no cambia (quedan 19 unidades). |
| E09 | O010 | DRAFT | evaluar descuento -> 0% | DRAFT | ninguno | Total exactamente 500: MinimumAmountSpec usa > (estricto). Además no es VIP. |
| E10 | O011 | DRAFT | evaluar descuento -> 0% | DRAFT | ninguno | VIP y 1500 MXN, pero solo 3 unidades: MinimumUnitsSpec(4) falla. |
| E11 | O012 | DRAFT | confirm() -> OK; ship('') -> InvalidOrderData: Se requiere numero de guia | CONFIRMED | OrderConfirmed | confirm() sí es válido (OrderConfirmed); ship('') lanza InvalidOrderData. Queda en CONFIRMED. |
| E12 | O013 | DRAFT | confirm() #1 -> OK; confirm() #2 -> InvalidOrderTransition: No se puede confirmar un pedido en estado CONFIRMED | CONFIRMED | OrderConfirmed | La segunda confirmación lanza InvalidOrderTransition (API: 409) y NO agrega evento. |
| E13 | O014 | DRAFT | confirm() -> OK; ship('GUIA-014') -> OK; cancel('arrepentimiento') -> InvalidOrderTransition: No se puede cancelar un pedido en estado SHIPPED | SHIPPED | OrderConfirmed, OrderShipped | cancel() solo se permite desde CONFIRMED; en SHIPPED lanza InvalidOrderTransition. |
| E14 | O015 | DRAFT | confirm() -> OK; ship('GUIA-015') -> OK; return_order() -> OK | RETURNED | OrderConfirmed, OrderShipped, OrderReturned | SHIPPED -> RETURNED es una transición válida; termina en RETURNED. |
| E15 | O016 | DRAFT | confirm() -> OK; ship('GUIA-016') -> OK; deliver() -> OK | DELIVERED | OrderConfirmed, OrderShipped, OrderDelivered | SHIPPED -> DELIVERED es una transición válida; termina en DELIVERED. |
