"""Nucleo de dominio de TechStore (Actividad 4 - CLN - Unidad 4).

Contiene: excepciones de dominio, Value Objects (Money, OrderItem),
entidades (Customer, Order como Aggregate Root), maquina de estados y
Domain Events. No depende de FastAPI ni de ningun servidor: se puede
probar en memoria.
"""
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from datetime import datetime, timezone

MAX_UNITS = 20  # limite de UNIDADES (suma de cantidades), no de renglones


# ---------------------------------------------------------------- Excepciones
class DomainException(Exception):
    """Violacion de una regla de negocio (no es un error tecnico)."""


class OrderException(DomainException):
    """Violaciones relacionadas con pedidos."""


class InvalidOrderData(OrderException):
    """Datos invalidos: monto negativo, pedido vacio, cliente inactivo..."""


class InvalidOrderTransition(OrderException):
    """Operacion no permitida desde el estado actual del pedido."""


class OrderItemLimitExceeded(OrderException):
    """El pedido superaria las 20 unidades."""


# ------------------------------------------------------------- Value Objects
@dataclass(frozen=True)
class Money:
    """Importe inmutable. Invariante: nunca negativo ni no-finito."""
    amount: Decimal
    currency: str = "MXN"

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            raise InvalidOrderData("El monto debe ser Decimal, no float/int")
        if not self.amount.is_finite() or self.amount < 0:
            raise InvalidOrderData("Monto invalido")

    def add(self, other):
        if self.currency != other.currency:
            raise InvalidOrderData("Monedas distintas")
        return Money(self.amount + other.amount, self.currency)

    def times(self, factor):
        """Multiplica por un factor Decimal y redondea a centavos."""
        value = (self.amount * factor).quantize(Decimal("0.01"), ROUND_HALF_UP)
        return Money(value, self.currency)


@dataclass(frozen=True)
class OrderItem:
    """Renglon de un pedido: producto + cantidad + precio unitario."""
    sku: str
    quantity: int
    unit_price: Money

    def __post_init__(self):
        if not self.sku.strip() or self.quantity <= 0:
            raise InvalidOrderData("Articulo invalido")

    @property
    def subtotal(self):
        # Se calcula, nunca se captura a mano.
        return Money(self.unit_price.amount * self.quantity,
                     self.unit_price.currency)


# ------------------------------------------------------------------ Entidades
@dataclass(frozen=True)
class Customer:
    id: str
    is_vip: bool = False
    active: bool = True


class OrderStatus(str, Enum):
    DRAFT = "DRAFT"
    CONFIRMED = "CONFIRMED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    RETURNED = "RETURNED"


@dataclass(frozen=True)
class DomainEvent:
    """Hecho ya ocurrido: inmutable y con marca de tiempo."""
    name: str
    order_id: str
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass
class Order:
    """Aggregate Root. Toda regla de pedidos vive aqui."""
    customer: Customer
    id: str
    has_promotion: bool = False
    status: OrderStatus = OrderStatus.DRAFT
    items: list = field(default_factory=list)
    events: list = field(default_factory=list)

    # --- consultas -------------------------------------------------------
    @property
    def units(self):
        return sum(item.quantity for item in self.items)

    @property
    def total(self):
        amount = sum((x.subtotal.amount for x in self.items), Decimal("0"))
        return Money(amount)

    # --- comandos --------------------------------------------------------
    def add_item(self, item):
        if self.status != OrderStatus.DRAFT:
            raise InvalidOrderTransition("Solo DRAFT admite articulos")
        if self.units + item.quantity > MAX_UNITS:
            raise OrderItemLimitExceeded("Maximo 20 unidades")
        if item.unit_price.currency != "MXN":
            raise InvalidOrderData("Solo MXN")
        self.items.append(item)

    def confirm(self):
        self._require(OrderStatus.DRAFT, "confirmar")
        if not self.items or not self.customer.active:
            raise InvalidOrderData("Requiere articulos y cliente activo")
        self._move(OrderStatus.CONFIRMED, "OrderConfirmed")

    def ship(self, tracking_number):
        self._require(OrderStatus.CONFIRMED, "enviar")
        if not tracking_number or not tracking_number.strip():
            raise InvalidOrderData("Se requiere numero de guia")
        self._move(OrderStatus.SHIPPED, "OrderShipped")

    def cancel(self, reason):
        self._require(OrderStatus.CONFIRMED, "cancelar")
        if not reason or not reason.strip():
            raise InvalidOrderData("Se requiere un motivo de cancelacion")
        self._move(OrderStatus.CANCELLED, "OrderCancelled")

    def deliver(self):
        self._require(OrderStatus.SHIPPED, "entregar")
        self._move(OrderStatus.DELIVERED, "OrderDelivered")

    def return_order(self):
        self._require(OrderStatus.SHIPPED, "devolver")
        self._move(OrderStatus.RETURNED, "OrderReturned")

    # --- utilidades internas --------------------------------------------
    def _require(self, expected, action):
        if self.status != expected:
            raise InvalidOrderTransition(
                f"No se puede {action} un pedido en estado {self.status.value}"
            )

    def _move(self, new_status, event_name):
        # Se llama SOLO despues de validar: cambia estado y registra evento.
        self.status = new_status
        self.events.append(DomainEvent(event_name, self.id))
