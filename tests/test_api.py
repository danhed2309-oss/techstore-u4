import pytest
from fastapi.testclient import TestClient
from app import api
from cargar_csv import load_fixture


@pytest.fixture(autouse=True)
def datos_limpios():
    """Cada prueba arranca con los 16 pedidos en DRAFT."""
    api.orders.clear()
    api.orders.update(load_fixture())


client = TestClient(api.app)


def test_404_pedido_inexistente():
    assert client.post("/orders/NOEXISTE/confirm").status_code == 404
    assert client.get("/orders/NOEXISTE").status_code == 404

def test_get_pedido():
    r = client.get("/orders/O001")
    assert r.status_code == 200
    assert r.json()["units"] == 4 and r.json()["total_mxn"] == "2100.00"

def test_confirmar_ok_200():
    r = client.post("/orders/O013/confirm")
    assert r.status_code == 200
    assert r.json()["status"] == "CONFIRMED"
    assert r.json()["events"] == ["OrderConfirmed"]

def test_confirmar_dos_veces_409():
    client.post("/orders/O013/confirm")
    r = client.post("/orders/O013/confirm")
    assert r.status_code == 409

def test_confirmar_pedido_vacio_422():
    assert client.post("/orders/O007/confirm").status_code == 422

def test_confirmar_cliente_inactivo_422():
    assert client.post("/orders/O003/confirm").status_code == 422

def test_enviar_sin_guia_422():
    client.post("/orders/O012/confirm")
    r = client.post("/orders/O012/ship", json={"tracking_number": ""})
    assert r.status_code == 422
    assert client.get("/orders/O012").json()["status"] == "CONFIRMED"

def test_enviar_ok_y_cancelar_desde_shipped_409():
    client.post("/orders/O014/confirm")
    assert client.post("/orders/O014/ship", json={"tracking_number": "G1"}).status_code == 200
    r = client.post("/orders/O014/cancel", json={"reason": "tarde"})
    assert r.status_code == 409
    assert client.get("/orders/O014").json()["status"] == "SHIPPED"

def test_cancelar_desde_confirmed_200():
    client.post("/orders/O014/confirm")
    r = client.post("/orders/O014/cancel", json={"reason": "cliente"})
    assert r.status_code == 200 and r.json()["status"] == "CANCELLED"

def test_agregar_item_excede_20_unidades_422():
    r = client.post("/orders/O009/items",
                    json={"sku": "SKU003", "quantity": 2, "unit_price_mxn": "120.00"})
    assert r.status_code == 422

def test_agregar_item_ok():
    r = client.post("/orders/O009/items",
                    json={"sku": "SKU003", "quantity": 1, "unit_price_mxn": "120.00"})
    assert r.status_code == 200 and r.json()["units"] == 20

def test_entrega_y_devolucion():
    for pid, op, estado in [("O016", "deliver", "DELIVERED"), ("O015", "return", "RETURNED")]:
        client.post(f"/orders/{pid}/confirm")
        client.post(f"/orders/{pid}/ship", json={"tracking_number": "G"})
        r = client.post(f"/orders/{pid}/{op}")
        assert r.status_code == 200 and r.json()["status"] == estado

def test_descuento_endpoint():
    r = client.get("/orders/O001/discount").json()
    assert r["discount_rate"] == "0.10" and r["total_with_discount_mxn"] == "1890.00"
    assert client.get("/orders/O006/discount").json()["discount_rate"] == "0.05"
    assert client.get("/orders/O005/discount").json()["discount_rate"] == "0"

def test_openapi_documenta_endpoints():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/orders/{order_id}/confirm" in paths
