# TechStore U4 - Núcleo de negocio (Actividad 4 - CLN - FIME UANL)

Dominio de pedidos con entidades y Value Objects, Specification Pattern,
máquina de estados con Domain Events y API REST con FastAPI. Todo funciona en
memoria (sin base de datos): al cerrar el programa se pierden los cambios.

## Instalación
```bash
python --version                  # 3.11 o superior
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Windows CMD:        .venv\Scripts\activate.bat
# macOS / Linux:      source .venv/bin/activate
python -m pip install fastapi uvicorn pytest httpx
```

## Ejecución
```bash
python cargar_csv.py              # carga los 16 pedidos (todos en DRAFT)
python ejecutar_escenarios.py     # corre E01-E15 y muestra la tabla de la bitácora
python -m pytest -q               # pruebas
uvicorn app.api:app --reload      # API -> http://127.0.0.1:8000/docs
```

## Estructura
```
datos/                 5 CSV (clientes, productos, pedidos, detalle, escenarios)
cargar_csv.py          cargador de fixtures (recibido en el paquete)
app/domain.py          Money, OrderItem, Customer, Order, estados, eventos, excepciones
app/specifications.py  Specification + reglas de descuento
app/api.py             API REST (FastAPI)
tests/                 test_domain.py, test_api.py
ejecutar_escenarios.py ejecuta E01-E15
BITACORA.md            resultado de los 15 escenarios
DIAGRAMA_ESTADOS.md    diagrama de estados y Domain Events
openapi.json           contrato OpenAPI exportado
```

## Reglas de negocio
- `Money` es inmutable, usa `Decimal`, rechaza montos negativos y monedas distintas.
- Máximo **20 unidades** por pedido (suma de cantidades, no de renglones). Solo se agregan artículos en DRAFT.
- Confirmar exige: estado DRAFT, al menos un artículo y cliente activo.
- Enviar exige CONFIRMED y número de guía. Cancelar exige CONFIRMED y motivo. Entregar y devolver exigen SHIPPED.
- Descuento del **10 %**: cliente VIP, total > 500, al menos 4 unidades y sin promoción.
- Descuento del **5 %**: total > 5000 y sin promoción. Si se cumplen ambas, gana el 10 %.
- El inventario (`existencia`) es solo información del catálogo; no se descuenta.

## Endpoints
| Método | Ruta | Éxito | Errores |
|---|---|---|---|
| GET | `/orders/{id}` | 200 | 404 |
| GET | `/orders/{id}/discount` | 200 | 404 |
| POST | `/orders/{id}/items` | 200 | 404, 409, 422 |
| POST | `/orders/{id}/confirm` | 200 | 404, 409, 422 |
| POST | `/orders/{id}/ship` (`tracking_number`) | 200 | 404, 409, 422 |
| POST | `/orders/{id}/cancel` (`reason`) | 200 | 404, 409, 422 |
| POST | `/orders/{id}/deliver` | 200 | 404, 409 |
| POST | `/orders/{id}/return` | 200 | 404, 409 |

Traducción de excepciones: `InvalidOrderTransition` -> **409**; `InvalidOrderData` y
`OrderItemLimitExceeded` -> **422**; pedido inexistente -> **404**.
