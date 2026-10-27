import pytest
from decimal import Decimal
from app.domain import (
    Money, OrderItem, Order, Customer, OrderStatus,
    InvalidOrderData, InvalidOrderTransition, OrderItemLimitExceeded,
)
from app.specifications import (
    MinimumAmountSpec, VIPCustomerSpec, MinimumUnitsSpec,
    ActivePromotionSpec, ten_percent, five_percent, any_discount,
    discount_rate,
)
from cargar_csv import load_fixture


def mk_order(vip=True, active=True, promo=False, qty=1, price="600.00"):
    order = Order(Customer("CX", vip, active), "OX", promo)
    if qty:
        order.add_item(OrderItem("SKU001", qty, Money(Decimal(price))))
    return order


# ---------------------------------------------------- Value Objects
def test_money_negativo():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("-1"))

def test_money_rechaza_float():
    with pytest.raises(InvalidOrderData):
        Money(600.0)

def test_money_monedas_distintas():
    with pytest.raises(InvalidOrderData):
        Money(Decimal("1")).add(Money(Decimal("1"), "USD"))

def test_money_add_devuelve_nuevo_objeto():
    a, b = Money(Decimal("100")), Money(Decimal("50"))
    assert a.add(b) == Money(Decimal("150"))
    assert a.amount == Decimal("100")  # no se modifico

def test_money_es_inmutable():
    with pytest.raises(Exception):
        Money(Decimal("1")).amount = Decimal("2")

@pytest.mark.parametrize("qty", [0, -1])
def test_item_cantidad_invalida(qty):
    with pytest.raises(InvalidOrderData):
        OrderItem("SKU001", qty, Money(Decimal("1")))

def test_item_subtotal_calculado():
    assert OrderItem("SKU001", 2, Money(Decimal("600.00"))).subtotal.amount == Decimal("1200.00")


# --------------------------------------------------------- Fixtures
def test_pedido_o001_inicia_draft():
    orders = load_fixture()
    assert orders["O001"].status.value == "DRAFT"
    assert orders["O001"].units == 4
    assert orders["O001"].total.amount == Decimal("2100.00")

def test_se_cargan_16_pedidos_todos_draft():
    orders = load_fixture()
    assert len(orders) == 16
    assert all(o.status == OrderStatus.DRAFT for o in orders.values())


# ----------------------------------------------------- Limite 20 unidades
def test_20_unidades_exactas_permitidas():
    assert load_fixture()["O008"].units == 20

def test_21_unidades_rechazadas_sin_modificar_items():
    o = load_fixture()["O009"]
    with pytest.raises(OrderItemLimitExceeded):
        o.add_item(OrderItem("SKU003", 2, Money(Decimal("120.00"))))
    assert o.units == 19 and len(o.items) == 1

def test_limite_cuenta_unidades_no_renglones():
    o = mk_order(qty=0)
    for _ in range(5):  # 5 renglones de 4 = 20 unidades
        o.add_item(OrderItem("SKU001", 4, Money(Decimal("1"))))
    with pytest.raises(OrderItemLimitExceeded):
        o.add_item(OrderItem("SKU002", 1, Money(Decimal("1"))))

def test_no_agrega_items_si_no_es_draft():
    o = mk_order(); o.confirm()
    with pytest.raises(InvalidOrderTransition):
        o.add_item(OrderItem("SKU002", 1, Money(Decimal("1"))))

def test_solo_mxn():
    o = mk_order(qty=0)
    with pytest.raises(InvalidOrderData):
        o.add_item(OrderItem("SKU001", 1, Money(Decimal("1"), "USD")))


# ------------------------------------------------------ Specifications
def test_specs_individuales():
    o = load_fixture()["O001"]
    assert MinimumAmountSpec(500).is_satisfied_by(o)
    assert VIPCustomerSpec().is_satisfied_by(o)
    assert MinimumUnitsSpec(4).is_satisfied_by(o)
    assert not ActivePromotionSpec().is_satisfied_by(o)

def test_composicion_and_or_not():
    o = load_fixture()["O001"]
    assert (VIPCustomerSpec() & MinimumUnitsSpec(4)).is_satisfied_by(o)
    assert (ActivePromotionSpec() | VIPCustomerSpec()).is_satisfied_by(o)
    assert (~ActivePromotionSpec()).is_satisfied_by(o)
    assert not (VIPCustomerSpec() & ActivePromotionSpec()).is_satisfied_by(o)

def test_specification_no_modifica_el_pedido():
    o = load_fixture()["O001"]
    antes = (o.status, o.units, len(o.events))
    ten_percent.is_satisfied_by(o)
    assert (o.status, o.units, len(o.events)) == antes

@pytest.mark.parametrize("pid,esperado", [
    ("O001", "0.10"),  # VIP, 2100, 4 u, sin promo
    ("O002", "0"),     # no VIP, <5000
    ("O005", "0"),     # promocion activa
    ("O006", "0.05"),  # 18000 > 5000
    ("O010", "0"),     # total exactamente 500
    ("O011", "0"),     # VIP pero solo 3 unidades
])
def test_descuento_por_pedido(pid, esperado):
    assert discount_rate(load_fixture()[pid]) == Decimal(esperado)

def test_umbral_500_es_estricto():
    o = mk_order(vip=True, qty=4, price="125.00")  # total = 500 exacto
    assert not MinimumAmountSpec(500).is_satisfied_by(o)
    assert discount_rate(o) == 0

def test_prioridad_10_sobre_5():
    o = mk_order(vip=True, qty=4, price="2000.00")  # 8000: cumple ambas
    assert ten_percent.is_satisfied_by(o) and five_percent.is_satisfied_by(o)
    assert any_discount.is_satisfied_by(o)
    assert discount_rate(o) == Decimal("0.10")

def test_5_por_ciento_bloqueado_por_promocion():
    o = mk_order(vip=False, promo=True, qty=1, price="9000.00")
    assert discount_rate(o) == 0


# ------------------------------------------------- Maquina de estados
def test_confirmar_pedido_vacio_rechazado():
    o = load_fixture()["O007"]
    with pytest.raises(InvalidOrderData):
        o.confirm()
    assert o.status == OrderStatus.DRAFT and o.events == []

def test_confirmar_cliente_inactivo_rechazado():
    o = load_fixture()["O003"]
    with pytest.raises(InvalidOrderData):
        o.confirm()
    assert o.status == OrderStatus.DRAFT and o.events == []

def test_confirmar_20_unidades_exitoso():
    o = load_fixture()["O008"]; o.confirm()
    assert o.status == OrderStatus.CONFIRMED

def test_confirmacion_doble_no_agrega_evento():
    o = load_fixture()["O013"]
    o.confirm()
    assert o.status == OrderStatus.CONFIRMED
    assert [e.name for e in o.events] == ["OrderConfirmed"]
    with pytest.raises(InvalidOrderTransition):
        o.confirm()
    assert len(o.events) == 1

@pytest.mark.parametrize("guia", ["", "   ", None])
def test_enviar_sin_guia_rechazado(guia):
    o = load_fixture()["O012"]; o.confirm()
    with pytest.raises(InvalidOrderData):
        o.ship(guia)
    assert o.status == OrderStatus.CONFIRMED
    assert [e.name for e in o.events] == ["OrderConfirmed"]

def test_cancelar_desde_shipped_rechazado():
    o = load_fixture()["O014"]
    o.confirm(); o.ship("GUIA123")
    with pytest.raises(InvalidOrderTransition):
        o.cancel("ya no lo quiero")
    assert o.status == OrderStatus.SHIPPED
    assert "OrderCancelled" not in [e.name for e in o.events]

def test_cancelar_requiere_motivo():
    o = load_fixture()["O014"]; o.confirm()
    with pytest.raises(InvalidOrderData):
        o.cancel("")
    assert o.status == OrderStatus.CONFIRMED

def test_cancelar_desde_confirmed():
    o = load_fixture()["O014"]; o.confirm(); o.cancel("cliente cambio de opinion")
    assert o.status == OrderStatus.CANCELLED

def test_confirmar_pedido_cancelado_rechazado():
    o = load_fixture()["O014"]; o.confirm(); o.cancel("x")
    with pytest.raises(InvalidOrderTransition):
        o.confirm()

def test_devolucion_desde_shipped():
    o = load_fixture()["O015"]
    o.confirm(); o.ship("G1"); o.return_order()
    assert o.status == OrderStatus.RETURNED
    assert [e.name for e in o.events] == ["OrderConfirmed", "OrderShipped", "OrderReturned"]

def test_entrega_desde_shipped():
    o = load_fixture()["O016"]
    o.confirm(); o.ship("G2"); o.deliver()
    assert o.status == OrderStatus.DELIVERED
    assert [e.name for e in o.events][-1] == "OrderDelivered"

def test_no_se_puede_entregar_ni_devolver_sin_enviar():
    o = load_fixture()["O016"]; o.confirm()
    with pytest.raises(InvalidOrderTransition):
        o.deliver()
    with pytest.raises(InvalidOrderTransition):
        o.return_order()

def test_eventos_inmutables_y_con_timestamp():
    o = load_fixture()["O013"]; o.confirm()
    ev = o.events[0]
    assert ev.order_id == "O013" and ev.occurred_at is not None
    with pytest.raises(Exception):
        ev.name = "otro"
