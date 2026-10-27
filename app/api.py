"""API REST de TechStore. El controlador es delgado: busca el pedido,
llama al metodo de Order y traduce excepciones de dominio a codigos HTTP.
Ninguna regla de negocio vive aqui."""
from decimal import Decimal
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from cargar_csv import load_fixture
from app.domain import (
    DomainException, InvalidOrderData, InvalidOrderTransition,
    OrderItem, Money,
)
from app.specifications import discount_rate

app = FastAPI(title="TechStore U4",
              description="Actividad 4 - CLN - nucleo de negocio")
orders = load_fixture()  # repositorio en memoria


# ------------------------------------------------ DomainException -> HTTP
@app.exception_handler(InvalidOrderTransition)
async def _transition(_, exc):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(DomainException)  # InvalidOrderData, limite de 20...
async def _domain(_, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


# -------------------------------------------------------------- DTOs
class ShipRequest(BaseModel):
    tracking_number: str


class CancelRequest(BaseModel):
    reason: str


class ItemRequest(BaseModel):
    sku: str
    quantity: int
    unit_price_mxn: str  # texto para construir Decimal sin pasar por float


def _get(order_id):
    order = orders.get(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="No existe el pedido")
    return order


def _dto(order):
    return {
        "id": order.id,
        "customer_id": order.customer.id,
        "status": order.status.value,
        "units": order.units,
        "total_mxn": str(order.total.amount),
        "events": [e.name for e in order.events],
    }


# --------------------------------------------------------- Endpoints
@app.get("/orders/{order_id}")
def get_order(order_id: str):
    return _dto(_get(order_id))


@app.get("/orders/{order_id}/discount")
def get_discount(order_id: str):
    order = _get(order_id)
    rate = discount_rate(order)
    final = order.total.times(Decimal("1") - rate)
    return {"id": order.id, "discount_rate": str(rate),
            "total_mxn": str(order.total.amount),
            "total_with_discount_mxn": str(final.amount)}


@app.post("/orders/{order_id}/items")
def add_item(order_id: str, body: ItemRequest):
    order = _get(order_id)
    try:
        price = Money(Decimal(body.unit_price_mxn))
    except Exception:
        raise InvalidOrderData("Precio invalido")
    order.add_item(OrderItem(body.sku, body.quantity, price))
    return _dto(order)


@app.post("/orders/{order_id}/confirm")
def confirm_order(order_id: str):
    order = _get(order_id)
    order.confirm()
    return _dto(order)


@app.post("/orders/{order_id}/ship")
def ship_order(order_id: str, body: ShipRequest):
    order = _get(order_id)
    order.ship(body.tracking_number)
    return _dto(order)


@app.post("/orders/{order_id}/cancel")
def cancel_order(order_id: str, body: CancelRequest):
    order = _get(order_id)
    order.cancel(body.reason)
    return _dto(order)


@app.post("/orders/{order_id}/deliver")
def deliver_order(order_id: str):
    order = _get(order_id)
    order.deliver()
    return _dto(order)


@app.post("/orders/{order_id}/return")
def return_order(order_id: str):
    order = _get(order_id)
    order.return_order()
    return _dto(order)
